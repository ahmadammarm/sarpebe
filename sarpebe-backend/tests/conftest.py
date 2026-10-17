import os

# Must be set before the app (and its Settings) is imported; takes priority over .env.
os.environ["AUTH_JWT_SECRET"] = "test-secret-test-secret-test-secret-0123456789"
os.environ["EMAIL_BACKEND"] = "console"
os.environ["REQUIRE_EMAIL_VERIFICATION"] = "true"

import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_current_user, get_db
from app.db.base import Base
from app.db.models import AuthToken, Profile, RefreshToken
from datetime import datetime, timezone
import uuid

@pytest.fixture
def mock_user():
    return Profile(
        id=uuid.uuid4(),
        full_name="Test User",
        subscription_tier="free",
        role="user",
        created_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def override_auth(mock_user):
    async def _mock_get_current_user():
        return mock_user
    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def mock_db():
    """A stand-in session so endpoint tests never open a real database connection."""
    return AsyncMock()

@pytest.fixture
async def async_client(mock_db):
    async def _mock_get_db():
        yield mock_db
    app.dependency_overrides[get_db] = _mock_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
async def db():
    """A real SQLAlchemy session over in-memory SQLite with the authentication tables."""
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[Profile.__table__, RefreshToken.__table__, AuthToken.__table__],
        )
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()
