from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

class LessonPlanCreate(BaseModel):
    grade_level: str = Field(min_length=1, max_length=20)
    subject: str = Field(min_length=1, max_length=100)
    topic: str = Field(min_length=1, max_length=300)

    @field_validator("grade_level", "subject", "topic")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

class LessonPlanUpdate(BaseModel):
    generated_content: dict[str, Any]

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
    status: str  # pending | processing | completed | failed
    lesson_plan_id: UUID | None = None
    error: str | None = None
