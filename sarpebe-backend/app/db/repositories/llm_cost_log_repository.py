from typing import Dict, Any, Optional
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.repositories.base_repository import BaseRepository
from app.db.models.llm_cost_log import LLMCostLog

class LLMCostLogCreate(BaseModel):
    pass

class LLMCostLogUpdate(BaseModel):
    pass

class LLMCostLogRepository(BaseRepository[LLMCostLog, LLMCostLogCreate, LLMCostLogUpdate]):
    async def get_user_aggregated_costs(self, db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Returns aggregated prompt tokens, completion tokens, and total cost for a specific user."""
        stmt = (
            select(
                func.sum(LLMCostLog.prompt_tokens).label("total_prompt_tokens"),
                func.sum(LLMCostLog.completion_tokens).label("total_completion_tokens"),
                func.sum(LLMCostLog.total_cost).label("total_cost"),
            )
            .where(LLMCostLog.user_id == user_id)
        )

        result = await db.execute(stmt)
        row = result.first()

        return {
            "prompt_tokens": row.total_prompt_tokens or 0,
            "completion_tokens": row.total_completion_tokens or 0,
            "total_cost": float(row.total_cost or 0.0)
        }

    async def get_all_users_aggregated_costs(self, db: AsyncSession) -> list[Dict[str, Any]]:
        """Returns aggregated costs grouped by user_id."""
        stmt = (
            select(
                LLMCostLog.user_id,
                func.sum(LLMCostLog.prompt_tokens).label("total_prompt_tokens"),
                func.sum(LLMCostLog.completion_tokens).label("total_completion_tokens"),
                func.sum(LLMCostLog.total_cost).label("total_cost"),
            )
            .group_by(LLMCostLog.user_id)
        )

        result = await db.execute(stmt)
        rows = result.all()

        return [
            {
                "user_id": str(row.user_id),
                "prompt_tokens": row.total_prompt_tokens or 0,
                "completion_tokens": row.total_completion_tokens or 0,
                "total_cost": float(row.total_cost or 0.0)
            }
            for row in rows
        ]

llm_cost_log_repo = LLMCostLogRepository(LLMCostLog)
