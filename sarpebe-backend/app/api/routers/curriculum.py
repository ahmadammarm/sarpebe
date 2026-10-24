import uuid
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_admin
from app.schemas.common import PaginatedResponse
from app.schemas.curriculum import CurriculumDocumentResponse, CurriculumDocumentUpdate, DocumentType
from app.db.models.profile import Profile
from app.core.services.curriculum_service import curriculum_service

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

@router.post("/upload", response_model=CurriculumDocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    grade_level: str = Form(...),
    subject: str = Form(...),
    document_type: DocumentType = Form(DocumentType.CP),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_admin: Profile = Depends(require_admin)
):
    content = await file.read()
    return await curriculum_service.upload(
        db,
        filename=file.filename,
        content=content,
        grade_level=grade_level,
        subject=subject,
        document_type=document_type,
        admin_id=current_admin.id,
    )

@router.get("", response_model=PaginatedResponse[CurriculumDocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: Profile = Depends(require_admin)
):
    items, total = await curriculum_service.list_documents(db, skip, limit)
    return PaginatedResponse(items=list(items), total=total, skip=skip, limit=limit)

@router.patch("/{id}", response_model=CurriculumDocumentResponse)
async def update_document(
    id: uuid.UUID,
    payload: CurriculumDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Profile = Depends(require_admin)
):
    """Edits title, type, grade or subject. A new grade or subject processes the document again."""
    return await curriculum_service.update(db, id, payload, current_admin.id)

@router.post("/{id}/reindex", response_model=CurriculumDocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def reindex_document(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Profile = Depends(require_admin)
):
    return await curriculum_service.reindex(db, id, current_admin.id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Profile = Depends(require_admin)
):
    await curriculum_service.delete(db, id)
    return None
