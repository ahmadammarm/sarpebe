import json
from uuid import UUID
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field

from app.config import settings
from app.db.models.llm_cost_log import LLMCostLog
from app.db.models.document_chunk import DocumentChunk
from app.utils.cost_calculator import calculate_cost

client = genai.Client(api_key=settings.gemini_api_key)

class LessonPlanSchema(BaseModel):
    title: str = Field(description="Title of the lesson plan")
    objectives: list[str] = Field(description="Learning objectives")
    materials: list[str] = Field(description="Required materials")
    activities: list[dict[str, str]] = Field(description="List of activities. Each dict must have 'duration' and 'description' keys.")
    assessment: str = Field(description="How to assess learning")
    citations: list[str] = Field(description="Exact source document names and page numbers cited from context")

class LLMService:
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True
    )
    async def generate_lesson_plan(
        db: AsyncSession,
        context_chunks: list[DocumentChunk],
        grade_level: str,
        subject: str,
        topic: str,
        user_id: UUID,
        lesson_plan_id: UUID
    ) -> dict[str, Any]:
        """
        Generates a lesson plan using strict JSON schema and prompt engineering.
        """
        context_text = ""
        for chunk in context_chunks:
            doc_name = chunk.document.title if chunk.document else "Unknown Document"
            page = chunk.page_number or "N/A"
            context_text += f"\n--- Source: {doc_name} (Page {page}) ---\n{chunk.chunk_content}\n"

        prompt = f"""
        You are an expert curriculum designer and educator.
        Generate a structured lesson plan for Grade {grade_level}, Subject: {subject}, Topic: {topic}.
        
        CRITICAL RULES:
        1. Base your lesson plan strictly on the official curriculum context provided below. Do not hallucinate outside information.
        2. You MUST cite the source document names and page numbers from the context in the 'citations' field.
        3. You MUST generate the entire lesson plan in Indonesian (Bahasa Indonesia).
        
        CONTEXT:
        {context_text}
        """

        response = await client.aio.models.generate_content(
            model=settings.gemini_generation_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LessonPlanSchema,
                temperature=0.2,
            )
        )
        
        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count if usage else 0
        comp_tokens = usage.candidates_token_count if usage else 0
        cost = calculate_cost(settings.gemini_generation_model, prompt_tokens, comp_tokens)
        
        cost_log = LLMCostLog(
            user_id=user_id,
            lesson_plan_id=lesson_plan_id,
            operation_type="generation",
            prompt_tokens=prompt_tokens,
            completion_tokens=comp_tokens,
            total_cost=cost
        )
        db.add(cost_log)
        await db.flush()
        
        try:
            return json.loads(response.text)
        except Exception:
            return {"error": "Failed to parse structured JSON from Gemini", "raw": response.text}

llm_service = LLMService()
