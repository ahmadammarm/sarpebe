from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CurriculumDocumentResponse(BaseModel):
    id: UUID
    title: str
    document_type: str
    url_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
