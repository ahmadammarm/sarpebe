from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.db.models.document_chunk import DocumentChunk
from app.db.repositories.base_repository import BaseRepository
from app.utils.labels import normalize_label
from app.utils.text import keyword_terms


@dataclass(frozen=True)
class ScoredChunk:
    chunk: DocumentChunk
    # Cosine similarity to the query embedding (1.0 = same direction), for every kind of hit.
    similarity: float


class DocumentChunkRepository(BaseRepository[DocumentChunk, dict, dict]):
    def __init__(self):
        super().__init__(DocumentChunk)

    def _label_filters(self, grade_level: str, subject: str):
        # Labels are compared in their normalized form (see app.utils.labels), which is also how
        # chunks are stored at ingestion time. Always applied before any ranking.
        return (
            self.model.grade_level == normalize_label(grade_level),
            self.model.subject == normalize_label(subject),
        )

    async def search_vector(
        self,
        db: AsyncSession,
        embedding: list[float],
        grade_level: str,
        subject: str,
        limit: int,
    ) -> Sequence[ScoredChunk]:
        """
        Nearest chunks by cosine distance (pgvector `<=>`), pre-filtered by grade and subject.
        With the HNSW index, iterative scan keeps scanning until `limit` rows pass the label
        filter; without it a filtered ANN query can return fewer rows than exist.
        """
        if settings.rag_hnsw_iterative_scan:
            await db.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))

        distance = self.model.embedding.cosine_distance(embedding)
        result = await db.execute(
            select(self.model, (1 - distance).label("similarity"))
            .options(joinedload(self.model.document))
            .filter(*self._label_filters(grade_level, subject))
            .order_by(distance)
            .limit(limit)
        )
        return [ScoredChunk(chunk, float(similarity)) for chunk, similarity in result.all()]

    async def search_keyword(
        self,
        db: AsyncSession,
        query_text: str,
        embedding: list[float],
        grade_level: str,
        subject: str,
        limit: int,
    ) -> Sequence[ScoredChunk]:
        """
        Chunks that share words with the query (Indonesian full-text search, any-word match),
        best-ranked first, pre-filtered by grade and subject. Catches exact terms such as
        "inflasi" or "Profil Pelajar Pancasila" that an embedding can blur. The cosine
        similarity of each hit is returned too, so one similarity floor applies to all hits.
        """
        terms = keyword_terms(query_text)
        if not terms:
            return []

        tsquery = func.to_tsquery("indonesian", " | ".join(terms))
        distance = self.model.embedding.cosine_distance(embedding)
        result = await db.execute(
            select(self.model, (1 - distance).label("similarity"))
            .options(joinedload(self.model.document))
            .filter(*self._label_filters(grade_level, subject), self.model.search_vector.op("@@")(tsquery))
            .order_by(func.ts_rank_cd(self.model.search_vector, tsquery).desc())
            .limit(limit)
        )
        return [ScoredChunk(chunk, float(similarity)) for chunk, similarity in result.all()]

document_chunk_repo = DocumentChunkRepository()
