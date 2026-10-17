import uuid
from app.db.models.llm_cost_log import LLMCostLog
from app.db.session import get_session_factory
from app.utils.cost_calculator import calculate_cost


async def log_cost(
    *,
    model_name: str,
    operation_type: str,
    user_id: uuid.UUID,
    prompt_tokens: int,
    completion_tokens: int = 0,
    lesson_plan_id: uuid.UUID | None = None,
) -> float:
    """
    Records an LLM call in llm_cost_logs using its own session and commit, so the cost
    is persisted even if the surrounding pipeline later rolls back or retries
    (the Gemini call was already billed).
    """
    cost = calculate_cost(model_name, prompt_tokens, completion_tokens)
    async with get_session_factory()() as session:
        session.add(
            LLMCostLog(
                user_id=user_id,
                lesson_plan_id=lesson_plan_id,
                operation_type=operation_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_cost=cost,
            )
        )
        await session.commit()
    return cost
