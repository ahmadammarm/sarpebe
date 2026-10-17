import logging
from typing import Sequence
from uuid import UUID

from pydantic import BaseModel, Field

from app.config import settings
from app.core.llm_client import ensure_usable, generate_structured
from app.core.prompts.rerank import RERANK_INSTRUCTION, RerankCandidate, build_rerank_content
from app.db.repositories.document_chunk_repository import ScoredChunk
from app.schemas.json_schema import to_gemini_schema

logger = logging.getLogger(__name__)


class RerankItem(BaseModel):
    index: int = Field(ge=0, description="The index of the passage, exactly as given.")
    score: int = Field(ge=0, le=3, description="Relevance: 3 direct, 2 partial, 1 weak, 0 irrelevant.")


class RerankResponse(BaseModel):
    ranked: list[RerankItem]


RERANK_SCHEMA = to_gemini_schema(RerankResponse)


async def rerank_candidates(
    query: str,
    candidates: Sequence[ScoredChunk],
    *,
    user_id: UUID,
    lesson_plan_id: UUID | None = None,
) -> dict[int, int] | None:
    """
    Asks a small model to score each candidate 0-3 for the teacher's need.
    Returns {candidate position: score}, or None if the call could not be completed: reranking
    only improves precision, so the caller falls back to the fused order instead of failing.
    A candidate the model skipped scores 0.
    """
    content = build_rerank_content(
        query,
        [
            RerankCandidate(
                index=position,
                text=candidate.chunk.chunk_content,
                page=candidate.chunk.page_number,
                heading=candidate.chunk.heading,
            )
            for position, candidate in enumerate(candidates)
        ],
    )
    try:
        response = await generate_structured(
            model=settings.gemini_rerank_model,
            system_instruction=RERANK_INSTRUCTION,
            contents=content,
            json_schema=RERANK_SCHEMA,
            operation_type="rerank",
            user_id=user_id,
            lesson_plan_id=lesson_plan_id,
            max_output_tokens=1024,
        )
        parsed = RerankResponse.model_validate_json(ensure_usable(response))
    except Exception:  # best-effort stage: any failure means "use the fused order"
        logger.warning("Rerank failed; falling back to the fused order", exc_info=True)
        return None

    scores = {position: 0 for position in range(len(candidates))}
    for item in parsed.ranked:
        if item.index in scores:
            scores[item.index] = item.score
    return scores
