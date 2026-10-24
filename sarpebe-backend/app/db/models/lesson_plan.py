import uuid
from datetime import datetime
from sqlalchemy import Index, Integer, String, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base
from app.utils.time import utc_now

class LessonPlan(Base):
    __tablename__ = "lesson_plans"
    # Serves the per-user list and the generation quota ("plans of this user since ...").
    __table_args__ = (Index("ix_lesson_plans_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    grade_level: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    generated_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending | processing | completed | failed
    job_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    # Shape of generated_content: 1 = the original simple format, 2 = full Modul Ajar with tables.
    schema_version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    # What the teacher asked for beyond grade/subject/topic (meeting count, minutes, model, notes).
    request_options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Traceability: which prompt and model produced the content, and how (retrieval, stages, tokens).
    prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    generation_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now)

    # Relationships
    user: Mapped["Profile"] = relationship("Profile", back_populates="lesson_plans")
    llm_cost_logs: Mapped[list["LLMCostLog"]] = relationship("LLMCostLog", back_populates="lesson_plan")
