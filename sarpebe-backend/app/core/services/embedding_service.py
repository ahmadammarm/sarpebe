from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.db.models.llm_cost_log import LLMCostLog
from app.utils.cost_calculator import calculate_cost

client = genai.Client(api_key=settings.gemini_api_key)

from google.genai import types

class EmbeddingService:
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True
    )
    async def embed_text(db: AsyncSession, text: str, user_id: UUID) -> list[float]:
        """
        Embeds text using Gemini. Implements 3 retries with exponential backoff.
        Logs the cost to the database within the provided transaction.
        """
        response = await client.aio.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )

        
        embedding = response.embeddings[0].values
        
        # Estimate token cost (roughly 4 chars per token) if usage is not explicitly returned.
        prompt_tokens = len(text) // 4  
        
        cost = calculate_cost(settings.gemini_embedding_model, prompt_tokens=prompt_tokens, completion_tokens=0)
        
        cost_log = LLMCostLog(
            user_id=user_id,
            operation_type="embedding",
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            total_cost=cost
        )
        db.add(cost_log)
        await db.flush()
        
        return embedding

embedding_service = EmbeddingService()
