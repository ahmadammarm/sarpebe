import uuid
from datetime import datetime
from sqlalchemy import Integer, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base
from app.utils.time import utc_now

class CurriculumDocument(Base):
    __tablename__ = "curriculum_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False) # 'CP', 'ATP', 'BUKU_GURU'
    url_path: Mapped[str] = mapped_column(String, nullable=False)
    grade_level: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="processing")
    # Which ingestion pipeline produced the chunks (2 = tables kept, heading-aware chunking).
    ingest_version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    # Non-fatal problems found while reading the PDF, e.g. pages without extractable text.
    ingest_warnings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now)

    # Relationships
    document_chunks: Mapped[list["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
