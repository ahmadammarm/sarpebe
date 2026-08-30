from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.db.models.document_chunk import DocumentChunk
from app.db.repositories.base_repository import BaseRepository

class DocumentChunkRepository(BaseRepository[DocumentChunk, dict, dict]):
    def __init__(self):
        super().__init__(DocumentChunk)
        
    async def search_similar(
        self, 
        db: AsyncSession, 
        embedding: list[float], 
        grade_level: str, 
        subject: str, 
        top_k: int = 5
    ) -> Sequence[DocumentChunk]:
        """
        Executes a vector similarity search using pgvector's cosine distance (<=>).
        Crucially, it PRE-FILTERS by grade_level and subject using standard B-Tree
        indexes before computing the math-heavy vector distances.
        
        Uses joinedload() to eagerly load the parent CurriculumDocument metadata,
        preventing N+1 query issues.
        """
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.document))
            .filter(
                self.model.grade_level == grade_level,
                self.model.subject == subject
            )
            .order_by(self.model.embedding.cosine_distance(embedding))
            .limit(top_k)
        )
        return result.scalars().all()

document_chunk_repo = DocumentChunkRepository()
