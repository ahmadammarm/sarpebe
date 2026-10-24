from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.core.services.quota_service import QuotaStatus

pytestmark = pytest.mark.asyncio(loop_scope="session")

RESETS_AT = datetime(2026, 10, 25, 8, 30, tzinfo=timezone.utc)


# --- quota -------------------------------------------------------------------------------------------------

async def test_the_quota_shows_what_is_left_and_when_a_slot_frees_up(async_client: AsyncClient, override_auth, mocker):
    mocker.patch(
        "app.api.routers.users.quota_service.get_status", new_callable=AsyncMock,
        return_value=QuotaStatus(limit=10, used=7, resets_at=RESETS_AT),
    )

    response = await async_client.get("/api/users/me/quota")

    assert response.status_code == 200
    assert response.json() == {
        "limit": 10, "used": 7, "remaining": 3, "unlimited": False, "resets_at": "2026-10-25T08:30:00Z",
    }


async def test_the_quota_of_an_unlimited_user_has_no_limit(async_client: AsyncClient, override_auth, mocker):
    mocker.patch(
        "app.api.routers.users.quota_service.get_status", new_callable=AsyncMock,
        return_value=QuotaStatus(limit=None, used=2, resets_at=None),
    )

    body = (await async_client.get("/api/users/me/quota")).json()

    assert body == {"limit": None, "used": 2, "remaining": None, "unlimited": True, "resets_at": None}


async def test_the_quota_needs_a_signed_in_user(async_client: AsyncClient):
    assert (await async_client.get("/api/users/me/quota")).status_code in (401, 403)
