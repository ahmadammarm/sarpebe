import uuid
from datetime import timedelta

import bcrypt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core import rate_limit, security
from app.core.exceptions import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidEmailTokenError,
    InvalidRefreshTokenError,
    TooManyAttemptsError,
)
from app.core.security import decode_access_token, hash_token
from app.core.services.auth_service import RESET_PASSWORD, VERIFY_EMAIL, auth_service
from app.db.base import Base
from app.db.models import AuthToken, Profile, RefreshToken
from app.utils.time import utc_now

pytestmark = pytest.mark.asyncio(loop_scope="session")

PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def fast_hashing(monkeypatch):
    monkeypatch.setattr(security, "BCRYPT_ROUNDS", 4)


@pytest.fixture(autouse=True)
def fake_rate_limit(monkeypatch):
    counters: dict[str, int] = {}

    async def get_count(key):
        return counters.get(key, 0)

    async def increment(key, window_seconds):
        counters[key] = counters.get(key, 0) + 1
        return counters[key]

    async def reset(key):
        counters.pop(key, None)

    monkeypatch.setattr(rate_limit, "get_count", get_count)
    monkeypatch.setattr(rate_limit, "increment", increment)
    monkeypatch.setattr(rate_limit, "reset", reset)
    return counters


@pytest.fixture
async def db():
    """A real SQLAlchemy session over in-memory SQLite with the authentication tables."""
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[Profile.__table__, RefreshToken.__table__, AuthToken.__table__],
        )
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def make_user(db, email="guru@example.com", verified=True, password=PASSWORD, password_hash=None):
    user = Profile(
        id=uuid.uuid4(),
        email=email,
        password_hash=password_hash or await security.hash_password(password),
        full_name="Bu Guru",
        role="user",
        email_verified_at=utc_now() if verified else None,
    )
    db.add(user)
    await db.commit()
    return user


async def all_rows(db, model):
    return list((await db.execute(select(model))).scalars().all())


# --- registration and verification --------------------------------------------------------

async def test_register_creates_unverified_user_and_token(db):
    user, token = await auth_service.register(db, " Guru@Example.com ", PASSWORD, "Bu Guru")

    assert user.email == "guru@example.com"
    assert user.password_hash and PASSWORD not in user.password_hash
    assert user.email_verified_at is None
    assert user.role == "user"
    stored = (await all_rows(db, AuthToken))[0]
    assert stored.token_hash == hash_token(token)  # only the hash is stored
    assert stored.purpose == VERIFY_EMAIL


async def test_register_duplicate_email_returns_none(db):
    await make_user(db)
    assert await auth_service.register(db, "GURU@example.com", PASSWORD, "Someone Else") is None
    assert len(await all_rows(db, Profile)) == 1


