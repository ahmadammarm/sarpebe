from fastapi import APIRouter, Depends
from app.schemas.user import ProfileResponse
from app.api.deps import get_current_user
from app.db.models.profile import Profile

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=ProfileResponse)
async def get_me(current_user: Profile = Depends(get_current_user)):
    return current_user
