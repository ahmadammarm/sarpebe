import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.api.deps import require_admin
from app.core import security
from app.core.exceptions import (
    InvalidPasswordError,
    LastAdminError,
    SelfActionError,
    TooManyAttemptsError,
    UserNotFoundError,
)
from app.db.models.profile import Profile

pytestmark = pytest.mark.asyncio(loop_scope="session")

SERVICE = "app.api.routers.users.user_service"


@pytest.fixture
def admin(mock_user):
    from app.main import app

    mock_user.role = "admin"

    async def _require_admin():
        return mock_user

    app.dependency_overrides[require_admin] = _require_admin
    yield mock_user
    app.dependency_overrides.pop(require_admin, None)


def make_account(**overrides) -> Profile:
    values = dict(
        id=uuid.uuid4(), email="guru@example.com", full_name="Bu Guru", school_name=None, subscription_tier="free",
        role="user", created_at=datetime.now(timezone.utc), email_verified_at=None, disabled_at=None,
    )
    values.update(overrides)
    return Profile(**values)


# --- own profile -----------------------------------------------------------------------------------------------

async def test_the_name_and_school_are_updated(async_client: AsyncClient, override_auth, mock_user, mocker):
    updated = make_account(id=mock_user.id, full_name="Ibu Sari", school_name="SMPN 1")
    update = mocker.patch(f"{SERVICE}.update_profile", new_callable=AsyncMock, return_value=updated)

    response = await async_client.patch("/api/users/me", json={"full_name": " Ibu Sari ", "school_name": "SMPN 1"})

    assert response.status_code == 200
    assert (response.json()["full_name"], response.json()["school_name"]) == ("Ibu Sari", "SMPN 1")
    assert update.await_args.args[1] is mock_user
    assert update.await_args.args[2].full_name == "Ibu Sari"


@pytest.mark.parametrize("body", [{}, {"full_name": "A"}, {"full_name": "x" * 101}, {"school_name": "x" * 151}])
async def test_an_invalid_profile_update_is_rejected(async_client: AsyncClient, override_auth, body):
    assert (await async_client.patch("/api/users/me", json=body)).status_code == 422


async def test_a_profile_update_cannot_change_the_role_or_the_tier(async_client: AsyncClient, override_auth, mock_user, mocker):
    update = mocker.patch(f"{SERVICE}.update_profile", new_callable=AsyncMock, return_value=make_account(id=mock_user.id))

    await async_client.patch("/api/users/me", json={"full_name": "Ibu Sari", "role": "admin", "subscription_tier": "premium"})

    payload = update.await_args.args[2]
    assert not hasattr(payload, "role") and not hasattr(payload, "subscription_tier")


async def test_the_password_is_changed_and_the_answer_has_no_body(async_client: AsyncClient, override_auth, mock_user, mocker):
    change = mocker.patch(f"{SERVICE}.change_password", new_callable=AsyncMock)

    response = await async_client.post(
        "/api/users/me/change-password", json={"current_password": "old-password", "new_password": "new-password-123"}
    )

    assert response.status_code == 204 and response.content == b""
    assert change.await_args.args[1:] == (mock_user, "old-password", "new-password-123")


@pytest.mark.parametrize("body", [
    {"current_password": "", "new_password": "new-password-123"},
    {"current_password": "old-password", "new_password": "short"},
    {"current_password": "old-password", "new_password": "é" * 40},  # 80 bytes: over bcrypt's limit
    {"new_password": "new-password-123"},
])
async def test_an_invalid_password_change_is_rejected_before_the_service(async_client: AsyncClient, override_auth, mocker, body):
    change = mocker.patch(f"{SERVICE}.change_password", new_callable=AsyncMock)

    assert (await async_client.post("/api/users/me/change-password", json=body)).status_code == 422
    change.assert_not_awaited()


@pytest.mark.parametrize("error,status,code", [
    (InvalidPasswordError("wrong"), 400, "invalid_password"),  # never 401: the client would think the session ended
    (TooManyAttemptsError("later"), 429, "too_many_attempts"),
])
async def test_password_failures_have_stable_codes(async_client: AsyncClient, override_auth, mocker, error, status, code):
    mocker.patch(f"{SERVICE}.change_password", new_callable=AsyncMock, side_effect=error)

    response = await async_client.post(
        "/api/users/me/change-password", json={"current_password": "x", "new_password": "new-password-123"}
    )

    assert (response.status_code, response.json()["code"]) == (status, code)


async def test_the_account_is_deleted_with_the_password_in_the_body(async_client: AsyncClient, override_auth, mock_user, mocker):
    delete = mocker.patch(f"{SERVICE}.delete_account", new_callable=AsyncMock)

    response = await async_client.request("DELETE", "/api/users/me", json={"password": "secret-password"})

    assert response.status_code == 204
    assert delete.await_args.args[1:] == (mock_user, "secret-password")


async def test_deleting_an_account_needs_a_password_and_cannot_orphan_the_system(async_client: AsyncClient, override_auth, mocker):
    assert (await async_client.request("DELETE", "/api/users/me", json={})).status_code == 422

    mocker.patch(f"{SERVICE}.delete_account", new_callable=AsyncMock, side_effect=LastAdminError("only admin"))
    response = await async_client.request("DELETE", "/api/users/me", json={"password": "secret-password"})

    assert (response.status_code, response.json()["code"]) == (409, "last_admin")


