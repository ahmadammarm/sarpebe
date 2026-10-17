import asyncio
import uuid
from datetime import timedelta
from typing import AsyncIterator, Any, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidStateError, LessonPlanNotFoundError
from app.db.models.lesson_plan import LessonPlan
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.db.session import AsyncSessionLocal
from app.schemas.lesson_plan import JobStatusResponse, LessonPlanCreate
from app.utils.pdf_generator import generate_lesson_plan_pdf
from app.utils.time import utc_now

TERMINAL_STATUSES = {"completed", "failed"}
STALE_AFTER = timedelta(minutes=15)
STREAM_POLL_SECONDS = 1

class LessonPlanService:
    @staticmethod
    async def trigger_generation(db: AsyncSession, user_id: uuid.UUID, payload: LessonPlanCreate) -> tuple[str, uuid.UUID]:
        """
        Creates a pending plan and dispatches generation to Celery.
        """
        job_id = str(uuid.uuid4())
        plan = await lesson_plan_repo.create(db, {
            "user_id": user_id,
            "grade_level": payload.grade_level,
            "subject": payload.subject,
            "topic": payload.topic,
            "status": "pending",
            "job_id": job_id,
        })
        # Commit before dispatch so the worker is guaranteed to see the row.
        # (Explicit commit rather than session.begin(): the request session has already autobegun.)
        await db.commit()

        from app.tasks.generation_tasks import generate_lesson_plan_task
        generate_lesson_plan_task.apply_async(args=[str(plan.id), str(user_id)], task_id=job_id)

        return job_id, plan.id

    @staticmethod
    async def list_plans(db: AsyncSession, user_id: uuid.UUID, skip: int, limit: int) -> tuple[Sequence[LessonPlan], int]:
        return await lesson_plan_repo.get_multi_by_user(db, user_id, skip, limit)

    @staticmethod
    async def get_plan(db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> LessonPlan:
        plan = await lesson_plan_repo.get_by_id_and_user(db, plan_id, user_id)
        if not plan:
            raise LessonPlanNotFoundError("Lesson plan not found")
        return plan

    @staticmethod
    async def update_content(db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID, content: dict[str, Any]) -> LessonPlan:
        plan = await LessonPlanService.get_plan(db, plan_id, user_id)
        if plan.status != "completed":
            raise InvalidStateError("Only completed lesson plans can be edited.")
        plan = await lesson_plan_repo.update(db, plan, {"generated_content": content})
        await db.commit()
        return plan

    @staticmethod
    async def delete_plan(db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> None:
        plan = await LessonPlanService.get_plan(db, plan_id, user_id)
        await lesson_plan_repo.delete(db, plan.id)
        await db.commit()

    @staticmethod
    async def export_pdf(db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> tuple[bytes, str]:
        plan = await LessonPlanService.get_plan(db, plan_id, user_id)
        if plan.status != "completed" or not plan.generated_content:
            raise InvalidStateError("Lesson plan is not completed yet or has no content to export.")

        pdf_bytes = generate_lesson_plan_pdf(
            plan_metadata={
                "grade_level": plan.grade_level,
                "subject": plan.subject,
                "topic": plan.topic,
            },
            content=plan.generated_content,
        )
        filename = f"Modul_Ajar_{plan.topic.replace(' ', '_')}.pdf"
        return pdf_bytes, filename

    @staticmethod
    async def get_job_status(db: AsyncSession, job_id: str, user_id: uuid.UUID) -> JobStatusResponse:
        """
        Reports job progress from the lesson plan row (the source of truth), scoped to its owner.
        Plans stuck unfinished for longer than STALE_AFTER are reported as timed out.
        """
        plan = await lesson_plan_repo.get_by_job_id_and_user(db, job_id, user_id)
        if not plan:
            raise LessonPlanNotFoundError("Job not found")

        status = plan.status
        error = None
        if status == "failed" and plan.generated_content:
            error = plan.generated_content.get("error")
        elif status not in TERMINAL_STATUSES and utc_now() - plan.created_at > STALE_AFTER:
            status = "failed"
            error = "Pembuatan modul ajar melebihi batas waktu."

        return JobStatusResponse(job_id=job_id, status=status, lesson_plan_id=plan.id, error=error)

    @staticmethod
    async def stream_job_status(job_id: str, user_id: uuid.UUID) -> AsyncIterator[JobStatusResponse]:
        """
        Yields the job status once per second until it reaches a terminal state.
        Uses a short-lived session per poll so no connection is held while streaming.
        """
        while True:
            async with AsyncSessionLocal() as session:
                job = await LessonPlanService.get_job_status(session, job_id, user_id)
            yield job
            if job.status in TERMINAL_STATUSES:
                return
            await asyncio.sleep(STREAM_POLL_SECONDS)

lesson_plan_service = LessonPlanService()
