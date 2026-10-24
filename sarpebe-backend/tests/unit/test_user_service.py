import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from app.core import rate_limit, security
from app.core.exceptions import (
    InvalidPasswordError,
    LastAdminError,
    SelfActionError,
    TooManyAttemptsError,
    UserNotFoundError,
)
from app.core.security import hash_token
from app.core.services import user_service as service_module
from app.core.services.user_service import RESET_PASSWORD, user_service
from app.db.models import AuthToken, Profile, RefreshToken
from app.schemas.user import ProfileUpdate, UserAdminUpdate
from app.utils.time import utc_now

async_test = pytest.mark.asyncio(loop_scope="session")

PASSWORD = "correct-horse-battery"
NEW_PASSWORD = "another-long-password"


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
def delete(mocker):
    """The cascading delete needs tables the SQLite test database does not have, so it is replaced."""
    return mocker.patch.object(service_module.user_repo, "delete", new_callable=AsyncMock)


async def make_user(db, email="guru@example.com", role="user", tier="free", disabled=False, name="Bu Guru", created_at=None):
    user = Profile(
        id=uuid.uuid4(), email=email, password_hash=await security.hash_password(PASSWORD), full_name=name,
        role=role, subscription_tier=tier, email_verified_at=utc_now(),
        disabled_at=utc_now() if disabled else None, created_at=created_at or utc_now(),
    )
    db.add(user)
    await db.commit()
    return user


async def add_session(db, user):
    token = RefreshToken(
        user_id=user.id, family_id=uuid.uuid4(), token_hash=hash_token(uuid.uuid4().hex),
        expires_at=utc_now() + timedelta(days=14),
    )
    db.add(token)
    await db.commit()
    return token


async def reload(db, *objects):
    """Bulk UPDATEs change the rows, not the objects already in the session, so read them again."""
    for obj in objects:
        await db.refresh(obj)


# --- own profile ---------------------------------------------------------------------------------------------------

@async_test
async def test_the_name_and_school_can_be_changed(db):
    user = await make_user(db)

    updated = await user_service.update_profile(db, user, ProfileUpdate(full_name="  Ibu Sari ", school_name=" SMPN 1 "))

    assert (updated.full_name, updated.school_name) == ("Ibu Sari", "SMPN 1")


@async_test
async def test_an_empty_school_name_clears_it_but_the_name_is_kept_when_not_sent(db):
    user = await make_user(db)
    user.school_name = "SMPN 1"

    updated = await user_service.update_profile(db, user, ProfileUpdate(school_name="   "))

    assert updated.school_name is None and updated.full_name == "Bu Guru"


@async_test
async def test_an_explicit_null_name_does_not_erase_the_name(db):
    user = await make_user(db)

    updated = await user_service.update_profile(db, user, ProfileUpdate(full_name=None, school_name="SMPN 2"))

    assert updated.full_name == "Bu Guru" and updated.school_name == "SMPN 2"


@pytest.mark.parametrize("body", [{}, {"full_name": "A"}, {"full_name": " "}])
def test_an_empty_or_too_short_profile_update_is_invalid(body):
    with pytest.raises(ValueError):
        ProfileUpdate(**body)


# --- changing the password -----------------------------------------------------------------------------------------

@async_test
async def test_a_wrong_current_password_changes_nothing_and_is_counted(db, fake_rate_limit):
    user = await make_user(db)
    old_hash = user.password_hash
    session = await add_session(db, user)

    with pytest.raises(InvalidPasswordError):
        await user_service.change_password(db, user, "not-the-password", NEW_PASSWORD)

    assert user.password_hash == old_hash and session.revoked_at is None
    assert fake_rate_limit[f"auth:password_check_failures:{user.id}"] == 1


@async_test
async def test_a_new_password_replaces_the_old_one_and_signs_out_every_device(db):
    user = await make_user(db)
    other = await make_user(db, email="lain@example.com")
    mine = [await add_session(db, user), await add_session(db, user)]
    theirs = await add_session(db, other)

    await user_service.change_password(db, user, PASSWORD, NEW_PASSWORD)
    await reload(db, *mine, theirs)

    assert await security.verify_password(NEW_PASSWORD, user.password_hash)
    assert not await security.verify_password(PASSWORD, user.password_hash)
    assert all(token.revoked_at is not None for token in mine)
    assert theirs.revoked_at is None  # someone else's sessions are untouched


@async_test
async def test_changing_the_password_cancels_unused_reset_links(db):
    user = await make_user(db)
    link = AuthToken(user_id=user.id, purpose=RESET_PASSWORD, token_hash=hash_token("x"), expires_at=utc_now() + timedelta(hours=1))
    db.add(link)
    await db.commit()

    await user_service.change_password(db, user, PASSWORD, NEW_PASSWORD)
    await reload(db, link)

    assert link.used_at is not None


