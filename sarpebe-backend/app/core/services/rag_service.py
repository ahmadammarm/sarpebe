from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.services.embedding_service import embedding_service
from app.db.repositories.document_chunk_repository import document_chunk_repo
from app.db.models.document_chunk import DocumentChunk

class RAGService:
    @staticmethod
    async def retrieve_context(
        db: AsyncSession, 
        topic: str, 
        grade_level: str, 
        subject: str, 
        user_id: UUID,
        top_k: int = 5
    ) -> list[DocumentChunk]:
        """
        1. Embeds the topic query.
        2. Retrieves the most relevant chunks, strictly pre-filtered by grade and subject.
        """
        embedding = await embedding_service.embed_text(db, topic, user_id)
        
        chunks = await document_chunk_repo.search_similar(
            db=db,
            embedding=embedding,
            grade_level=grade_level,
            subject=subject,
            top_k=top_k
        )
        
        return list(chunks)

rag_service = RAGService()
