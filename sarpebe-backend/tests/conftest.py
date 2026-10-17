import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_current_user, get_db
from app.db.models.profile import Profile
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
