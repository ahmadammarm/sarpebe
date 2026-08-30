from typing import Sequence
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.lesson_plan import LessonPlan
from app.db.repositories.base_repository import BaseRepository
from app.schemas.lesson_plan import LessonPlanCreate

class LessonPlanRepository(BaseRepository[LessonPlan, LessonPlanCreate, dict]):
    def __init__(self):
        super().__init__(LessonPlan)
        
    async def get_multi_by_user(
        self, db: AsyncSession, user_id: UUID | str, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[LessonPlan], int]:
        """
        Fetches a paginated list of lesson plans for a specific user,
        returning both the items and the total count.
        """
        # Execute total count query
        count_result = await db.execute(
            select(func.count()).filter(self.model.user_id == user_id)
        )
        total = count_result.scalar_one()
        
        # Execute data query
        result = await db.execute(
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = result.scalars().all()
        return items, total

    async def get_by_id_and_user(self, db: AsyncSession, id: UUID | str, user_id: UUID | str) -> LessonPlan | None:
        """
        Fetches a single lesson plan ensuring the user owns it.
        """
        result = await db.execute(
            select(self.model).filter(self.model.id == id, self.model.user_id == user_id)
        )
        return result.scalar_one_or_none()

lesson_plan_repo = LessonPlanRepository()
