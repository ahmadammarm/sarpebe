import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.core.exceptions import QuotaExceededError
from app.core.services import quota_service as quota_module
from app.core.services.quota_service import QUOTA_WINDOW, QuotaService, QuotaStatus, quota_service
from app.db.models.profile import Profile

async_test = pytest.mark.asyncio(loop_scope="session")

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


def make_user(role="user", tier="free") -> Profile:
    return Profile(id=uuid.uuid4(), full_name="Guru", role=role, subscription_tier=tier)


@pytest.fixture(autouse=True)
def limit_of_three(mocker):
    mocker.patch.object(settings, "generation_daily_limit_free", 3)
    mocker.patch.object(quota_module, "utc_now", return_value=NOW)


@pytest.fixture
def usage(mocker):
    """Sets what the repository reports: `usage.return_value = (count, oldest_created_at)`."""
    return mocker.patch.object(quota_module.lesson_plan_repo, "usage_since", new_callable=AsyncMock, return_value=(0, None))


@pytest.fixture
def lock(mocker):
    return mocker.patch.object(quota_module.user_repo, "get_by_id_for_update", new_callable=AsyncMock)


# --- who is limited ------------------------------------------------------------------------------------------------

def test_a_free_teacher_has_the_configured_limit():
    assert quota_service.limit_for(make_user()) == 3


@pytest.mark.parametrize("user", [make_user(role="admin"), make_user(tier="premium")])
def test_admins_and_other_tiers_are_not_limited(user):
    assert quota_service.limit_for(user) is None


def test_a_configured_limit_of_zero_means_nobody_is_limited(mocker):
    mocker.patch.object(settings, "generation_daily_limit_free", 0)
    assert quota_service.limit_for(make_user()) is None


# --- status --------------------------------------------------------------------------------------------------------

@async_test
async def test_status_counts_only_the_last_24_hours(usage):
    user = make_user()

    await quota_service.get_status(AsyncMock(), user)

    assert usage.await_args.args[1] == user.id
    assert usage.await_args.args[2] == NOW - QUOTA_WINDOW


@async_test
async def test_status_reports_what_is_left_and_when_a_slot_frees_up(usage):
    oldest = NOW - timedelta(hours=5)
    usage.return_value = (2, oldest)

    status = await quota_service.get_status(AsyncMock(), make_user())

    assert (status.limit, status.used, status.remaining, status.unlimited) == (3, 2, 1, False)
    assert status.resets_at == oldest + QUOTA_WINDOW


@async_test
async def test_status_without_any_plan_has_no_reset_time(usage):
    status = await quota_service.get_status(AsyncMock(), make_user())

    assert (status.used, status.remaining, status.resets_at) == (0, 3, None)


@async_test
async def test_status_of_an_unlimited_user_still_shows_usage(usage):
    usage.return_value = (7, NOW - timedelta(hours=1))

    status = await quota_service.get_status(AsyncMock(), make_user(role="admin"))

    assert (status.limit, status.used, status.remaining, status.unlimited) == (None, 7, None, True)


def test_remaining_never_goes_below_zero():
    assert QuotaStatus(limit=3, used=5, resets_at=None).remaining == 0


# --- enforcing -----------------------------------------------------------------------------------------------------

@async_test
async def test_a_teacher_with_a_slot_left_may_start_a_plan(usage, lock):
    usage.return_value = (2, NOW - timedelta(hours=1))
    user = make_user()
    lock.return_value = user

    await quota_service.ensure_available(AsyncMock(), user)

    lock.assert_awaited_once()


@async_test
async def test_a_teacher_at_the_limit_is_refused(usage, lock):
    usage.return_value = (3, NOW - timedelta(hours=1))
    user = make_user()
    lock.return_value = user

    with pytest.raises(QuotaExceededError):
        await quota_service.ensure_available(AsyncMock(), user)


@async_test
async def test_the_check_runs_under_the_users_row_lock(usage, lock):
    """The lock is what stops two simultaneous requests from both taking the last slot."""
    order = []
    lock.side_effect = lambda *a, **k: order.append("lock") or make_user()
    usage.side_effect = lambda *a, **k: order.append("count") or (0, None)

    await quota_service.ensure_available(AsyncMock(), make_user())

    assert order == ["lock", "count"]


@async_test
async def test_an_unlimited_user_is_neither_locked_nor_counted(usage, lock):
    await quota_service.ensure_available(AsyncMock(), make_user(role="admin"))

    lock.assert_not_awaited()
    usage.assert_not_awaited()


@async_test
async def test_the_limit_is_read_from_the_locked_row_so_a_tier_change_applies_at_once(usage, lock):
    usage.return_value = (50, NOW)
    stale = make_user(tier="free")
    lock.return_value = make_user(tier="premium")
    lock.return_value.id = stale.id

    await quota_service.ensure_available(AsyncMock(), stale)  # must not raise: the fresh row is a paid tier
