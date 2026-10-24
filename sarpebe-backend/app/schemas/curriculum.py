from enum import Enum
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class DocumentType(str, Enum):
    CP = "CP"
    ATP = "ATP"
    BUKU_GURU = "BUKU_GURU"

class CurriculumDocumentResponse(BaseModel):
    id: UUID
    title: str
    document_type: str
    url_path: str
    grade_level: str | None = None
    subject: str | None = None
    status: str
    ingest_version: int = 1
    # Non-fatal findings (pages read with OCR, pages without text) or, when status is "failed", the reason.
    ingest_warnings: list[str] | None = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CurriculumDocumentUpdate(BaseModel):
    """Partial update: only the fields that are sent change."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    document_type: DocumentType | None = None
    grade_level: str | None = Field(default=None, min_length=1, max_length=20)
    subject: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("title", "grade_level", "subject")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def require_a_change(self) -> "CurriculumDocumentUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self