@async_test
async def test_guessing_the_current_password_locks_the_action_even_for_the_right_password(db):
    user = await make_user(db)
    for _ in range(5):
        with pytest.raises(InvalidPasswordError):
            await user_service.change_password(db, user, "wrong-guess", NEW_PASSWORD)

    with pytest.raises(TooManyAttemptsError):
        await user_service.change_password(db, user, PASSWORD, NEW_PASSWORD)

    assert await security.verify_password(PASSWORD, user.password_hash)


@async_test
async def test_a_correct_password_clears_the_failure_count(db, fake_rate_limit):
    user = await make_user(db)
    with pytest.raises(InvalidPasswordError):
        await user_service.change_password(db, user, "wrong-guess", NEW_PASSWORD)

    await user_service.change_password(db, user, PASSWORD, NEW_PASSWORD)

    assert f"auth:password_check_failures:{user.id}" not in fake_rate_limit


# --- deleting the own account ----------------------------------------------------------------------------------------

@async_test
async def test_a_wrong_password_deletes_nothing(db, delete):
    user = await make_user(db)

    with pytest.raises(InvalidPasswordError):
        await user_service.delete_account(db, user, "wrong")

    delete.assert_not_awaited()


@async_test
async def test_the_right_password_deletes_the_account(db, delete):
    user = await make_user(db)

    await user_service.delete_account(db, user, PASSWORD)

    delete.assert_awaited_once()
    assert delete.await_args.args[1] == user.id


@async_test
async def test_the_only_admin_cannot_delete_their_own_account(db, delete):
    admin = await make_user(db, role="admin")

    with pytest.raises(LastAdminError):
        await user_service.delete_account(db, admin, PASSWORD)

    delete.assert_not_awaited()


@async_test
async def test_an_admin_can_delete_their_account_when_another_admin_remains(db, delete):
    admin = await make_user(db, role="admin")
    await make_user(db, email="admin2@example.com", role="admin")

    await user_service.delete_account(db, admin, PASSWORD)

    delete.assert_awaited_once()


@async_test
async def test_a_disabled_admin_does_not_count_as_the_remaining_admin(db, delete):
    admin = await make_user(db, role="admin")
    await make_user(db, email="admin2@example.com", role="admin", disabled=True)

    with pytest.raises(LastAdminError):
        await user_service.delete_account(db, admin, PASSWORD)


# --- administrators: changing another account ------------------------------------------------------------------------------

@async_test
async def test_an_unknown_user_is_not_found(db):
    admin = await make_user(db, role="admin")

    with pytest.raises(UserNotFoundError):
        await user_service.admin_update(db, admin, uuid.uuid4(), UserAdminUpdate(role="admin"))


@async_test
async def test_an_admin_can_promote_a_teacher_and_change_their_tier(db):
    admin = await make_user(db, role="admin")
    teacher = await make_user(db, email="guru2@example.com")

    updated = await user_service.admin_update(db, admin, teacher.id, UserAdminUpdate(role="admin", subscription_tier="premium"))

    assert (updated.role, updated.subscription_tier) == ("admin", "premium")


@async_test
async def test_an_admin_cannot_change_their_own_role_or_status(db):
    admin = await make_user(db, role="admin")
    await make_user(db, email="admin2@example.com", role="admin")

    with pytest.raises(SelfActionError):
        await user_service.admin_update(db, admin, admin.id, UserAdminUpdate(role="user"))
    with pytest.raises(SelfActionError):
        await user_service.admin_update(db, admin, admin.id, UserAdminUpdate(disabled=True))

    assert admin.role == "admin" and admin.disabled_at is None


@async_test
async def test_repeating_the_current_role_on_oneself_is_not_a_change(db):
    admin = await make_user(db, role="admin")

    updated = await user_service.admin_update(db, admin, admin.id, UserAdminUpdate(role="admin", subscription_tier="premium"))

    assert updated.subscription_tier == "premium"


@async_test
async def test_the_last_active_admin_cannot_be_demoted_or_disabled_by_someone_else(db):
    last = await make_user(db, role="admin")
    # The actor is an admin who is not active anymore, so `last` is the only one left.
    actor = await make_user(db, email="old@example.com", role="admin", disabled=True)

    with pytest.raises(LastAdminError):
        await user_service.admin_update(db, actor, last.id, UserAdminUpdate(role="user"))
    with pytest.raises(LastAdminError):
        await user_service.admin_update(db, actor, last.id, UserAdminUpdate(disabled=True))


