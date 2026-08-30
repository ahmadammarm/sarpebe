import uuid
from datetime import datetime
from sqlalchemy import String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    school_name: Mapped[str | None] = mapped_column(String, nullable=True)
    subscription_tier: Mapped[str] = mapped_column(String, default="free")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    lesson_plans: Mapped[list["LessonPlan"]] = relationship("LessonPlan", back_populates="user", cascade="all, delete-orphan")
    llm_cost_logs: Mapped[list["LLMCostLog"]] = relationship("LLMCostLog", back_populates="user", cascade="all, delete-orphan")
