from enum import Enum
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

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
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
