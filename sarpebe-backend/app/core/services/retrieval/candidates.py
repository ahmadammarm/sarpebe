from dataclasses import dataclass
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.retrieval.fusion import reciprocal_rank_fusion
from app.db.repositories.document_chunk_repository import ScoredChunk, document_chunk_repo


@dataclass(frozen=True)
class CandidateSet:
    vector_hits: Sequence[ScoredChunk]  # nearest by embedding, best first
    keyword_hits: Sequence[ScoredChunk]  # sharing words with the topic, best first
    fused: Sequence[ScoredChunk]  # both lists merged and deduplicated, best first


async def gather_candidates(
    db: AsyncSession,
    *,
    embedding: list[float],
    topic: str,
    grade_level: str,
    subject: str,
    limit: int,
) -> CandidateSet:
    """
    The retrieval stage before any filtering or reranking: vector search and full-text search over
    the chunks with this grade and subject, merged with reciprocal rank fusion. Shared by the
    production pipeline and the evaluation harness so they can never disagree about what a
    "candidate" is.
    """
    vector_hits = list(await document_chunk_repo.search_vector(db, embedding, grade_level, subject, limit))
    keyword_hits = list(await document_chunk_repo.search_keyword(db, topic, embedding, grade_level, subject, limit))

    by_id = {hit.chunk.id: hit for hit in [*keyword_hits, *vector_hits]}
    fused = reciprocal_rank_fusion([
        [hit.chunk.id for hit in vector_hits],
        [hit.chunk.id for hit in keyword_hits],
    ])
    return CandidateSet(
        vector_hits=vector_hits,
        keyword_hits=keyword_hits,
        fused=[by_id[chunk_id] for chunk_id, _ in fused],
    )
