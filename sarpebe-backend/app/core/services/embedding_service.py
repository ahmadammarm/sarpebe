from uuid import UUID
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.core.services.cost_logging import log_cost

client = genai.Client(api_key=settings.gemini_api_key)

EMBEDDING_DIMENSIONS = 768

class EmbeddingService:
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True
    )
    async def _embed_request(texts: list[str]) -> list[list[float]]:
        response = await client.aio.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS)
        )
        return [list(e.values) for e in response.embeddings]

    @staticmethod
    async def embed_texts(texts: list[str], user_id: UUID) -> list[list[float]]:
        """
        Embeds a batch of texts in one Gemini call (3 retries with exponential backoff) and
        logs a single cost row for the batch. If the API does not return exactly one
        embedding per input, falls back to one call per text.
        """
        if not texts:
            return []

        embeddings = await EmbeddingService._embed_request(texts)
        if len(embeddings) != len(texts):
            embeddings = [(await EmbeddingService._embed_request([t]))[0] for t in texts]

        # Token usage is not returned by embed_content; estimate roughly 4 chars per token.
        prompt_tokens = sum(len(t) for t in texts) // 4
        await log_cost(
            model_name=settings.gemini_embedding_model,
            operation_type="embedding",
            user_id=user_id,
            prompt_tokens=prompt_tokens,
        )
        return embeddings

    @staticmethod
    async def embed_text(text: str, user_id: UUID) -> list[float]:
        return (await EmbeddingService.embed_texts([text], user_id))[0]

embedding_service = EmbeddingService()