async def test_register_without_verification_requirement(db, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    user, token = await auth_service.register(db, "a@example.com", PASSWORD, "Bu Guru")
    assert token is None
    assert user.email_verified_at is not None


async def test_verify_email_marks_user_verified(db):
    user, token = await auth_service.register(db, "a@example.com", PASSWORD, "Bu Guru")
    await auth_service.verify_email(db, token)
    await db.refresh(user)
    assert user.email_verified_at is not None


async def test_verify_email_link_can_be_opened_twice(db):
    _, token = await auth_service.register(db, "a@example.com", PASSWORD, "Bu Guru")
    await auth_service.verify_email(db, token)
    await auth_service.verify_email(db, token)  # must not raise


async def test_verify_email_rejects_unknown_and_expired_tokens(db):
    user, token = await auth_service.register(db, "a@example.com", PASSWORD, "Bu Guru")
    with pytest.raises(InvalidEmailTokenError):
        await auth_service.verify_email(db, "not-a-real-token")

    stored = (await all_rows(db, AuthToken))[0]
    stored.expires_at = utc_now() - timedelta(minutes=1)
    await db.commit()
    with pytest.raises(InvalidEmailTokenError):
        await auth_service.verify_email(db, token)


async def test_resend_verification_only_for_unverified_accounts(db):
    await make_user(db, email="verified@example.com", verified=True)
    unverified = await make_user(db, email="new@example.com", verified=False)

    assert await auth_service.resend_verification(db, "verified@example.com") is None
    assert await auth_service.resend_verification(db, "missing@example.com") is None
    user, token = await auth_service.resend_verification(db, "new@example.com")
    assert user.id == unverified.id and token


async def test_resend_verification_invalidates_previous_link(db):
    user, first = await auth_service.register(db, "a@example.com", PASSWORD, "Bu Guru")
    _, second = await auth_service.resend_verification(db, "a@example.com")

    with pytest.raises(InvalidEmailTokenError):
        await auth_service.verify_email(db, first)
    await auth_service.verify_email(db, second)


async def test_email_actions_are_rate_limited(db):
    await make_user(db, email="new@example.com", verified=False)
    results = [await auth_service.resend_verification(db, "new@example.com") for _ in range(5)]
    assert [r is not None for r in results] == [True, True, True, False, False]


# --- login ----------------------------------------------------------------------------------

async def test_login_success_returns_working_tokens(db):
    user = await make_user(db)
    tokens = await auth_service.login(db, "GURU@example.com", PASSWORD)

    assert decode_access_token(tokens.access_token)["sub"] == str(user.id)
    assert tokens.user.email == "guru@example.com" and tokens.user.role == "user"
    assert tokens.expires_in == settings.access_token_ttl_minutes * 60
    stored = (await all_rows(db, RefreshToken))[0]
    assert stored.token_hash == hash_token(tokens.refresh_token)
    assert tokens.refresh_token not in stored.token_hash


async def test_login_wrong_password_and_unknown_email_look_the_same(db):
    await make_user(db)
    with pytest.raises(InvalidCredentialsError) as wrong:
        await auth_service.login(db, "guru@example.com", "wrong-password")
    with pytest.raises(InvalidCredentialsError) as unknown:
        await auth_service.login(db, "nobody@example.com", PASSWORD)
    assert str(wrong.value) == str(unknown.value)


async def test_login_requires_verified_email_but_only_after_password_check(db):
    await make_user(db, verified=False)
    with pytest.raises(EmailNotVerifiedError):
        await auth_service.login(db, "guru@example.com", PASSWORD)
    # A wrong password must not reveal that the account is unverified.
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(db, "guru@example.com", "wrong-password")


async def test_login_allows_unverified_when_verification_disabled(db, monkeypatch):
    monkeypatch.setattr(settings, "require_email_verification", False)
    await make_user(db, verified=False)
    assert (await auth_service.login(db, "guru@example.com", PASSWORD)).access_token


async def test_login_locks_out_after_repeated_failures(db):
    await make_user(db)
    for _ in range(settings.login_max_failed_attempts):
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(db, "guru@example.com", "wrong-password")

    with pytest.raises(TooManyAttemptsError):
        await auth_service.login(db, "guru@example.com", PASSWORD)  # even the right one


async def test_successful_login_clears_failure_counter(db, fake_rate_limit):
    await make_user(db)
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(db, "guru@example.com", "wrong-password")
    assert fake_rate_limit
    await auth_service.login(db, "guru@example.com", PASSWORD)
    assert not fake_rate_limit


async def test_imported_supabase_account_can_log_in(db):
    legacy_hash = bcrypt.hashpw(b"old-supabase-pw", bcrypt.gensalt(rounds=4)).decode().replace("$2b$", "$2a$", 1)
    await make_user(db, password_hash=legacy_hash)
    assert (await auth_service.login(db, "guru@example.com", "old-supabase-pw")).access_token


async def test_account_without_password_cannot_log_in(db):
    user = await make_user(db)
    user.password_hash = None
    await db.commit()
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(db, "guru@example.com", PASSWORD)


# --- refresh rotation ---------------------------------------------------------------------

async def test_refresh_rotates_tokens(db):
    await make_user(db)
    first = await auth_service.login(db, "guru@example.com", PASSWORD)
    second = await auth_service.refresh(db, first.refresh_token)

    assert second.refresh_token != first.refresh_token
    rows = {r.token_hash: r for r in await all_rows(db, RefreshToken)}
    old, new = rows[hash_token(first.refresh_token)], rows[hash_token(second.refresh_token)]
    assert old.revoked_at is not None and old.rotated
    assert new.revoked_at is None
    assert old.family_id == new.family_id


async def test_refresh_rejects_unknown_and_expired_tokens(db):
    await make_user(db)
    with pytest.raises(InvalidRefreshTokenError):
        await auth_service.refresh(db, "unknown-token")

    tokens = await auth_service.login(db, "guru@example.com", PASSWORD)
    row = (await all_rows(db, RefreshToken))[0]
    row.expires_at = utc_now() - timedelta(seconds=1)
    await db.commit()
    with pytest.raises(InvalidRefreshTokenError):
        await auth_service.refresh(db, tokens.refresh_token)


async def test_replayed_old_refresh_token_revokes_the_whole_session(db):
    await make_user(db)
    first = await auth_service.login(db, "guru@example.com", PASSWORD)
    second = await auth_service.refresh(db, first.refresh_token)

    # Pretend the rotation happened long ago, so the replay is not a concurrent refresh.
    old = next(r for r in await all_rows(db, RefreshToken) if r.token_hash == hash_token(first.refresh_token))
    old.revoked_at = utc_now() - timedelta(hours=1)
    await db.commit()

    with pytest.raises(InvalidRefreshTokenError):
        await auth_service.refresh(db, first.refresh_token)
    # The legitimate newer token is dead too: the thief and the owner are both signed out.
    with pytest.raises(InvalidRefreshTokenError):
        await auth_service.refresh(db, second.refresh_token)


async def test_concurrent_refresh_within_grace_window_is_tolerated(db):
    await make_user(db)
    first = await auth_service.login(db, "guru@example.com", PASSWORD)
    second = await auth_service.refresh(db, first.refresh_token)
    third = await auth_service.refresh(db, first.refresh_token)  # same token, moments later

    assert third.refresh_token not in (first.refresh_token, second.refresh_token)
    # Both successors stay valid, whichever one the client ends up keeping.
    assert (await auth_service.refresh(db, second.refresh_token)).access_token
    assert (await auth_service.refresh(db, third.refresh_token)).access_token


async def test_logout_revokes_the_session(db):
    await make_user(db)
    first = await auth_service.login(db, "guru@example.com", PASSWORD)
    latest = await auth_service.refresh(db, first.refresh_token)

    await auth_service.logout(db, latest.refresh_token)
    assert all(r.revoked_at is not None for r in await all_rows(db, RefreshToken))
    with pytest.raises(InvalidRefreshTokenError):
        await auth_service.refresh(db, latest.refresh_token)


async def test_logout_with_unknown_token_is_a_noop(db):
    await auth_service.logout(db, "unknown-token")


async def test_logout_does_not_affect_other_sessions(db):
    await make_user(db)
    laptop = await auth_service.login(db, "guru@example.com", PASSWORD)
    phone = await auth_service.login(db, "guru@example.com", PASSWORD)

    await auth_service.logout(db, laptop.refresh_token)
    assert (await auth_service.refresh(db, phone.refresh_token)).access_token


# --- password reset -----------------------------------------------------------------------

async def test_forgot_password_unknown_email_returns_none(db):
    assert await auth_service.forgot_password(db, "nobody@example.com") is None


async def test_reset_password_changes_password_and_signs_out_everywhere(db):
    await make_user(db)
    session = await auth_service.login(db, "guru@example.com", PASSWORD)
    _, token = await auth_service.forgot_password(db, "guru@example.com")

    await auth_service.reset_password(db, token, "a-brand-new-password")

    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(db, "guru@example.com", PASSWORD)
    assert (await auth_service.login(db, "guru@example.com", "a-brand-new-password")).access_token
    with pytest.raises(InvalidRefreshTokenError):
        await auth_service.refresh(db, session.refresh_token)


async def test_reset_token_is_single_use(db):
    await make_user(db)
    _, token = await auth_service.forgot_password(db, "guru@example.com")
    await auth_service.reset_password(db, token, "a-brand-new-password")
    with pytest.raises(InvalidEmailTokenError):
        await auth_service.reset_password(db, token, "another-password-1")


async def test_reset_token_expires(db):
    await make_user(db)
    _, token = await auth_service.forgot_password(db, "guru@example.com")
    row = next(t for t in await all_rows(db, AuthToken) if t.purpose == RESET_PASSWORD)
    row.expires_at = utc_now() - timedelta(minutes=1)
    await db.commit()
    with pytest.raises(InvalidEmailTokenError):
        await auth_service.reset_password(db, token, "a-brand-new-password")


async def test_verification_token_cannot_reset_a_password(db):
    _, verify_token = await auth_service.register(db, "a@example.com", PASSWORD, "Bu Guru")
    with pytest.raises(InvalidEmailTokenError):
        await auth_service.reset_password(db, verify_token, "a-brand-new-password")


async def test_reset_marks_unverified_email_as_verified(db):
    user = await make_user(db, verified=False)
    _, token = await auth_service.forgot_password(db, "guru@example.com")
    await auth_service.reset_password(db, token, "a-brand-new-password")
    await db.refresh(user)
    assert user.email_verified_at is not None


async def test_newer_reset_link_invalidates_older_one(db):
    await make_user(db)
    _, first = await auth_service.forgot_password(db, "guru@example.com")
    _, second = await auth_service.forgot_password(db, "guru@example.com")
    with pytest.raises(InvalidEmailTokenError):
        await auth_service.reset_password(db, first, "a-brand-new-password")
    await auth_service.reset_password(db, second, "a-brand-new-password")
