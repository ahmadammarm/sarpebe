from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict

class LessonPlanCreate(BaseModel):
    grade_level: str
    subject: str
    topic: str

class LessonPlanResponse(BaseModel):
    id: UUID
    grade_level: str
    subject: str
    topic: str
    generated_content: dict[str, Any] | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending | completed | failed
    lesson_plan_id: UUID | None = None
