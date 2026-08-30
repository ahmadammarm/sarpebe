import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def test_get_me(async_client: AsyncClient, override_auth, mock_user):
    """Test the /api/users/me endpoint with mocked authentication."""
    response = await async_client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Test User"
    assert data["subscription_tier"] == "free"
    assert data["id"] == str(mock_user.id)
