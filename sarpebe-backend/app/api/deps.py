from typing import AsyncGenerator
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.security import verify_supabase_token
from app.db.repositories.user_repository import user_repo
from app.db.models.profile import Profile

security = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yields a database session."""
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Profile:
    """
    Validates the Supabase JWT and fetches the user profile from the database.
    """
    payload = verify_supabase_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")

    user = await user_repo.get(db, user_id)
    if not user:
        # Auto-create profile if missing (e.g. Supabase DB trigger not installed)
        email = payload.get("email") or "user@sarpebe.com"
        name = payload.get("user_metadata", {}).get("full_name") or email.split("@")[0]
        user = await user_repo.create(db, {
            "id": user_id,
            "full_name": name,
            "school_name": None,
            "role": "user",
            "subscription_tier": "free"
        })
        await db.commit()
        await db.refresh(user)

    return user

async def require_admin(
    current_user: Profile = Depends(get_current_user)
) -> Profile:
    """
    Ensures the current authenticated user has the 'admin' role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
