from typing import Sequence
from uuid import UUID
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.curriculum_document import CurriculumDocument
from app.db.models.document_chunk import DocumentChunk
from app.db.repositories.base_repository import BaseRepository

class CurriculumDocumentRepository(BaseRepository[CurriculumDocument, dict, dict]):
    def __init__(self):
        super().__init__(CurriculumDocument)

    async def list_paginated(
        self, db: AsyncSession, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[CurriculumDocument], int]:
        """One page of documents, newest first, with the total number of documents."""
        total = (await db.execute(select(func.count()).select_from(self.model))).scalar_one()
        result = await db.execute(
            select(self.model).order_by(self.model.uploaded_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    async def delete_chunks(self, db: AsyncSession, document_id: UUID) -> None:
        """Removes every chunk of a document (used to make re-ingestion idempotent)."""
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

curriculum_document_repo = CurriculumDocumentRepository()
