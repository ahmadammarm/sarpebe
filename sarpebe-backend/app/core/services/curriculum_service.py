import logging
import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import storage
from app.core.exceptions import DocumentNotFoundError, InvalidStateError, InvalidUploadError
from app.db.models.curriculum_document import CurriculumDocument
from app.db.repositories.curriculum_document_repository import curriculum_document_repo
from app.schemas.curriculum import CurriculumDocumentUpdate, DocumentType
from app.utils.labels import normalize_label

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"

class CurriculumService:
    @staticmethod
    def _validate_pdf(filename: str | None, content: bytes) -> None:
        if not filename or not filename.lower().endswith(".pdf"):
            raise InvalidUploadError("Only PDF files are supported.")
        if not content.startswith(PDF_MAGIC):
            raise InvalidUploadError("The uploaded file is not a valid PDF.")
        if len(content) > settings.max_upload_mb * 1024 * 1024:
            raise InvalidUploadError(f"File exceeds the {settings.max_upload_mb} MB upload limit.")

    @staticmethod
    async def upload(
        db: AsyncSession,
        *,
        filename: str | None,
        content: bytes,
        grade_level: str,
        subject: str,
        document_type: DocumentType,
        admin_id: uuid.UUID,
    ) -> CurriculumDocument:
        CurriculumService._validate_pdf(filename, content)

        grade = normalize_label(grade_level)
        subj = normalize_label(subject)
        if not grade or not subj:
            raise InvalidUploadError("Grade level and subject are required.")

        doc_id = uuid.uuid4()
        storage_path = storage.curriculum_storage_path(doc_id)
        try:
            storage.upload_pdf(storage_path, content)
        except Exception as e:
            logger.exception("Storage upload failed for %s", doc_id)
            raise InvalidUploadError(f"Failed to upload to storage: {e}")

        doc = await curriculum_document_repo.create(db, {
            "id": doc_id,
            "title": filename,
            "document_type": document_type.value,
            "url_path": storage.public_url(storage_path),
            "grade_level": grade,
            "subject": subj,
            "status": "processing",
        })
        # The worker must see the row, so commit before dispatching.
        await db.commit()

        from app.tasks.curriculum_tasks import process_curriculum_document_task
        process_curriculum_document_task.delay(str(doc.id), str(admin_id))
        return doc

    @staticmethod
    async def list_documents(db: AsyncSession, skip: int, limit: int) -> tuple[Sequence[CurriculumDocument], int]:
        return await curriculum_document_repo.list_paginated(db, skip, limit)

    @staticmethod
    async def _get_idle(db: AsyncSession, document_id: uuid.UUID) -> CurriculumDocument:
        """A document that exists and is not being processed right now."""
        doc = await curriculum_document_repo.get(db, document_id)
        if not doc:
            raise DocumentNotFoundError("Curriculum document not found")
        if doc.status == "processing":
            raise InvalidStateError("The document is still being processed.")
        return doc

    @staticmethod
    async def _start_processing(db: AsyncSession, doc: CurriculumDocument, admin_id: uuid.UUID) -> None:
        """Marks the document as processing and hands it to the worker (commit first, so it sees the row)."""
        doc.status = "processing"
        await db.commit()

        from app.tasks.curriculum_tasks import process_curriculum_document_task
        process_curriculum_document_task.delay(str(doc.id), str(admin_id))

    @staticmethod
    async def reindex(db: AsyncSession, document_id: uuid.UUID, admin_id: uuid.UUID) -> CurriculumDocument:
        """Reads the stored PDF again and replaces the document's chunks."""
        doc = await CurriculumService._get_idle(db, document_id)
        await CurriculumService._start_processing(db, doc, admin_id)
        return doc

    @staticmethod
    async def update(
        db: AsyncSession, document_id: uuid.UUID, payload: CurriculumDocumentUpdate, admin_id: uuid.UUID
    ) -> CurriculumDocument:
        """
        Edits a document's details. Grade and subject are part of every chunk's embedded text and
        of the retrieval filter, so changing either processes the document again; a new title or
        type is a plain update.
        """
        doc = await CurriculumService._get_idle(db, document_id)
        changes = payload.model_dump(exclude_unset=True, exclude_none=True)

        for label in ("grade_level", "subject"):
            if label in changes:
                changes[label] = normalize_label(changes[label])
        if isinstance(changes.get("document_type"), DocumentType):
            changes["document_type"] = changes["document_type"].value

        reprocess = any(getattr(doc, label) != changes[label] for label in ("grade_level", "subject") if label in changes)
        doc = await curriculum_document_repo.update(db, doc, changes)

        if reprocess:
            await CurriculumService._start_processing(db, doc, admin_id)
        else:
            await db.commit()
        return doc

    @staticmethod
    async def delete(db: AsyncSession, document_id: uuid.UUID) -> None:
        doc = await curriculum_document_repo.get(db, document_id)
        if not doc:
            raise DocumentNotFoundError("Curriculum document not found")

        try:
            storage.remove(storage.curriculum_storage_path(doc.id))
        except Exception:
            # Proceed with DB deletion even if the file is already gone.
            logger.warning("Could not remove storage object for %s", doc.id)

        await curriculum_document_repo.delete(db, doc.id)
        await db.commit()

curriculum_service = CurriculumService()
