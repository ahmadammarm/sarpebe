import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanResponse, JobStatusResponse
from app.schemas.common import PaginatedResponse
from app.core.services.lesson_plan_service import lesson_plan_service
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.core.exceptions import QuotaExceededError
from app.db.models.profile import Profile

router = APIRouter(prefix="/lesson-plans", tags=["Lesson Plans"])

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_lesson_plan(
    payload: LessonPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    try:
        job_id = await lesson_plan_service.trigger_generation(db, current_user.id, payload)
        await db.commit()
        return {"job_id": job_id}
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

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    from app.tasks.celery_app import celery_app
    from celery.result import AsyncResult
    
    result = AsyncResult(job_id, app=celery_app)
    
    state = result.state.lower()
    if state == "success":
        state = "completed"
        
    return JobStatusResponse(job_id=job_id, status=state)
