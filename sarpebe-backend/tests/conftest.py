import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_current_user
from app.db.models.profile import Profile
from datetime import datetime, timezone
import uuid

@pytest.fixture
def mock_user():
    return Profile(
        id=uuid.uuid4(),
        full_name="Test User",
        subscription_tier="free",
        created_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def override_auth(mock_user):
    async def _mock_get_current_user():
        return mock_user
    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
