import asyncio
import uuid
from datetime import timedelta
from typing import AsyncIterator, Any, Sequence
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import InvalidContentError, InvalidStateError, LessonPlanNotFoundError
from app.core.services.quota_service import quota_service
from app.db.models.lesson_plan import LessonPlan
from app.db.models.profile import Profile
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.db.session import AsyncSessionLocal
from app.schemas.lesson_plan import JobStatusResponse, LessonPlanCreate
from app.schemas.lesson_plan_content import SCHEMA_VERSION, ModulContent
from app.utils.modul_docx import generate_modul_docx
from app.utils.modul_pdf import generate_modul_pdf
from app.utils.pdf_generator import generate_lesson_plan_pdf
from app.utils.text import safe_filename
from app.utils.time import utc_now

TERMINAL_STATUSES = {"completed", "failed"}
STALE_AFTER = timedelta(minutes=15)
STREAM_POLL_SECONDS = 1

class LessonPlanService:
    @staticmethod
    async def trigger_generation(db: AsyncSession, user: Profile, payload: LessonPlanCreate) -> tuple[str, uuid.UUID]:
        """
        Creates a pending plan and dispatches generation to Celery.
        Raises QuotaExceededError if the user has no plans left in the current window.
        """
        user_id = user.id
        await quota_service.ensure_available(db, user)
        job_id = str(uuid.uuid4())
        plan = await lesson_plan_repo.create(db, {
            "user_id": user_id,
            "grade_level": payload.grade_level,
            "subject": payload.subject,
            "topic": payload.topic,
            "status": "pending",
            "job_id": job_id,
            "request_options": {
                "meeting_count": payload.meeting_count,
                "minutes_per_meeting": payload.minutes_per_meeting,
                "teaching_model": payload.teaching_model.value,
                "class_notes": payload.class_notes,
            },
            "prompt_version": settings.prompt_version,
            "model_name": settings.gemini_generation_model,
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

        if plan.schema_version == SCHEMA_VERSION:
            # A saved edit must still be a valid module (e.g. a table cannot lose a column).
            try:
                content = ModulContent.model_validate(content).model_dump(mode="json")
            except ValidationError as error:
                first = error.errors()[0]
                where = ".".join(str(part) for part in first["loc"])
                raise InvalidContentError(f"Isi modul tidak sesuai format ({where}: {first['msg']}).") from error

        plan = await lesson_plan_repo.update(db, plan, {"generated_content": content})
        await db.commit()
        return plan

    @staticmethod
    async def delete_plan(db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> None:
        plan = await LessonPlanService.get_plan(db, plan_id, user_id)
        await lesson_plan_repo.delete(db, plan.id)
        await db.commit()

    @staticmethod
    async def _get_exportable(db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> LessonPlan:
        plan = await LessonPlanService.get_plan(db, plan_id, user_id)
        if plan.status != "completed" or not plan.generated_content:
            raise InvalidStateError("Lesson plan is not completed yet or has no content to export.")
        return plan

    @staticmethod
    async def export_pdf(db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> tuple[bytes, str]:
        plan = await LessonPlanService._get_exportable(db, plan_id, user_id)

        # Rendering is CPU-bound, so it runs in a thread instead of blocking the event loop.
        if plan.schema_version == SCHEMA_VERSION:
            pdf_bytes = await asyncio.to_thread(generate_modul_pdf, ModulContent.model_validate(plan.generated_content))
        else:
            pdf_bytes = await asyncio.to_thread(
                generate_lesson_plan_pdf,
                plan_metadata={
                    "grade_level": plan.grade_level,
                    "subject": plan.subject,
                    "topic": plan.topic,
                },
                content=plan.generated_content,
            )
        return pdf_bytes, safe_filename(f"Modul_Ajar_{plan.topic}", "pdf")

    @staticmethod
    async def export_docx(db: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID) -> tuple[bytes, str]:
        """Word export. Only full modules (schema version 2) have it; older plans stay PDF-only."""
        plan = await LessonPlanService._get_exportable(db, plan_id, user_id)
        if plan.schema_version != SCHEMA_VERSION:
            raise InvalidStateError("Word export is only available for modules in the current format.")

        docx_bytes = await asyncio.to_thread(generate_modul_docx, ModulContent.model_validate(plan.generated_content))
        return docx_bytes, safe_filename(f"Modul_Ajar_{plan.topic}", "docx")

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
        stage = None
        error = None
        error_code = None
        if status == "failed" and plan.generated_content:
            error = plan.generated_content.get("error")
            error_code = plan.generated_content.get("code")
        elif status not in TERMINAL_STATUSES and utc_now() - plan.created_at > STALE_AFTER:
            status = "failed"
            error = "Pembuatan modul ajar melebihi batas waktu."
            error_code = "timeout"
        elif status == "processing" and plan.generation_meta:
            stage = plan.generation_meta.get("stage")

        return JobStatusResponse(
            job_id=job_id,
            status=status,
            stage=stage,
            lesson_plan_id=plan.id,
            error=error,
            error_code=error_code,
        )

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
