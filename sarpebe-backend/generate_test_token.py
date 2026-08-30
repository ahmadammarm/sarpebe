import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models.profile import Profile

async def main():
    test_user_id = uuid.uuid4()
    
    # 1. Create a fake Supabase JWT for this user
    payload = {
        "sub": str(test_user_id),
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(days=365),
        "iat": datetime.now(timezone.utc)
    }
    # Sign it using the exact secret the backend uses to verify
    token = jwt.encode(payload, settings.supabase_jwt_secret, algorithm="HS256")
    
    # 2. Insert the user into the database
    async with AsyncSessionLocal() as db:
        user = Profile(
            id=test_user_id,
            full_name="Test Educator",
            subscription_tier="premium"
        )
        db.add(user)
        await db.commit()
        
    print("\n" + "="*50)
    print("TEST USER CREATED SUCCESSFULLY")
    print(f"User ID: {test_user_id}")
    print("="*50)
    print("PASTE THE FOLLOWING TOKEN INTO SWAGGER 'AUTHORIZE':\n")
    print(token)
    print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(main())
