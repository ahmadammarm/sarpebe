import uuid
import tempfile
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pypdf import PdfReader
from app.api.deps import get_db, get_current_user
from app.schemas.curriculum import CurriculumDocumentResponse
from app.db.models.profile import Profile
from app.db.models.curriculum_document import CurriculumDocument
from app.db.models.document_chunk import DocumentChunk
from app.utils.chunking import semantic_chunk_text
from app.core.services.embedding_service import embedding_service

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

@router.post("/upload", response_model=CurriculumDocumentResponse)
async def upload_document(
    grade_level: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
        
    text = ""
    try:
        reader = PdfReader(tmp_path)
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")
    finally:
        os.remove(tmp_path)
        
    chunks = semantic_chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Could not extract any text from the PDF.")
        
    doc_id = uuid.uuid4()
    doc = CurriculumDocument(
        id=doc_id,
        title=file.filename,
        document_type="pdf",
        url_path=f"curriculum/{doc_id}.pdf",
    )
    db.add(doc)
    await db.flush()
    
    # Process embeddings inside a transaction block
    async with db.begin_nested():
        for i, chunk_text in enumerate(chunks):
            embedding = await embedding_service.embed_text(db, chunk_text, current_user.id)
            chunk_obj = DocumentChunk(
                document_id=doc.id,
                chunk_content=chunk_text,
                embedding=embedding,
                page_number=1, # Assuming page 1 for simplicity in this implementation
                grade_level=grade_level,
                subject=subject
            )
            db.add(chunk_obj)
            
    await db.commit()
    await db.refresh(doc)
    
    return doc

@router.get("", response_model=list[CurriculumDocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    from sqlalchemy import select
    result = await db.execute(select(CurriculumDocument))
    return list(result.scalars().all())
