import uuid
from fastapi import APIRouter, Depends, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate, LessonPlanResponse, JobStatusResponse
from app.schemas.common import PaginatedResponse
from app.core.services.lesson_plan_service import lesson_plan_service
from app.db.models.profile import Profile

router = APIRouter(prefix="/lesson-plans", tags=["Lesson Plans"])

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_lesson_plan(
    payload: LessonPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    job_id, plan_id = await lesson_plan_service.trigger_generation(db, current_user.id, payload)
    return {"job_id": job_id, "id": str(plan_id)}

@router.get("", response_model=PaginatedResponse[LessonPlanResponse])
async def list_lesson_plans(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    items, total = await lesson_plan_service.list_plans(db, current_user.id, skip, limit)
    return PaginatedResponse(items=list(items), total=total, skip=skip, limit=limit)

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    return await lesson_plan_service.get_job_status(db, job_id, current_user.id)

@router.get("/jobs/{job_id}/stream")
async def stream_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Server-Sent Events (SSE) endpoint to stream generation progress in real time.
    Ownership is verified before the stream opens (404 for jobs the caller does not own).
    """
    await lesson_plan_service.get_job_status(db, job_id, current_user.id)

    async def event_generator():
        async for job in lesson_plan_service.stream_job_status(job_id, current_user.id):
            yield f"data: {job.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/{id}", response_model=LessonPlanResponse)
async def get_lesson_plan(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    return await lesson_plan_service.get_plan(db, id, current_user.id)

@router.put("/{id}", response_model=LessonPlanResponse)
async def update_lesson_plan(
    id: uuid.UUID,
    payload: LessonPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    return await lesson_plan_service.update_content(db, id, current_user.id, payload.generated_content)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson_plan(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    await lesson_plan_service.delete_plan(db, id, current_user.id)
    return None

@router.get("/{id}/export/pdf")
async def export_lesson_plan_pdf(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    pdf_bytes, filename = await lesson_plan_service.export_pdf(db, id, current_user.id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
