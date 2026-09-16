import asyncio
from uuid import UUID
from celery.utils.log import get_task_logger

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.core.services.rag_service import rag_service
from app.core.services.llm_service import llm_service

logger = get_task_logger(__name__)

async def _run_generation(lesson_plan_id: str, user_id: str) -> None:
    """Async core of the generation task."""
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"[{lesson_plan_id}] Step 1: Fetching pending lesson plan...")
            plan = await lesson_plan_repo.get(db, lesson_plan_id)
            if not plan:
                logger.error(f"[{lesson_plan_id}] Lesson plan not found in database.")
                return

            logger.info(f"[{lesson_plan_id}] Step 2: Retrieving context chunks via RAG...")
            context_chunks = await rag_service.retrieve_context(
                db=db,
                topic=plan.topic,
                grade_level=plan.grade_level,
                subject=plan.subject,
                user_id=UUID(user_id)
            )
            logger.info(f"[{lesson_plan_id}] Retrieved {len(context_chunks)} chunks for context.")

            logger.info(f"[{lesson_plan_id}] Step 3: Generating structured lesson plan via Gemini API...")
            generated_content = await llm_service.generate_lesson_plan(
                db=db,
                context_chunks=context_chunks,
                grade_level=plan.grade_level,
                subject=plan.subject,
                topic=plan.topic,
                user_id=UUID(user_id),
                lesson_plan_id=UUID(lesson_plan_id)
            )

            # 4. Update the lesson plan status
            if "error" in generated_content:
                plan.status = "failed"
                plan.generated_content = generated_content
                logger.error(f"[{lesson_plan_id}] Step 4: LLM Generation failed with error: {generated_content.get('error')}")
            else:
                plan.status = "completed"
                plan.generated_content = generated_content
                logger.info(f"[{lesson_plan_id}] Step 4: Generation completed successfully!")

            await db.commit()

        except Exception as e:
            logger.exception(f"[{lesson_plan_id}] FATAL ERROR during generation: {str(e)}")
            await db.rollback()

            # Use a fresh transaction to ensure we mark the plan as failed
            async with AsyncSessionLocal() as fallback_db:
                failed_plan = await lesson_plan_repo.get(fallback_db, lesson_plan_id)
                if failed_plan:
                    failed_plan.status = "failed"
                    # Optionally record the error message inside the JSON content so frontend can show why it failed
                    failed_plan.generated_content = {"error": f"Task crashed: {str(e)}"}
                    await fallback_db.commit()
            raise e

# autoretry_for catches exceptions like rate limits (e.g. from google genai library) and retries the task
# max_retries=2 means it will attempt 3 times total. default_retry_delay=60 means it waits 60s between retries.
@celery_app.task(bind=True, name="tasks.generate_lesson_plan", autoretry_for=(Exception,), retry_kwargs={'max_retries': 2}, default_retry_delay=60)
def generate_lesson_plan_task(self, lesson_plan_id: str, user_id: str):
    """
    Synchronous Celery task wrapper that executes the async RAG and LLM pipeline.
    """
    logger.info(f"==================================================")
    logger.info(f"STARTING GENERATION TASK for plan {lesson_plan_id}")
    logger.info(f"==================================================")

    try:
        asyncio.run(_run_generation(lesson_plan_id, user_id))
    except Exception as exc:
        logger.error(f"Task failed, preparing for potential retry: {str(exc)}")
        raise exc
