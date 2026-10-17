from typing import Sequence
from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.curriculum_document import CurriculumDocument
from app.db.models.document_chunk import DocumentChunk
from app.db.repositories.base_repository import BaseRepository

class CurriculumDocumentRepository(BaseRepository[CurriculumDocument, dict, dict]):
    def __init__(self):
        super().__init__(CurriculumDocument)

    async def list_all(self, db: AsyncSession) -> Sequence[CurriculumDocument]:
        result = await db.execute(
            select(self.model).order_by(self.model.uploaded_at.desc())
        )
        return result.scalars().all()

    async def delete_chunks(self, db: AsyncSession, document_id: UUID) -> None:
        """Removes every chunk of a document (used to make re-ingestion idempotent)."""
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

curriculum_document_repo = CurriculumDocumentRepository()
