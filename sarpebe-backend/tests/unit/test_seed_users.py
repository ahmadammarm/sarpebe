import pytest
from sqlalchemy import select

from app.core import security
from app.db.models import Profile
from scripts.seed_users import SEED_USERS, resolve_users, seed

async_test = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(autouse=True)
def fast_hashing(monkeypatch):
    monkeypatch.setattr(security, "BCRYPT_ROUNDS", 4)


async def profiles(db):
    return {p.email: p for p in (await db.execute(select(Profile))).scalars().all()}


def test_resolve_users_uses_defaults_and_environment_overrides():
    defaults = resolve_users({})
    assert [email for _, email, _ in defaults] == ["admin@example.com", "guru@example.com"]
    assert all(password is None for _, _, password in defaults)

    custom = resolve_users({
        "SEED_ADMIN_EMAIL": " Boss@School.ID ",
        "SEED_ADMIN_PASSWORD": "a-strong-password",
    })
    _, email, password = custom[0]
    assert email == "boss@school.id"
    assert password == "a-strong-password"


@pytest.mark.parametrize("password", ["short", "x" * 80])
def test_resolve_users_rejects_unusable_passwords(password):
    with pytest.raises(SystemExit):
        resolve_users({"SEED_ADMIN_PASSWORD": password})


def test_resolve_users_rejects_duplicate_emails():
    with pytest.raises(SystemExit):
        resolve_users({"SEED_ADMIN_EMAIL": "same@example.com", "SEED_USER_EMAIL": "SAME@example.com"})


@async_test
async def test_seed_creates_verified_admin_and_user(db):
    results = await seed(db, resolve_users({}))
    await db.commit()

    stored = await profiles(db)
    assert stored["admin@example.com"].role == "admin"
    assert stored["guru@example.com"].role == "user"
    assert all(p.email_verified_at is not None for p in stored.values())
    assert [r.action for r in results] == ["created", "created"]


@async_test
async def test_seed_generates_and_stores_a_working_password(db):
    results = await seed(db, resolve_users({}))
    await db.commit()

    generated = results[0].generated_password
    assert generated and len(generated) >= 12
    admin = (await profiles(db))["admin@example.com"]
    assert admin.password_hash != generated
    assert await security.verify_password(generated, admin.password_hash)


@async_test
async def test_seed_uses_password_from_environment_and_does_not_print_it(db):
    users = resolve_users({"SEED_ADMIN_PASSWORD": "from-the-environment", "SEED_USER_PASSWORD": "another-env-pass"})
    results = await seed(db, users)
    await db.commit()

    assert all(r.generated_password is None for r in results)
    admin = (await profiles(db))["admin@example.com"]
    assert await security.verify_password("from-the-environment", admin.password_hash)


@async_test
async def test_seed_is_idempotent_and_keeps_existing_accounts_untouched(db):
    first = await seed(db, resolve_users({}))
    await db.commit()
    original_hash = (await profiles(db))["admin@example.com"].password_hash

    second = await seed(db, resolve_users({}))
    await db.commit()

    assert [r.action for r in second] == ["skipped", "skipped"]
    assert all(r.generated_password is None for r in second)  # nothing new to reveal
    stored = await profiles(db)
    assert len(stored) == len(SEED_USERS)
    assert stored["admin@example.com"].password_hash == original_hash
    assert first[0].generated_password  # first run did generate one


@async_test
async def test_seed_reset_passwords_overwrites_existing_accounts(db):
    await seed(db, resolve_users({"SEED_ADMIN_PASSWORD": "original-password"}))
    await db.commit()

    results = await seed(db, resolve_users({"SEED_ADMIN_PASSWORD": "replacement-password"}), reset_passwords=True)
    await db.commit()

    assert results[0].action == "updated"
    admin = (await profiles(db))["admin@example.com"]
    assert await security.verify_password("replacement-password", admin.password_hash)
    assert not await security.verify_password("original-password", admin.password_hash)


@async_test
async def test_seed_does_not_demote_or_change_a_differently_roled_existing_user(db):
    existing = Profile(email="admin@example.com", full_name="Someone", role="user", password_hash="x")
    db.add(existing)
    await db.commit()

    results = await seed(db, resolve_users({}))
    await db.commit()

    assert results[0].action == "skipped"
    assert (await profiles(db))["admin@example.com"].role == "user"
