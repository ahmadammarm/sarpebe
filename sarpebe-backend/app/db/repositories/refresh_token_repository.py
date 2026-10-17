from datetime import datetime
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.refresh_token import RefreshToken
from app.db.repositories.base_repository import BaseRepository

class RefreshTokenRepository(BaseRepository[RefreshToken, dict, dict]):
    def __init__(self):
        super().__init__(RefreshToken)

    async def get_by_hash_for_update(self, db: AsyncSession, token_hash: str) -> RefreshToken | None:
        """
        Locks the token row so two concurrent refreshes with the same token are serialized
        rather than both passing the "not yet revoked" check.
        """
        result = await db.execute(
            select(self.model).filter(self.model.token_hash == token_hash).with_for_update()
        )
        return result.scalar_one_or_none()

    async def revoke_family(self, db: AsyncSession, family_id: UUID, now: datetime) -> None:
        await db.execute(
            update(self.model)
            .where(self.model.family_id == family_id, self.model.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    async def revoke_all_for_user(self, db: AsyncSession, user_id: UUID, now: datetime) -> None:
        await db.execute(
            update(self.model)
            .where(self.model.user_id == user_id, self.model.revoked_at.is_(None))
            .values(revoked_at=now)
        )

refresh_token_repo = RefreshTokenRepository()
