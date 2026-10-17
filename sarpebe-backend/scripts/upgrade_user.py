"""
Sets a user's role. Run from sarpebe-backend/:

    python -m scripts.upgrade_user <user_id> [role]    # role defaults to "admin"
"""
import asyncio
import sys
from uuid import UUID

from sqlalchemy import update

from app.db.models.profile import Profile
from app.db.session import AsyncSessionLocal

async def main(user_id: UUID, role: str) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(update(Profile).where(Profile.id == user_id).values(role=role))
        await db.commit()
    print(f"User {user_id} role set to {role!r}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    asyncio.run(main(UUID(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else "admin"))
