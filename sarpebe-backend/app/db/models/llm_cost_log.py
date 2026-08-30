import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class LLMCostLog(Base):
    __tablename__ = "llm_cost_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    lesson_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lesson_plans.id", ondelete="SET NULL"), nullable=True)
    operation_type: Mapped[str] = mapped_column(String, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0.0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    user: Mapped["Profile"] = relationship("Profile", back_populates="llm_cost_logs")
    lesson_plan: Mapped["LessonPlan"] = relationship("LessonPlan", back_populates="llm_cost_log")
