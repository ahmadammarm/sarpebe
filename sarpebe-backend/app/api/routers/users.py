from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import ProfileResponse, CostSummaryResponse, UserCostSummaryResponse
from app.api.deps import get_current_user, require_admin, get_db
from app.db.models.profile import Profile
from app.db.repositories.llm_cost_log_repository import llm_cost_log_repo

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=ProfileResponse)
async def get_me(current_user: Profile = Depends(get_current_user)):
    return current_user

@router.get("/me/costs", response_model=CostSummaryResponse)
async def get_my_costs(
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated token usage and fiat cost for the authenticated user."""
    costs = await llm_cost_log_repo.get_user_aggregated_costs(db, current_user.id)
    return costs

@router.get("/costs", response_model=list[UserCostSummaryResponse])
async def get_all_users_costs(
    current_admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only: Get aggregated token usage and fiat cost across all users."""
    costs = await llm_cost_log_repo.get_all_users_aggregated_costs(db)
    return costs
