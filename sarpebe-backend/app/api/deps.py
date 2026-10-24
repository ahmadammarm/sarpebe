from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.exceptions import AccountDisabledError, ForbiddenError, InvalidAccessTokenError
from app.core.security import decode_access_token
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
    Validates the access token issued by this backend and loads the user profile.
    """
    payload = decode_access_token(credentials.credentials)

    user = await user_repo.get(db, payload["sub"])
    if not user:
        # The account was deleted after the token was issued.
        raise InvalidAccessTokenError("Could not validate credentials")
    if user.disabled_at is not None:
        raise AccountDisabledError("This account has been disabled.")

    return user

async def require_admin(
    current_user: Profile = Depends(get_current_user)
) -> Profile:
    """
    Ensures the current authenticated user has the 'admin' role.
    """
    if current_user.role != "admin":
        raise ForbiddenError("Admin privileges required")
    return current_user
