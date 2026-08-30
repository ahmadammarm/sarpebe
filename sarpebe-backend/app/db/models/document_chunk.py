import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("curriculum_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(768), nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_level: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    # Relationships
    document: Mapped["CurriculumDocument"] = relationship("CurriculumDocument", back_populates="document_chunks")
