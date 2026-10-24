from typing import Sequence
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.profile import Profile
from app.db.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[Profile, dict, dict]):
    def __init__(self):
        super().__init__(Profile)

    async def get_by_email(self, db: AsyncSession, email: str) -> Profile | None:
        """Looks up a profile by its (already normalized) email address."""
        result = await db.execute(select(self.model).filter(self.model.email == email))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, db: AsyncSession, id: str) -> Profile | None:
        """
        Fetches a profile and explicitly locks the row using SELECT ... FOR UPDATE.
        Use when a read-modify-write on the profile must not interleave with another request.
        """
        result = await db.execute(
            select(self.model).filter(self.model.id == id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_filtered(
        self, db: AsyncSession, skip: int = 0, limit: int = 20, query: str | None = None, role: str | None = None
    ) -> tuple[Sequence[Profile], int]:
        """
        One page of accounts, newest first, with the total that matches. `query` matches part of the
        name or email, ignoring case; `role` is an exact match.
        """
        conditions = []
        if query:
            escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            conditions.append(or_(
                self.model.email.ilike(pattern, escape="\\"),
                self.model.full_name.ilike(pattern, escape="\\"),
            ))
        if role:
            conditions.append(self.model.role == role)

        total = (await db.execute(select(func.count()).select_from(self.model).where(*conditions))).scalar_one()
        result = await db.execute(
            select(self.model).where(*conditions).order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    async def lock_active_admin_ids(self, db: AsyncSession) -> list[UUID]:
        """
        Ids of the administrators who can still sign in, locked until the transaction ends so two
        requests cannot each remove "the other" admin. (FOR UPDATE cannot be combined with count.)
        """
        result = await db.execute(
            select(self.model.id)
            .where(self.model.role == "admin", self.model.disabled_at.is_(None))
            .with_for_update()
        )
        return list(result.scalars().all())

user_repo = UserRepository()
