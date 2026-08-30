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
        raise HTTPException(status_code=404, detail="User profile not found")
        
    return user
