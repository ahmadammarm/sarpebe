import time
import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from jose import jwt
from unittest.mock import AsyncMock

from app.config import settings
from app.core import security
from app.core.exceptions import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidEmailTokenError,
    InvalidRefreshTokenError,
    TooManyAttemptsError,
)
from app.db.models.profile import Profile
from app.schemas.auth import AuthUser, TokenResponse

pytestmark = pytest.mark.asyncio(loop_scope="session")

SERVICE = "app.api.routers.auth.auth_service"
EMAIL_SERVICE = "app.api.routers.auth.email_service"


def make_profile(**overrides):
    values = dict(id=uuid.uuid4(), email="guru@example.com", full_name="Bu Guru", role="user")
    values.update(overrides)
    return Profile(**values)


def token_response(user: Profile) -> TokenResponse:
    return TokenResponse(
        access_token="access", refresh_token="refresh", expires_in=900, user=AuthUser.model_validate(user)
    )


# --- register ---------------------------------------------------------------------------

async def test_register_sends_verification_email(async_client: AsyncClient, mocker):
    user = make_profile()
    mocker.patch(f"{SERVICE}.register", new_callable=AsyncMock, return_value=(user, "raw-token"))
    send = mocker.patch(f"{EMAIL_SERVICE}.send_verification_email", new_callable=AsyncMock)

    response = await async_client.post(
        "/api/auth/register",
        json={"email": "guru@example.com", "password": "long-enough-pw", "full_name": "Bu Guru"},
    )

    assert response.status_code == 202
    send.assert_awaited_once_with("guru@example.com", "Bu Guru", "raw-token")


async def test_register_existing_email_looks_identical_and_sends_nothing(async_client: AsyncClient, mocker):
    fresh = mocker.patch(f"{SERVICE}.register", new_callable=AsyncMock, return_value=(make_profile(), "t"))
    mocker.patch(f"{EMAIL_SERVICE}.send_verification_email", new_callable=AsyncMock)
    body = {"email": "guru@example.com", "password": "long-enough-pw", "full_name": "Bu Guru"}
    new_response = await async_client.post("/api/auth/register", json=body)

    fresh.return_value = None
    send = mocker.patch(f"{EMAIL_SERVICE}.send_verification_email", new_callable=AsyncMock)
    existing_response = await async_client.post("/api/auth/register", json=body)

    assert existing_response.status_code == new_response.status_code == 202
    assert existing_response.json() == new_response.json()
    send.assert_not_called()


@pytest.mark.parametrize("password", ["short", "x" * 80])
async def test_register_validates_password(async_client: AsyncClient, password):
    response = await async_client.post(
        "/api/auth/register",
        json={"email": "guru@example.com", "password": password, "full_name": "Bu Guru"},
    )
    assert response.status_code == 422


async def test_register_rejects_invalid_email(async_client: AsyncClient):
    response = await async_client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "long-enough-pw", "full_name": "Bu Guru"},
    )
    assert response.status_code == 422


# --- login ------------------------------------------------------------------------------

async def test_login_returns_tokens(async_client: AsyncClient, mocker):
    mocker.patch(f"{SERVICE}.login", new_callable=AsyncMock, return_value=token_response(make_profile()))
    response = await async_client.post("/api/auth/login", json={"email": "guru@example.com", "password": "pw"})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "access" and body["refresh_token"] == "refresh"
    assert body["user"]["email"] == "guru@example.com"
    assert "password_hash" not in str(body)


@pytest.mark.parametrize("error,status_code,code", [
    (InvalidCredentialsError("Invalid email or password."), 401, "invalid_credentials"),
    (EmailNotVerifiedError("Email address has not been verified."), 403, "email_not_verified"),
    (TooManyAttemptsError("Too many failed login attempts."), 429, "too_many_attempts"),
])
async def test_login_errors_carry_status_and_code(async_client: AsyncClient, mocker, error, status_code, code):
    mocker.patch(f"{SERVICE}.login", new_callable=AsyncMock, side_effect=error)
    response = await async_client.post("/api/auth/login", json={"email": "guru@example.com", "password": "pw"})
    assert response.status_code == status_code
    assert response.json()["code"] == code


