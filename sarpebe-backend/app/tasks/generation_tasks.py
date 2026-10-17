import asyncio
from uuid import UUID
from celery.utils.log import get_task_logger

from app.tasks.celery_app import celery_app
from app.db.session import task_session_scope
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.core.services.rag_service import rag_service
from app.core.services.llm_service import llm_service

logger = get_task_logger(__name__)

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 60
NO_CONTEXT_ERROR = "Belum ada dokumen kurikulum untuk kelas/mata pelajaran ini."

async def _run_generation(lesson_plan_id: str, user_id: str, is_final_attempt: bool) -> None:
    """
    Async core of the generation task.

    Deterministic failures (no curriculum context, LLM returned unusable output) mark the plan
    failed and return. Unexpected exceptions are re-raised so Celery can retry; only on the final
    attempt is the plan marked failed.
    """
    async with task_session_scope() as session_factory:
        try:
            async with session_factory() as db:
                logger.info(f"[{lesson_plan_id}] Step 1: Fetching pending lesson plan...")
                plan = await lesson_plan_repo.get(db, lesson_plan_id)
                if not plan:
                    logger.error(f"[{lesson_plan_id}] Lesson plan not found in database.")
                    return
                if plan.status == "completed":
                    logger.info(f"[{lesson_plan_id}] Already completed; skipping duplicate delivery.")
                    return

                plan.status = "processing"
                await db.commit()

                logger.info(f"[{lesson_plan_id}] Step 2: Retrieving context chunks via RAG...")
                context_chunks = await rag_service.retrieve_context(
                    db=db,
                    topic=plan.topic,
                    grade_level=plan.grade_level,
                    subject=plan.subject,
                    user_id=UUID(user_id)
                )
                logger.info(f"[{lesson_plan_id}] Retrieved {len(context_chunks)} chunks for context.")

                if not context_chunks:
                    plan.status = "failed"
                    plan.generated_content = {"error": NO_CONTEXT_ERROR}
                    await db.commit()
                    logger.warning(f"[{lesson_plan_id}] No curriculum context found; skipping LLM call.")
                    return

                logger.info(f"[{lesson_plan_id}] Step 3: Generating structured lesson plan via Gemini API...")
                generated_content = await llm_service.generate_lesson_plan(
                    context_chunks=context_chunks,
                    grade_level=plan.grade_level,
                    subject=plan.subject,
                    topic=plan.topic,
                    user_id=UUID(user_id),
                    lesson_plan_id=UUID(lesson_plan_id)
                )

                plan.generated_content = generated_content
                if "error" in generated_content:
                    plan.status = "failed"
                    logger.error(f"[{lesson_plan_id}] Step 4: LLM Generation failed with error: {generated_content.get('error')}")
                else:
                    plan.status = "completed"
                    logger.info(f"[{lesson_plan_id}] Step 4: Generation completed successfully!")

                await db.commit()

        except Exception as e:
            logger.exception(f"[{lesson_plan_id}] Error during generation: {str(e)}")
            if not is_final_attempt:
                raise

            async with session_factory() as fallback_db:
                failed_plan = await lesson_plan_repo.get(fallback_db, lesson_plan_id)
                if failed_plan:
                    failed_plan.status = "failed"
                    failed_plan.generated_content = {"error": f"Task crashed: {str(e)}"}
                    await fallback_db.commit()

@celery_app.task(bind=True, name="tasks.generate_lesson_plan", max_retries=MAX_RETRIES, soft_time_limit=240, time_limit=300)
def generate_lesson_plan_task(self, lesson_plan_id: str, user_id: str):
    """
    Synchronous Celery task wrapper that executes the async RAG and LLM pipeline.
    Retries transient errors (e.g. Gemini rate limits) up to MAX_RETRIES times.
    """
    logger.info(f"STARTING GENERATION TASK for plan {lesson_plan_id} (attempt {self.request.retries + 1})")

    is_final_attempt = self.request.retries >= self.max_retries
    try:
        asyncio.run(_run_generation(lesson_plan_id, user_id, is_final_attempt))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=RETRY_DELAY_SECONDS)
