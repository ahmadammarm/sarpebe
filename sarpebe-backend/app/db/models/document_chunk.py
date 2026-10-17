import uuid
from sqlalchemy import Computed, String, Text, Integer, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
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
    # Nearest heading above the chunk, e.g. "Elemen Pemahaman IPS".
    heading: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_type: Mapped[str] = mapped_column(String, default="text", server_default=text("'text'"), nullable=False)  # 'text' | 'table'
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Which model produced `embedding`, so vectors from different models are never mixed silently.
    embedding_model: Mapped[str | None] = mapped_column(String, nullable=True)
    # Full-text index over heading + content (Indonesian stemming), kept in sync by Postgres.
    search_vector = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('indonesian', coalesce(heading, '') || ' ' || chunk_content)", persisted=True),
        nullable=True,
    )

    # Relationships
    document: Mapped["CurriculumDocument"] = relationship("CurriculumDocument", back_populates="document_chunks")
