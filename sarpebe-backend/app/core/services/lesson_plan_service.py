import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.user_repository import user_repo
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.schemas.lesson_plan import LessonPlanCreate
from app.core.exceptions import QuotaExceededError
from app.config import settings

class LessonPlanService:
    @staticmethod
    async def trigger_generation(db: AsyncSession, user_id: uuid.UUID, payload: LessonPlanCreate) -> str:
        """
        Validates quota using row-level locking, creates a pending plan, and dispatches to Celery.
        """
        user = await user_repo.get_by_id_for_update(db, str(user_id))
        
        # Check quota dynamically by counting existing plans
        _, count = await lesson_plan_repo.get_multi_by_user(db, user_id, 0, 1)
        if user.subscription_tier == "free" and count >= settings.free_tier_quota:
            raise QuotaExceededError(f"Free tier limit of {settings.free_tier_quota} reached.")
            
        plan = await lesson_plan_repo.create(db, {
            "user_id": user_id,
            "grade_level": payload.grade_level,
            "subject": payload.subject,
            "topic": payload.topic,
            "status": "pending"
        })
        
        # Dispatch background generation task (task defined in Phase 6)
        from app.tasks.celery_app import celery_app
        job = celery_app.send_task(
            "tasks.generate_lesson_plan",
            args=[str(plan.id), str(user_id)]
        )
        
        return job.id

lesson_plan_service = LessonPlanService()