# --- refresh / logout / email flows -----------------------------------------------------

async def test_refresh_invalid_token_is_401(async_client: AsyncClient, mocker):
    mocker.patch(f"{SERVICE}.refresh", new_callable=AsyncMock, side_effect=InvalidRefreshTokenError("Invalid refresh token."))
    response = await async_client.post("/api/auth/refresh", json={"refresh_token": "bad"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["code"] == "invalid_refresh_token"


async def test_logout_returns_204(async_client: AsyncClient, mocker):
    logout = mocker.patch(f"{SERVICE}.logout", new_callable=AsyncMock)
    response = await async_client.post("/api/auth/logout", json={"refresh_token": "token"})
    assert response.status_code == 204
    logout.assert_awaited_once()


async def test_verify_email_invalid_token_is_400(async_client: AsyncClient, mocker):
    mocker.patch(f"{SERVICE}.verify_email", new_callable=AsyncMock, side_effect=InvalidEmailTokenError("invalid"))
    response = await async_client.post("/api/auth/verify-email", json={"token": "bad"})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_email_token"


async def test_forgot_password_answers_the_same_for_unknown_emails(async_client: AsyncClient, mocker):
    forgot = mocker.patch(f"{SERVICE}.forgot_password", new_callable=AsyncMock, return_value=(make_profile(), "t"))
    mocker.patch(f"{EMAIL_SERVICE}.send_password_reset_email", new_callable=AsyncMock)
    known = await async_client.post("/api/auth/forgot-password", json={"email": "guru@example.com"})

    forgot.return_value = None
    send = mocker.patch(f"{EMAIL_SERVICE}.send_password_reset_email", new_callable=AsyncMock)
    unknown = await async_client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    send.assert_not_called()


async def test_reset_password_validates_new_password(async_client: AsyncClient):
    response = await async_client.post("/api/auth/reset-password", json={"token": "t", "password": "short"})
    assert response.status_code == 422


# --- protected endpoints use the backend-issued access token ---------------------------

async def test_protected_endpoint_accepts_valid_access_token(async_client: AsyncClient, mocker):
    user = make_profile(subscription_tier="free", created_at=datetime.now(timezone.utc))
    mocker.patch("app.api.deps.user_repo.get", new_callable=AsyncMock, return_value=user)
    token, _ = security.create_access_token(user.id)

    response = await async_client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "guru@example.com"


async def test_protected_endpoint_rejects_missing_token(async_client: AsyncClient):
    response = await async_client.get("/api/users/me")
    assert response.status_code in (401, 403)


async def test_protected_endpoint_rejects_forged_and_expired_tokens(async_client: AsyncClient, mocker):
    mocker.patch("app.api.deps.user_repo.get", new_callable=AsyncMock, return_value=make_profile())
    base = {"sub": str(uuid.uuid4()), "iss": settings.auth_jwt_issuer, "type": "access"}
    forged = jwt.encode({**base, "exp": int(time.time()) + 600}, "x" * 40, algorithm="HS256")
    expired = jwt.encode({**base, "exp": int(time.time()) - 5}, settings.auth_jwt_secret, algorithm="HS256")

    for token in (forged, expired):
        response = await async_client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.json()["code"] == "invalid_token"


async def test_deleted_user_with_valid_token_is_rejected(async_client: AsyncClient, mocker):
    mocker.patch("app.api.deps.user_repo.get", new_callable=AsyncMock, return_value=None)
    token, _ = security.create_access_token(uuid.uuid4())
    response = await async_client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_old_supabase_token_is_no_longer_accepted(async_client: AsyncClient, mocker):
    mocker.patch("app.api.deps.user_repo.get", new_callable=AsyncMock, return_value=make_profile())
    legacy = jwt.encode(
        {"sub": str(uuid.uuid4()), "aud": "authenticated", "exp": int(time.time()) + 600},
        "some-supabase-jwt-secret", algorithm="HS256",
    )
    response = await async_client.get("/api/users/me", headers={"Authorization": f"Bearer {legacy}"})
    assert response.status_code == 401
