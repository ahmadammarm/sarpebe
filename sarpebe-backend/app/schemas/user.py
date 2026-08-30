from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProfileResponse(BaseModel):
    id: UUID
    full_name: str
    school_name: str | None
    subscription_tier: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
