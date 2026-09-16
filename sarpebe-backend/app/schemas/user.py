from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProfileResponse(BaseModel):
    id: UUID
    full_name: str
    school_name: str | None
    subscription_tier: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CostSummaryResponse(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_cost: float

class UserCostSummaryResponse(CostSummaryResponse):
    user_id: UUID
