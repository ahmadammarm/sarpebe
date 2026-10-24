import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import rate_limit
from app.core.exceptions import (
    AccountDisabledError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidEmailTokenError,
    InvalidRefreshTokenError,
    TooManyAttemptsError,
)
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    normalize_email,
    verify_password,
)
from app.db.models.profile import Profile
from app.db.repositories.auth_token_repository import auth_token_repo
from app.db.repositories.refresh_token_repository import refresh_token_repo
from app.db.repositories.user_repository import user_repo
from app.schemas.auth import AuthUser, TokenResponse
from app.utils.time import utc_now

VERIFY_EMAIL = "verify_email"
RESET_PASSWORD = "reset_password"

EMAIL_ACTIONS_PER_HOUR = 3


def _aware(value: datetime) -> datetime:
    """Some drivers return naive datetimes for timestamptz columns; they are always UTC."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _login_failure_key(email: str) -> str:
    return f"auth:login_failures:{email}"


def _email_action_key(purpose: str, email: str) -> str:
    return f"auth:{purpose}:{email}"


class AuthService:
    # --- helpers ---------------------------------------------------------------------

    @staticmethod
    async def _issue_tokens(db: AsyncSession, user: Profile, family_id: uuid.UUID | None = None) -> TokenResponse:
        """Creates an access token and a new refresh token. The caller commits."""
        access_token, expires_in = create_access_token(user.id)
        raw_refresh = generate_opaque_token()
        await refresh_token_repo.create(db, {
            "user_id": user.id,
            "family_id": family_id or uuid.uuid4(),
            "token_hash": hash_token(raw_refresh),
            "expires_at": utc_now() + timedelta(days=settings.refresh_token_ttl_days),
        })
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=expires_in,
            user=AuthUser.model_validate(user),
        )

    @staticmethod
    async def _issue_email_token(db: AsyncSession, user: Profile, purpose: str, ttl: timedelta) -> str:
        """Creates a one-time emailed token, invalidating older unused ones. The caller commits."""
        now = utc_now()
        await auth_token_repo.invalidate_unused(db, user.id, purpose, now)
        raw = generate_opaque_token()
        await auth_token_repo.create(db, {
            "user_id": user.id,
            "purpose": purpose,
            "token_hash": hash_token(raw),
            "expires_at": now + ttl,
        })
        return raw

    @staticmethod
    async def _email_action_allowed(purpose: str, email: str) -> bool:
        count = await rate_limit.increment(_email_action_key(purpose, email), 3600)
        return count <= EMAIL_ACTIONS_PER_HOUR

    # --- registration and email verification -------------------------------------------

    @staticmethod
    async def register(db: AsyncSession, email: str, password: str, full_name: str) -> tuple[Profile, str | None] | None:
        """
        Creates an account. Returns (user, verification_token), or None if the email is already
        registered (the API answers identically in both cases so emails cannot be enumerated).
        verification_token is None when email verification is disabled.
        """
        email = normalize_email(email)
        # Hash first so the "already registered" path costs the same time as a new account.
        password_hash = await hash_password(password)

        if await user_repo.get_by_email(db, email):
            return None

        try:
            user = await user_repo.create(db, {
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": "user",
                "subscription_tier": "free",
                "email_verified_at": None if settings.require_email_verification else utc_now(),
            })
            token = None
            if settings.require_email_verification:
                token = await AuthService._issue_email_token(
                    db, user, VERIFY_EMAIL, timedelta(hours=settings.verification_token_ttl_hours)
                )
            await db.commit()
        except IntegrityError:
            # A concurrent request registered the same email between our check and insert.
            await db.rollback()
            return None
        return user, token

    @staticmethod
    async def verify_email(db: AsyncSession, raw_token: str) -> None:
        now = utc_now()
        token = await auth_token_repo.get_by_hash_for_update(db, hash_token(raw_token), VERIFY_EMAIL)
        if not token or _aware(token.expires_at) <= now:
            raise InvalidEmailTokenError("This verification link is invalid or has expired.")

        user = await user_repo.get(db, token.user_id)
        if not user:
            raise InvalidEmailTokenError("This verification link is invalid or has expired.")

        if token.used_at is not None:
            # Opening the same link twice (or a double-fired request) must not look like a failure.
            if user.email_verified_at is not None:
                return
            raise InvalidEmailTokenError("This verification link is invalid or has expired.")

        token.used_at = now
        if user.email_verified_at is None:
            user.email_verified_at = now
        await db.commit()

    @staticmethod
    async def resend_verification(db: AsyncSession, email: str) -> tuple[Profile, str] | None:
        """Returns (user, token) when a new link should be emailed, otherwise None."""
        email = normalize_email(email)
        user = await user_repo.get_by_email(db, email)
        if not user or user.email_verified_at is not None:
            return None
        if not await AuthService._email_action_allowed(VERIFY_EMAIL, email):
            return None

        token = await AuthService._issue_email_token(
            db, user, VERIFY_EMAIL, timedelta(hours=settings.verification_token_ttl_hours)
        )
        await db.commit()
        return user, token

    # --- login, refresh, logout ------------------------------------------------------

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
        email = normalize_email(email)
        failure_key = _login_failure_key(email)

        if await rate_limit.get_count(failure_key) >= settings.login_max_failed_attempts:
            raise TooManyAttemptsError("Too many failed login attempts. Try again later.")

        user = await user_repo.get_by_email(db, email)
        password_ok = await verify_password(password, user.password_hash if user else None)
        if not user or not password_ok:
            await rate_limit.increment(failure_key, settings.login_lockout_minutes * 60)
            raise InvalidCredentialsError("Invalid email or password.")

        # Account status is only revealed to someone who proved they know the password.
        if user.disabled_at is not None:
            raise AccountDisabledError("This account has been disabled.")
        if settings.require_email_verification and user.email_verified_at is None:
            raise EmailNotVerifiedError("Email address has not been verified.")

        await rate_limit.reset(failure_key)
        tokens = await AuthService._issue_tokens(db, user)
        await db.commit()
        return tokens

    @staticmethod
    async def refresh(db: AsyncSession, raw_refresh_token: str) -> TokenResponse:
        """
        Exchanges a refresh token for a new access/refresh pair (rotation). Replaying a token that
        was rotated long ago revokes the whole login session, since it implies the token leaked.
        A replay within the grace window is accepted: it is two requests refreshing at once.
        """
        now = utc_now()
        token = await refresh_token_repo.get_by_hash_for_update(db, hash_token(raw_refresh_token))
        if not token:
            raise InvalidRefreshTokenError("Invalid refresh token.")

        if token.revoked_at is not None:
            within_grace = token.rotated and now - _aware(token.revoked_at) <= timedelta(
                seconds=settings.refresh_reuse_grace_seconds
            )
            if not within_grace:
                await refresh_token_repo.revoke_family(db, token.family_id, now)
                await db.commit()  # persist the revocation before rejecting
                raise InvalidRefreshTokenError("Invalid refresh token.")
        elif _aware(token.expires_at) <= now:
            raise InvalidRefreshTokenError("Refresh token has expired.")
        else:
            token.revoked_at = now
            token.rotated = True

        user = await user_repo.get(db, token.user_id)
        if not user:
            raise InvalidRefreshTokenError("Invalid refresh token.")
        if user.disabled_at is not None:
            # A session that outlived the account being disabled must not renew itself.
            await refresh_token_repo.revoke_family(db, token.family_id, now)
            await db.commit()
            raise AccountDisabledError("This account has been disabled.")

        tokens = await AuthService._issue_tokens(db, user, family_id=token.family_id)
        await db.commit()
        return tokens

    @staticmethod
    async def logout(db: AsyncSession, raw_refresh_token: str) -> None:
        """Revokes the login session the token belongs to. Unknown tokens are ignored."""
        token = await refresh_token_repo.get_by_hash_for_update(db, hash_token(raw_refresh_token))
        if token and token.revoked_at is None:
            await refresh_token_repo.revoke_family(db, token.family_id, utc_now())
            await db.commit()

    # --- password reset --------------------------------------------------------------

    @staticmethod
    async def forgot_password(db: AsyncSession, email: str) -> tuple[Profile, str] | None:
        """Returns (user, token) when a reset link should be emailed, otherwise None."""
        email = normalize_email(email)
        user = await user_repo.get_by_email(db, email)
        if not user:
            return None
        if not await AuthService._email_action_allowed(RESET_PASSWORD, email):
            return None

        token = await AuthService._issue_email_token(
            db, user, RESET_PASSWORD, timedelta(minutes=settings.reset_token_ttl_minutes)
        )
        await db.commit()
        return user, token

    @staticmethod
    async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> None:
        now = utc_now()
        token = await auth_token_repo.get_by_hash_for_update(db, hash_token(raw_token), RESET_PASSWORD)
        if not token or token.used_at is not None or _aware(token.expires_at) <= now:
            raise InvalidEmailTokenError("This reset link is invalid or has expired.")

        user = await user_repo.get(db, token.user_id)
        if not user or not user.email:
            raise InvalidEmailTokenError("This reset link is invalid or has expired.")

        user.password_hash = await hash_password(new_password)
        # Following the emailed link proves ownership of the address.
        if user.email_verified_at is None:
            user.email_verified_at = now
        token.used_at = now
        await auth_token_repo.invalidate_unused(db, user.id, RESET_PASSWORD, now)
        # Anyone holding an old session (possibly the reason for the reset) is signed out.
        await refresh_token_repo.revoke_all_for_user(db, user.id, now)
        await db.commit()
        await rate_limit.reset(_login_failure_key(user.email))

auth_service = AuthService()
