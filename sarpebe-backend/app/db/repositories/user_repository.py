from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.profile import Profile
from app.db.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[Profile, dict, dict]):
    def __init__(self):
        super().__init__(Profile)
    
    async def get_by_id_for_update(self, db: AsyncSession, id: str) -> Profile | None:
        """
        Fetches a profile and explicitly locks the row using SELECT ... FOR UPDATE.
        Crucial for preventing race conditions when checking and decrementing quotas.
        """
        result = await db.execute(
            select(self.model).filter(self.model.id == id).with_for_update()
        )
        return result.scalar_one_or_none()

user_repo = UserRepository()
