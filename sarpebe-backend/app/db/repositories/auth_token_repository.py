from datetime import datetime
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.auth_token import AuthToken
from app.db.repositories.base_repository import BaseRepository

class AuthTokenRepository(BaseRepository[AuthToken, dict, dict]):
    def __init__(self):
        super().__init__(AuthToken)

    async def get_by_hash_for_update(self, db: AsyncSession, token_hash: str, purpose: str) -> AuthToken | None:
        """Locks the row so a token cannot be redeemed twice by concurrent requests."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.token_hash == token_hash, self.model.purpose == purpose)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def invalidate_unused(self, db: AsyncSession, user_id: UUID, purpose: str, now: datetime) -> None:
        """Marks earlier unused tokens of this purpose as used, so only the newest link works."""
        await db.execute(
            update(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.purpose == purpose,
                self.model.used_at.is_(None),
            )
            .values(used_at=now)
        )

auth_token_repo = AuthTokenRepository()
