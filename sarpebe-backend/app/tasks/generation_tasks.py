import asyncio
from typing import Any
from uuid import UUID
from celery.utils.log import get_task_logger

from app.config import settings
from app.core.exceptions import (
    AppError,
    ContentBlockedError,
    InsufficientContextError,
    LLMOutputError,
    TransientLLMError,
)
from app.core.prompts.lesson_plan import ModulRequest
from app.core.services.llm_service import llm_service
from app.core.services.rag_service import rag_service
from app.db.models.lesson_plan import LessonPlan
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.db.session import task_session_scope
from app.schemas.lesson_plan_content import SCHEMA_VERSION
from app.tasks.celery_app import celery_app
from app.utils.fase import fase_for_grade

logger = get_task_logger(__name__)

MAX_RETRIES = 1  # infrastructure faults only (database, Redis); model errors are handled below
RETRY_DELAY_SECONDS = 30

# Failures where running the same request again cannot help, or would only repeat the cost.
PERMANENT_ERRORS = (InsufficientContextError, LLMOutputError, ContentBlockedError, TransientLLMError)


def _request_from_plan(plan: LessonPlan) -> ModulRequest:
    options: dict[str, Any] = plan.request_options or {}
    fase = fase_for_grade(plan.grade_level)
    return ModulRequest(
        grade_level=plan.grade_level,
        fase=fase.code if fase else None,
        subject=plan.subject,
        topic=plan.topic,
        meeting_count=int(options.get("meeting_count", 1)),
        minutes_per_meeting=int(options.get("minutes_per_meeting", 80)),
        teaching_model=str(options.get("teaching_model", "otomatis")),
        class_notes=str(options.get("class_notes", "")),
    )


INTERNAL_ERROR_MESSAGE = "Modul belum berhasil disusun karena gangguan sistem. Coba lagi."

# What the teacher reads when a permanent error stops a plan. The exception's own text is English
# developer text and may carry details, so only InsufficientContextError (already Indonesian,
# written for the teacher) passes its message through.
FAILURE_MESSAGES: dict[type[Exception], str] = {
    LLMOutputError: "Model belum menghasilkan modul yang valid. Coba buat ulang.",
    ContentBlockedError: "Model tidak dapat menyusun modul untuk topik ini. Ubah topiknya lalu coba lagi.",
    TransientLLMError: "Layanan penyusun modul sedang tidak tersedia. Coba lagi beberapa saat lagi.",
}


def _failure_for(error: AppError) -> tuple[str, str]:
    """(teacher-facing message, stable code) for an error that repeating cannot fix."""
    if isinstance(error, InsufficientContextError):
        return error.message, error.code
    return FAILURE_MESSAGES.get(type(error), INTERNAL_ERROR_MESSAGE), error.code


async def _fail(
    session_factory,
    plan_id: str,
    message: str,
    code: str,
    meta: dict[str, Any] | None = None,
) -> None:
    """Marks the plan failed in a fresh session, so an aborted transaction cannot get in the way."""
    async with session_factory() as db:
        plan = await lesson_plan_repo.get(db, plan_id)
        if plan:
            plan.status = "failed"
            plan.generated_content = {"error": message, "code": code}
            plan.generation_meta = {**(meta or {}), "failed": True}
            await db.commit()


async def _run_generation(lesson_plan_id: str, user_id: str, is_final_attempt: bool) -> None:
    """
    Retrieval, then generation, with the current stage saved on the plan so the UI can show it.

    Errors that repeating cannot fix (nothing relevant in the documents, unusable model output,
    blocked content, the model API staying down after its own retries) mark the plan failed and
    return. Anything else is re-raised so Celery can retry once; only the last attempt marks the
    plan failed.
    """
    async with task_session_scope() as session_factory:
        try:
            async with session_factory() as db:
                plan = await lesson_plan_repo.get(db, lesson_plan_id)
                if not plan:
                    logger.error(f"[{lesson_plan_id}] Lesson plan not found in database.")
                    return
                if plan.status == "completed":
                    logger.info(f"[{lesson_plan_id}] Already completed; skipping duplicate delivery.")
                    return

                async def set_stage(stage: str) -> None:
                    plan.generation_meta = {**(plan.generation_meta or {}), "stage": stage}
                    await db.commit()

                plan.status = "processing"
                plan.generation_meta = None
                await set_stage("retrieving")

                request = _request_from_plan(plan)
                retrieval = await rag_service.retrieve_context(
                    db,
                    topic=plan.topic,
                    grade_level=plan.grade_level,
                    subject=plan.subject,
                    user_id=UUID(user_id),
                    lesson_plan_id=UUID(lesson_plan_id),
                )
                logger.info(f"[{lesson_plan_id}] Retrieved {len(retrieval.passages)} passages.")

                await set_stage("drafting")
                outcome = await llm_service.generate_modul(
                    request=request,
                    passages=retrieval.passages,
                    user_id=UUID(user_id),
                    lesson_plan_id=UUID(lesson_plan_id),
                    on_stage=set_stage,
                )

                plan.generated_content = outcome.content
                plan.schema_version = SCHEMA_VERSION
                plan.prompt_version = settings.prompt_version
                plan.model_name = settings.gemini_generation_model
                plan.generation_meta = {"retrieval": retrieval.stats, "generation": outcome.meta}
                plan.status = "completed"
                await db.commit()
                logger.info(f"[{lesson_plan_id}] Generation completed successfully!")

        except PERMANENT_ERRORS as e:
            logger.warning(f"[{lesson_plan_id}] Generation stopped: {e.message}")
            message, code = _failure_for(e)
            await _fail(session_factory, lesson_plan_id, message, code)

        except Exception as e:
            logger.exception(f"[{lesson_plan_id}] Error during generation: {str(e)}")
            if not is_final_attempt:
                raise
            await _fail(session_factory, lesson_plan_id, INTERNAL_ERROR_MESSAGE, "internal_error")


@celery_app.task(
    bind=True,
    name="tasks.generate_lesson_plan",
    max_retries=MAX_RETRIES,
    soft_time_limit=420,
    time_limit=480,
)
def generate_lesson_plan_task(self, lesson_plan_id: str, user_id: str):
    """
    Synchronous Celery task wrapper that executes the async RAG and LLM pipeline.
    """
    logger.info(f"STARTING GENERATION TASK for plan {lesson_plan_id} (attempt {self.request.retries + 1})")

    is_final_attempt = self.request.retries >= self.max_retries
    try:
        asyncio.run(_run_generation(lesson_plan_id, user_id, is_final_attempt))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=RETRY_DELAY_SECONDS)