@async_test
async def test_one_of_two_admins_can_be_demoted(db):
    admin = await make_user(db, role="admin")
    other = await make_user(db, email="admin2@example.com", role="admin")

    updated = await user_service.admin_update(db, admin, other.id, UserAdminUpdate(role="user"))

    assert updated.role == "user"


@async_test
async def test_disabling_an_account_signs_it_out_everywhere(db):
    admin = await make_user(db, role="admin")
    teacher = await make_user(db, email="guru2@example.com")
    sessions = [await add_session(db, teacher), await add_session(db, teacher)]
    bystander = await add_session(db, admin)

    updated = await user_service.admin_update(db, admin, teacher.id, UserAdminUpdate(disabled=True))
    await reload(db, *sessions, bystander)

    assert updated.disabled_at is not None
    assert all(token.revoked_at is not None for token in sessions)
    assert bystander.revoked_at is None


@async_test
async def test_enabling_an_account_clears_the_block(db):
    admin = await make_user(db, role="admin")
    teacher = await make_user(db, email="guru2@example.com", disabled=True)

    updated = await user_service.admin_update(db, admin, teacher.id, UserAdminUpdate(disabled=False))

    assert updated.disabled_at is None


@async_test
async def test_a_disabled_admin_can_be_demoted_even_when_it_leaves_no_other_admin(db):
    actor = await make_user(db, role="admin")
    sleeping = await make_user(db, email="admin2@example.com", role="admin", disabled=True)

    updated = await user_service.admin_update(db, actor, sleeping.id, UserAdminUpdate(role="user"))

    assert updated.role == "user"


@pytest.mark.parametrize("body", [{}, {"role": "owner"}, {"subscription_tier": "gold"}])
def test_an_empty_or_unknown_admin_update_is_invalid(body):
    with pytest.raises(ValueError):
        UserAdminUpdate(**body)


@async_test
async def test_an_admin_can_delete_another_account_but_not_their_own(db, delete):
    admin = await make_user(db, role="admin")
    teacher = await make_user(db, email="guru2@example.com")

    with pytest.raises(SelfActionError):
        await user_service.admin_delete(db, admin, admin.id)
    with pytest.raises(UserNotFoundError):
        await user_service.admin_delete(db, admin, uuid.uuid4())
    delete.assert_not_awaited()

    await user_service.admin_delete(db, admin, teacher.id)

    assert delete.await_args.args[1] == teacher.id


# --- administrators: listing ---------------------------------------------------------------------------------------------

@async_test
async def test_users_are_listed_newest_first_with_a_total(db):
    now = datetime.now(timezone.utc)
    old = await make_user(db, email="a@example.com", created_at=now - timedelta(days=2))
    new = await make_user(db, email="b@example.com", created_at=now)
    mid = await make_user(db, email="c@example.com", created_at=now - timedelta(days=1))

    items, total = await user_service.list_users(db, 0, 2, None, None)

    assert total == 3 and [u.id for u in items] == [new.id, mid.id]
    page_two, _ = await user_service.list_users(db, 2, 2, None, None)
    assert [u.id for u in page_two] == [old.id]


@async_test
async def test_the_search_matches_name_or_email_ignoring_case(db):
    by_name = await make_user(db, email="x@example.com", name="Ibu Sari Wulandari")
    by_email = await make_user(db, email="sari.guru@example.com", name="Pak Budi")
    await make_user(db, email="z@example.com", name="Pak Anto")

    items, total = await user_service.list_users(db, 0, 20, "  SARI ", None)

    assert total == 2 and {u.id for u in items} == {by_name.id, by_email.id}


@async_test
async def test_percent_and_underscore_in_a_search_are_literal(db):
    percent = await make_user(db, email="p@example.com", name="Diskon 100% guru")
    await make_user(db, email="q@example.com", name="Diskon 1000 guru")
    underscore = await make_user(db, email="a_b@example.com", name="Pak A")
    await make_user(db, email="axb@example.com", name="Pak B")

    by_percent, _ = await user_service.list_users(db, 0, 20, "100%", None)
    by_underscore, _ = await user_service.list_users(db, 0, 20, "a_b", None)

    assert [u.id for u in by_percent] == [percent.id]
    assert [u.id for u in by_underscore] == [underscore.id]


@async_test
async def test_the_list_can_be_limited_to_one_role(db):
    admin = await make_user(db, role="admin")
    await make_user(db, email="guru2@example.com")

    items, total = await user_service.list_users(db, 0, 20, None, "admin")

    assert total == 1 and items[0].id == admin.id
