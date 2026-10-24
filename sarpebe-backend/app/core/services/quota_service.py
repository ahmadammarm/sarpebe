from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import QuotaExceededError
from app.db.models.profile import Profile
from app.db.repositories.lesson_plan_repository import lesson_plan_repo
from app.db.repositories.user_repository import user_repo
from app.utils.time import utc_now

QUOTA_WINDOW = timedelta(hours=24)
FREE_TIER = "free"


@dataclass(frozen=True)
class QuotaStatus:
    limit: int | None  # None = unlimited
    used: int
    resets_at: datetime | None  # when the oldest counted plan leaves the window and a slot frees up

    @property
    def unlimited(self) -> bool:
        return self.limit is None

    @property
    def remaining(self) -> int | None:
        return None if self.limit is None else max(0, self.limit - self.used)


class QuotaService:
    @staticmethod
    def limit_for(user: Profile) -> int | None:
        """Plans the user may start per window. Admins, paid tiers, and a configured 0 are unlimited."""
        if user.role == "admin" or user.subscription_tier != FREE_TIER:
            return None
        return settings.generation_daily_limit_free or None

    @staticmethod
    async def get_status(db: AsyncSession, user: Profile) -> QuotaStatus:
        used, oldest = await lesson_plan_repo.usage_since(db, user.id, utc_now() - QUOTA_WINDOW)
        return QuotaStatus(
            limit=QuotaService.limit_for(user),
            used=used,
            resets_at=oldest + QUOTA_WINDOW if oldest else None,
        )

    @staticmethod
    async def ensure_available(db: AsyncSession, user: Profile) -> None:
        """
        Raises QuotaExceededError if the user has no plan left in the window.

        The user's row is locked (SELECT ... FOR UPDATE) until the caller commits, so two requests
        that arrive together cannot both pass the check on the last remaining slot. Users without a
        limit are not locked.
        """
        if QuotaService.limit_for(user) is None:
            return

        locked = await user_repo.get_by_id_for_update(db, user.id)
        status = await QuotaService.get_status(db, locked or user)
        if status.remaining == 0:
            raise QuotaExceededError("Generation limit reached for the current period.")

quota_service = QuotaService()
