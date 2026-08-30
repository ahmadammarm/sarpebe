import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import update
from app.db.models.profile import Profile

async def main():
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Profile)
            .where(Profile.id == '001209f6-43ba-4b4b-b292-88d8fc776689')
            .values(subscription_tier='premium')
        )
        await db.commit()
    print("User tier updated to premium!")

if __name__ == "__main__":
    asyncio.run(main())
