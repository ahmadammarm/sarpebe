import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate, LessonPlanResponse, JobStatusResponse
from app.schemas.common import PaginatedResponse
from app.core.services.lesson_plan_service import lesson_plan_service
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.core.exceptions import QuotaExceededError
from app.db.models.profile import Profile
from app.utils.pdf_generator import generate_lesson_plan_pdf

router = APIRouter(prefix="/lesson-plans", tags=["Lesson Plans"])

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_lesson_plan(
    payload: LessonPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    try:
        job_id, plan_id = await lesson_plan_service.trigger_generation(db, current_user.id, payload)
        await db.commit()
        return {"job_id": job_id, "id": str(plan_id)}
    except QuotaExceededError as e:
        await db.rollback()
        raise HTTPException(status_code=403, detail=str(e))

@router.get("", response_model=PaginatedResponse[LessonPlanResponse])
async def list_lesson_plans(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    items, total = await lesson_plan_repo.get_multi_by_user(db, current_user.id, skip, limit)
    return PaginatedResponse(items=list(items), total=total, skip=skip, limit=limit)

@router.get("/{id}", response_model=LessonPlanResponse)
async def get_lesson_plan(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    plan = await lesson_plan_repo.get_by_id_and_user(db, id, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    return plan

@router.put("/{id}", response_model=LessonPlanResponse)
async def update_lesson_plan(
    id: uuid.UUID,
    payload: LessonPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    plan = await lesson_plan_repo.get_by_id_and_user(db, id, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    plan.generated_content = payload.generated_content
    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson_plan(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    plan = await lesson_plan_repo.get_by_id_and_user(db, id, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    await db.delete(plan)
    await db.commit()
    return None

@router.get("/{id}/export/pdf")
async def export_lesson_plan_pdf(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    plan = await lesson_plan_repo.get_by_id_and_user(db, id, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    if plan.status != "completed" or not plan.generated_content:
        raise HTTPException(status_code=400, detail="Lesson plan is not completed yet or has no content to export.")

    pdf_bytes = generate_lesson_plan_pdf(
        plan_metadata={
            "grade_level": plan.grade_level,
            "subject": plan.subject,
            "topic": plan.topic
        },
        content=plan.generated_content
    )

    safe_title = plan.topic.replace(" ", "_")
    filename = f"Modul_Ajar_{safe_title}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    from app.tasks.celery_app import celery_app
    from celery.result import AsyncResult

    result = AsyncResult(job_id, app=celery_app)

    state = result.state.lower()
    if state == "success":
        state = "completed"

    return JobStatusResponse(job_id=job_id, status=state)

@router.get("/jobs/{job_id}/stream")
async def stream_job_status(job_id: str):
    """
    Server-Sent Events (SSE) endpoint to stream generation task progress in real time.
    """
    from app.tasks.celery_app import celery_app
    from celery.result import AsyncResult

    async def event_generator():
        result = AsyncResult(job_id, app=celery_app)
        while True:
            state = result.state.lower()
            if state == "success":
                state = "completed"

            payload = {"job_id": job_id, "status": state}
            yield f"data: {json.dumps(payload)}\n\n"

            if state in ["completed", "failed", "revoked"]:
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

