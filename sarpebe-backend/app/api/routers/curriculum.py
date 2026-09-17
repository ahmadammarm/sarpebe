import uuid
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_admin
from app.schemas.curriculum import CurriculumDocumentResponse
from app.db.models.profile import Profile
from app.db.models.curriculum_document import CurriculumDocument
from app.core.storage import supabase_client
from app.tasks.curriculum_tasks import process_curriculum_document_task

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

@router.post("/upload", response_model=CurriculumDocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    grade_level: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_admin: Profile = Depends(require_admin)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    doc_id = uuid.uuid4()
    storage_path = f"curriculum/{doc_id}.pdf"

    # Upload to Supabase Storage
    try:
        supabase_client.storage.from_("sarpebe-storage").upload(
            path=storage_path,
            file=content,
            file_options={"content-type": "application/pdf"}
        )

        # Construct public URL manually to ensure it's never empty
        from app.config import settings
        url_path = f"{settings.supabase_url}/storage/v1/object/public/sarpebe-storage/{storage_path}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(e)}")

    doc = CurriculumDocument(
        id=doc_id,
        title=file.filename,
        document_type="pdf",
        url_path=url_path,
        status="processing"
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Dispatch background task
    process_curriculum_document_task.delay(str(doc.id), str(current_admin.id), grade_level, subject)

    return doc

@router.get("", response_model=list[CurriculumDocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_admin: Profile = Depends(require_admin)
):
    result = await db.execute(select(CurriculumDocument))
    return list(result.scalars().all())

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Profile = Depends(require_admin)
):
    doc = await db.get(CurriculumDocument, id)
    if not doc:
        raise HTTPException(status_code=404, detail="Curriculum document not found")

    # Try removing the file from Supabase storage
    try:
        storage_path = f"curriculum/{doc.id}.pdf"
        supabase_client.storage.from_("sarpebe-storage").remove([storage_path])
    except Exception:
        pass  # Proceed with DB deletion even if storage remove fails or file is missing

    await db.delete(doc)
    await db.commit()
    return None
