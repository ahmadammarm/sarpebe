import math
from typing import Literal
from uuid import UUID

from google.genai import types

from app.config import settings
from app.core.llm_client import call_with_retry, client
from app.core.services.cost_logging import log_cost

EMBEDDING_DIMENSIONS = 768

Purpose = Literal["document", "query"]

TASK_TYPES: dict[Purpose, str] = {
    "document": "RETRIEVAL_DOCUMENT",
    "query": "RETRIEVAL_QUERY",
}


def l2_normalize(vector: list[float]) -> list[float]:
    """
    Scales a vector to unit length. Truncating an embedding to fewer dimensions leaves it
    unnormalized, and normalizing keeps every stored vector comparable regardless of length.
    """
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


class EmbeddingService:
    @staticmethod
    async def _embed_request(texts: list[str], purpose: Purpose) -> list[list[float]]:
        config_args: dict = {"output_dimensionality": EMBEDDING_DIMENSIONS}
        if settings.embedding_use_task_types:
            config_args["task_type"] = TASK_TYPES[purpose]

        response = await call_with_retry(
            lambda: client.aio.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=texts,
                config=types.EmbedContentConfig(**config_args),
            )
        )
        return [l2_normalize(list(e.values)) for e in response.embeddings]

    @staticmethod
    async def embed_texts(
        texts: list[str],
        user_id: UUID,
        *,
        purpose: Purpose = "document",
        lesson_plan_id: UUID | None = None,
    ) -> list[list[float]]:
        """
        Embeds a batch of texts in one Gemini call (transient errors are retried) and logs a
        single cost row for the batch. If the API does not return exactly one embedding per
        input, falls back to one call per text.
        """
        if not texts:
            return []

        embeddings = await EmbeddingService._embed_request(texts, purpose)
        if len(embeddings) != len(texts):
            embeddings = [(await EmbeddingService._embed_request([t], purpose))[0] for t in texts]

        # Token usage is not returned by embed_content; estimate roughly 4 chars per token.
        prompt_tokens = sum(len(t) for t in texts) // 4
        await log_cost(
            model_name=settings.gemini_embedding_model,
            operation_type="embedding",
            user_id=user_id,
            lesson_plan_id=lesson_plan_id,
            prompt_tokens=prompt_tokens,
        )
        return embeddings

    @staticmethod
    async def embed_text(
        text: str,
        user_id: UUID,
        *,
        purpose: Purpose = "document",
        lesson_plan_id: UUID | None = None,
    ) -> list[float]:
        return (await EmbeddingService.embed_texts([text], user_id, purpose=purpose, lesson_plan_id=lesson_plan_id))[0]

embedding_service = EmbeddingService()