# --- administrators --------------------------------------------------------------------------------------------------

async def test_the_user_list_is_paginated_filtered_and_shows_status(async_client: AsyncClient, admin, mocker):
    disabled = make_account(disabled_at=datetime(2026, 10, 1, tzinfo=timezone.utc))
    listing = mocker.patch(f"{SERVICE}.list_users", new_callable=AsyncMock, return_value=([disabled], 41))

    response = await async_client.get("/api/users", params={"skip": 20, "limit": 10, "q": "sari", "role": "user"})

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["skip"], body["limit"]) == (41, 20, 10)
    assert body["items"][0]["disabled_at"] == "2026-10-01T00:00:00Z"
    assert "password_hash" not in body["items"][0]
    assert listing.await_args.args[1:] == (20, 10, "sari", "user")


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": 101}, {"role": "owner"}, {"q": "x" * 101}])
async def test_the_user_list_rejects_out_of_range_parameters(async_client: AsyncClient, admin, params):
    assert (await async_client.get("/api/users", params=params)).status_code == 422


async def test_an_admin_updates_another_account(async_client: AsyncClient, admin, mocker):
    target = make_account(role="admin", subscription_tier="premium")
    update = mocker.patch(f"{SERVICE}.admin_update", new_callable=AsyncMock, return_value=target)

    response = await async_client.patch(
        f"/api/users/{target.id}", json={"role": "admin", "subscription_tier": "premium", "disabled": False}
    )

    assert response.status_code == 200 and response.json()["role"] == "admin"
    assert update.await_args.args[1:3] == (admin, target.id)
    payload = update.await_args.args[3]
    assert (payload.role, payload.subscription_tier, payload.disabled) == ("admin", "premium", False)


@pytest.mark.parametrize("body", [{}, {"role": "owner"}, {"subscription_tier": "gold"}, {"disabled": "maybe"}])
async def test_an_invalid_admin_update_is_rejected(async_client: AsyncClient, admin, body):
    assert (await async_client.patch(f"/api/users/{uuid.uuid4()}", json=body)).status_code == 422


@pytest.mark.parametrize("error,status,code", [
    (UserNotFoundError("none"), 404, "user_not_found"),
    (LastAdminError("last"), 409, "last_admin"),
    (SelfActionError("self"), 409, "self_action_forbidden"),
])
async def test_admin_failures_have_stable_codes(async_client: AsyncClient, admin, mocker, error, status, code):
    mocker.patch(f"{SERVICE}.admin_update", new_callable=AsyncMock, side_effect=error)
    mocker.patch(f"{SERVICE}.admin_delete", new_callable=AsyncMock, side_effect=error)
    target = uuid.uuid4()

    updated = await async_client.patch(f"/api/users/{target}", json={"disabled": True})
    deleted = await async_client.delete(f"/api/users/{target}")

    assert (updated.status_code, updated.json()["code"]) == (status, code)
    assert (deleted.status_code, deleted.json()["code"]) == (status, code)


async def test_an_admin_deletes_another_account(async_client: AsyncClient, admin, mocker):
    delete = mocker.patch(f"{SERVICE}.admin_delete", new_callable=AsyncMock)
    target = uuid.uuid4()

    response = await async_client.delete(f"/api/users/{target}")

    assert response.status_code == 204
    assert delete.await_args.args[1:] == (admin, target)


async def test_a_teacher_cannot_use_the_admin_endpoints(async_client: AsyncClient, override_auth, mocker):
    service = mocker.patch(f"{SERVICE}.admin_update", new_callable=AsyncMock)
    target = uuid.uuid4()

    responses = [
        await async_client.get("/api/users"),
        await async_client.patch(f"/api/users/{target}", json={"role": "admin"}),
        await async_client.delete(f"/api/users/{target}"),
    ]

    assert all(r.status_code == 403 and r.json()["code"] == "forbidden" for r in responses)
    service.assert_not_awaited()


async def test_the_fixed_user_paths_are_not_swallowed_by_the_id_routes(async_client: AsyncClient, admin, override_auth, mocker):
    mocker.patch("app.api.routers.users.llm_cost_log_repo.get_all_users_aggregated_costs", new_callable=AsyncMock, return_value=[])
    mocker.patch(f"{SERVICE}.delete_account", new_callable=AsyncMock)

    assert (await async_client.get("/api/users/costs")).json() == []
    assert (await async_client.request("DELETE", "/api/users/me", json={"password": "secret-password"})).status_code == 204


# --- disabled accounts -----------------------------------------------------------------------------------------

async def test_a_valid_access_token_of_a_disabled_account_is_refused(async_client: AsyncClient, mocker):
    user = make_account(disabled_at=datetime.now(timezone.utc))
    mocker.patch("app.api.deps.user_repo.get", new_callable=AsyncMock, return_value=user)
    token, _ = security.create_access_token(user.id)

    response = await async_client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["code"] == "account_disabled"
