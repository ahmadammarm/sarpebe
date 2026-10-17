from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

class TeachingModel(str, Enum):
    OTOMATIS = "otomatis"
    DISKUSI_KELOMPOK = "diskusi_kelompok"
    PJBL = "pjbl"
    PBL = "pbl"
    INKUIRI = "inkuiri"
    KOOPERATIF = "kooperatif"
    CERAMAH_INTERAKTIF = "ceramah_interaktif"

class LessonPlanCreate(BaseModel):
    grade_level: str = Field(min_length=1, max_length=20)
    subject: str = Field(min_length=1, max_length=100)
    topic: str = Field(min_length=1, max_length=300)
    meeting_count: int = Field(default=1, ge=1, le=6)
    minutes_per_meeting: int = Field(default=80, ge=20, le=240)
    teaching_model: TeachingModel = TeachingModel.OTOMATIS
    class_notes: str = Field(default="", max_length=500)

    @field_validator("grade_level", "subject", "topic")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("class_notes")
    @classmethod
    def strip_notes(cls, value: str) -> str:
        return value.strip()

class LessonPlanUpdate(BaseModel):
    generated_content: dict[str, Any]

class LessonPlanResponse(BaseModel):
    id: UUID
    grade_level: str
    subject: str
    topic: str
    generated_content: dict[str, Any] | None = None
    schema_version: int = 1
    request_options: dict[str, Any] | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending | processing | completed | failed
    # While processing: retrieving | drafting | repairing. None otherwise.
    stage: str | None = None
    lesson_plan_id: UUID | None = None
    error: str | None = None
