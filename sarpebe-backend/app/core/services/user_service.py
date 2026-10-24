import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import rate_limit
from app.core.exceptions import (
    InvalidPasswordError,
    LastAdminError,
    SelfActionError,
    TooManyAttemptsError,
    UserNotFoundError,
)
from app.core.security import hash_password, verify_password
from app.db.models.profile import Profile
from app.db.repositories.auth_token_repository import auth_token_repo
from app.db.repositories.refresh_token_repository import refresh_token_repo
from app.db.repositories.user_repository import user_repo
from app.schemas.user import ProfileUpdate, UserAdminUpdate
from app.utils.time import utc_now

RESET_PASSWORD = "reset_password"  # purpose of the emailed reset links (see auth_service)


def _password_failure_key(user_id: uuid.UUID) -> str:
    return f"auth:password_check_failures:{user_id}"


class UserService:
    # --- the signed-in user ----------------------------------------------------------

    @staticmethod
    async def update_profile(db: AsyncSession, user: Profile, payload: ProfileUpdate) -> Profile:
        changes = payload.model_dump(exclude_unset=True)
        if changes.get("full_name") is None:
            changes.pop("full_name", None)  # the name is required; only school_name may be cleared
        user = await user_repo.update(db, user, changes)
        await db.commit()
        return user

    @staticmethod
    async def _check_password(user: Profile, password: str) -> None:
        """
        Proves the person at the keyboard knows the account password before a sensitive action.
        Wrong guesses are counted and lock the action for a while, like failed logins.
        """
        key = _password_failure_key(user.id)
        if await rate_limit.get_count(key) >= settings.login_max_failed_attempts:
            raise TooManyAttemptsError("Too many wrong passwords. Try again later.")
        if not await verify_password(password, user.password_hash):
            await rate_limit.increment(key, settings.login_lockout_minutes * 60)
            raise InvalidPasswordError("The password is incorrect.")
        await rate_limit.reset(key)

    @staticmethod
    async def change_password(db: AsyncSession, user: Profile, current_password: str, new_password: str) -> None:
        """Sets a new password and signs the user out everywhere, this device included."""
        await UserService._check_password(user, current_password)

        now = utc_now()
        user.password_hash = await hash_password(new_password)
        await auth_token_repo.invalidate_unused(db, user.id, RESET_PASSWORD, now)
        await refresh_token_repo.revoke_all_for_user(db, user.id, now)
        await db.commit()

    @staticmethod
    async def delete_account(db: AsyncSession, user: Profile, password: str) -> None:
        """Deletes the account with its plans, cost logs and sessions (the foreign keys cascade)."""
        await UserService._check_password(user, password)

        if user.role == "admin":
            admins = await user_repo.lock_active_admin_ids(db)
            if admins == [user.id]:
                raise LastAdminError("The only administrator cannot delete their own account.")

        await user_repo.delete(db, user.id)
        await db.commit()

    # --- administrators --------------------------------------------------------------

    @staticmethod
    async def list_users(
        db: AsyncSession, skip: int, limit: int, query: str | None, role: str | None
    ) -> tuple[Sequence[Profile], int]:
        return await user_repo.list_filtered(db, skip, limit, query=query.strip() if query else None, role=role)

    @staticmethod
    async def admin_update(
        db: AsyncSession, actor: Profile, user_id: uuid.UUID, payload: UserAdminUpdate
    ) -> Profile:
        """
        Changes another account's role, tier or status. Nobody can change their own role or status,
        and the last active administrator can never be demoted or disabled.
        """
        target = await user_repo.get_by_id_for_update(db, user_id)
        if not target:
            raise UserNotFoundError("User not found.")

        wants_role = payload.role is not None and payload.role != target.role
        wants_status = payload.disabled is not None and payload.disabled != (target.disabled_at is not None)
        if target.id == actor.id and (wants_role or wants_status):
            raise SelfActionError("You cannot change your own role or status.")

        removes_an_admin = target.role == "admin" and target.disabled_at is None and (
            (wants_role and payload.role != "admin") or (wants_status and payload.disabled)
        )
        if removes_an_admin and await user_repo.lock_active_admin_ids(db) == [target.id]:
            raise LastAdminError("The only active administrator cannot be demoted or disabled.")

        now = utc_now()
        if wants_role:
            target.role = payload.role
        if payload.subscription_tier is not None:
            target.subscription_tier = payload.subscription_tier
        if wants_status:
            target.disabled_at = now if payload.disabled else None
            if payload.disabled:
                await refresh_token_repo.revoke_all_for_user(db, target.id, now)

        await db.commit()
        return target

    @staticmethod
    async def admin_delete(db: AsyncSession, actor: Profile, user_id: uuid.UUID) -> None:
        if user_id == actor.id:
            raise SelfActionError("You cannot delete your own account here; use your profile page.")
        target = await user_repo.get(db, user_id)
        if not target:
            raise UserNotFoundError("User not found.")

        await user_repo.delete(db, target.id)
        await db.commit()

user_service = UserService()
