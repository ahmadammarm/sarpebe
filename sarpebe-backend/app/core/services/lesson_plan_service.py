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
        Creates a pending plan and dispatches to Celery (unlimited/free tier for now).
        """
        plan = await lesson_plan_repo.create(db, {
            "user_id": user_id,
            "grade_level": payload.grade_level,
            "subject": payload.subject,
            "topic": payload.topic,
            "status": "pending"
        })

        # Dispatch background generation task
        from app.tasks.generation_tasks import generate_lesson_plan_task
        job = generate_lesson_plan_task.delay(str(plan.id), str(user_id))

        return job.id

lesson_plan_service = LessonPlanService()
