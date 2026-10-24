import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.common import PaginatedResponse
from app.schemas.user import (
    AdminUserResponse,
    ChangePasswordRequest,
    CostSummaryResponse,
    DeleteAccountRequest,
    ProfileResponse,
    ProfileUpdate,
    QuotaResponse,
    UserAdminUpdate,
    UserCostSummaryResponse,
    UserRole,
)
from app.api.deps import get_current_user, require_admin, get_db
from app.core.services.quota_service import quota_service
from app.core.services.user_service import user_service
from app.db.models.profile import Profile
from app.db.repositories.llm_cost_log_repository import llm_cost_log_repo

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=ProfileResponse)
async def get_me(current_user: Profile = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=ProfileResponse)
async def update_me(
    payload: ProfileUpdate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.update_profile(db, current_user, payload)

@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    payload: ChangePasswordRequest,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Needs the current password. Signs the user out of every device, so the client must sign in again."""
    await user_service.change_password(db, current_user, payload.current_password, payload.new_password)
    return None

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    payload: DeleteAccountRequest,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Needs the password. Deletes the account together with its lesson plans and cost logs."""
    await user_service.delete_account(db, current_user, payload.password)
    return None

@router.get("/me/quota", response_model=QuotaResponse)
async def get_my_quota(
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """How many lesson plans the authenticated user can still start in the current 24 hours."""
    quota = await quota_service.get_status(db, current_user)
    return QuotaResponse(
        limit=quota.limit,
        used=quota.used,
        remaining=quota.remaining,
        unlimited=quota.unlimited,
        resets_at=quota.resets_at,
    )

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

@router.get("", response_model=PaginatedResponse[AdminUserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, max_length=100),
    role: UserRole | None = None,
    current_admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only: accounts, newest first. `q` matches part of the name or email."""
    items, total = await user_service.list_users(db, skip, limit, q, role)
    return PaginatedResponse(items=list(items), total=total, skip=skip, limit=limit)

@router.patch("/{id}", response_model=AdminUserResponse)
async def update_user(
    id: uuid.UUID,
    payload: UserAdminUpdate,
    current_admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only: change another account's role, tier or status (disabled)."""
    return await user_service.admin_update(db, current_admin, id, payload)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    id: uuid.UUID,
    current_admin: Profile = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin-only: delete another account with its lesson plans and cost logs."""
    await user_service.admin_delete(db, current_admin, id)
    return None
