import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import InsufficientContextError
from app.core.services.embedding_service import embedding_service
from app.core.services.retrieval.candidates import gather_candidates
from app.core.services.retrieval.query import build_query
from app.core.services.retrieval.rerank import rerank_candidates
from app.core.services.retrieval.passages import choose_passages
from app.core.services.retrieval.types import RetrievalResult

logger = logging.getLogger(__name__)

NO_DOCUMENTS_MESSAGE = "Belum ada dokumen kurikulum untuk kelas dan mata pelajaran ini."
NOT_COVERED_MESSAGE = "Dokumen kurikulum yang tersedia belum membahas topik ini."


class RAGService:
    @staticmethod
    async def retrieve_context(
        db: AsyncSession,
        *,
        topic: str,
        grade_level: str,
        subject: str,
        user_id: UUID,
        lesson_plan_id: UUID | None = None,
    ) -> RetrievalResult:
        """
        Finds the curriculum passages a lesson plan may be written from.

        1. Embed "mapel kelas N (Fase X): topik".
        2. Pre-filter by grade and subject, then take the nearest chunks by vector AND the chunks
           sharing words with the topic (full-text); merge both lists with reciprocal rank fusion.
        3. Drop anything below the similarity floor.
        4. Rerank the shortlist with a small model and keep what is at least partly relevant.
        5. Nothing left means the documents do not cover the topic: raise InsufficientContextError so
           the caller does not ask the model to write from nothing.
        """
        query = build_query(topic, grade_level, subject)
        embedding = await embedding_service.embed_text(
            query, user_id, purpose="query", lesson_plan_id=lesson_plan_id
        )

        candidates = await gather_candidates(
            db,
            embedding=embedding,
            topic=topic,
            grade_level=grade_level,
            subject=subject,
            limit=settings.rag_candidate_k,
        )
        ordered = list(candidates.fused)

        stats: dict = {
            "query": query,
            "vector_hits": len(candidates.vector_hits),
            "keyword_hits": len(candidates.keyword_hits),
            "fused": len(ordered),
            "similarity_floor": settings.rag_min_similarity,
        }
        if not ordered:
            raise InsufficientContextError(NO_DOCUMENTS_MESSAGE)

        stats["top_similarity"] = round(max(hit.similarity for hit in ordered), 4)
        above_floor = [hit for hit in ordered if hit.similarity >= settings.rag_min_similarity]
        stats["above_floor"] = len(above_floor)
        if not above_floor:
            logger.info("Nothing above the similarity floor for %r (best %.3f)", query, stats["top_similarity"])
            raise InsufficientContextError(NOT_COVERED_MESSAGE)

        shortlist = above_floor
        scores = None
        if settings.rag_use_rerank:
            shortlist = above_floor[: settings.rag_rerank_shortlist]
            scores = await rerank_candidates(query, shortlist, user_id=user_id, lesson_plan_id=lesson_plan_id)
        stats["reranked"] = scores is not None

        passages = choose_passages(
            shortlist,
            scores,
            top_k=settings.rag_top_k,
            max_chars=settings.rag_context_max_chars,
        )
        if not passages:
            raise InsufficientContextError(NOT_COVERED_MESSAGE)

        stats["kept"] = len(passages)
        stats["passages"] = [
            {
                "id": p.id,
                "chunk_id": str(p.chunk_id),
                "document_id": str(p.document_id),
                "page": p.page,
                "similarity": round(p.similarity, 4),
                "rerank_score": p.rerank_score,
            }
            for p in passages
        ]
        return RetrievalResult(passages=passages, stats=stats)

rag_service = RAGService()
