"""
Creates (or updates) a verified user from the command line. Run from sarpebe-backend/:

    python -m scripts.create_user <email> <password> [--role admin] [--name "Full Name"]

If the email already exists, its password and role are updated.
"""
import argparse
import asyncio
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, normalize_email
from app.db.models.profile import Profile
from app.db.repositories.user_repository import user_repo
from app.db.session import AsyncSessionLocal
from app.utils.time import utc_now

Action = Literal["created", "updated", "skipped"]

async def upsert_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    role: str,
    name: str | None = None,
    update_existing: bool = True,
) -> tuple[Profile, Action]:
    """
    Creates a verified user, or updates the password and role of an existing one.
    With update_existing=False an existing user is left untouched. The caller commits.
    """
    email = normalize_email(email)
    user = await user_repo.get_by_email(db, email)

    if user:
        if not update_existing:
            return user, "skipped"
        user.password_hash = await hash_password(password)
        user.role = role
        user.email_verified_at = user.email_verified_at or utc_now()
        return user, "updated"

    user = Profile(
        email=email,
        password_hash=await hash_password(password),
        full_name=name or email.split("@")[0],
        role=role,
        subscription_tier="free",
        email_verified_at=utc_now(),
    )
    db.add(user)
    await db.flush()
    return user, "created"

async def main(email: str, password: str, role: str, name: str | None) -> None:
    async with AsyncSessionLocal() as db:
        user, action = await upsert_user(db, email=email, password=password, role=role, name=name)
        await db.commit()
        print(f"User {user.email} {action} (id={user.id}, role={role}).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("--role", default="user", choices=["user", "admin"])
    parser.add_argument("--name")
    args = parser.parse_args()
    asyncio.run(main(args.email, args.password, args.role, args.name))
