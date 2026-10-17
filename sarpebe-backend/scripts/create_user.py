"""
Creates (or updates) a verified user from the command line. Run from sarpebe-backend/:

    python -m scripts.create_user <email> <password> [--role admin] [--name "Full Name"]

If the email already exists, its password and role are updated.
"""
import argparse
import asyncio

from app.core.security import hash_password, normalize_email
from app.db.models.profile import Profile
from app.db.repositories.user_repository import user_repo
from app.db.session import AsyncSessionLocal
from app.utils.time import utc_now

async def main(email: str, password: str, role: str, name: str | None) -> None:
    email = normalize_email(email)
    password_hash = await hash_password(password)

    async with AsyncSessionLocal() as db:
        user = await user_repo.get_by_email(db, email)
        if user:
            user.password_hash = password_hash
            user.role = role
            user.email_verified_at = user.email_verified_at or utc_now()
            action = "updated"
        else:
            user = Profile(
                email=email,
                password_hash=password_hash,
                full_name=name or email.split("@")[0],
                role=role,
                subscription_tier="free",
                email_verified_at=utc_now(),
            )
            db.add(user)
            action = "created"
        await db.commit()
        print(f"User {email} {action} (id={user.id}, role={role}).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("--role", default="user", choices=["user", "admin"])
    parser.add_argument("--name")
    args = parser.parse_args()
    asyncio.run(main(args.email, args.password, args.role, args.name))
