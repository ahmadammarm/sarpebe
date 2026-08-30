import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def test_create_lesson_plan(async_client: AsyncClient, override_auth, mock_user, mocker):
    """Test creating a lesson plan successfully."""
    # Mock the trigger_generation service so it doesn't hit the DB or Celery
    mock_trigger = mocker.patch(
        "app.api.routers.lesson_plans.lesson_plan_service.trigger_generation",
        new_callable=AsyncMock
    )
    mock_trigger.return_value = "fake-job-123"

    payload = {
        "grade_level": "10",
        "subject": "Biologi",
        "topic": "Sel Hewan"
    }
    response = await async_client.post("/api/lesson-plans", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == "fake-job-123"
    mock_trigger.assert_called_once()

async def test_create_lesson_plan_quota_exceeded(async_client: AsyncClient, override_auth, mock_user, mocker):
    """Test creating a lesson plan when quota is exceeded."""
    from app.core.exceptions import QuotaExceededError
    
    mock_trigger = mocker.patch(
        "app.api.routers.lesson_plans.lesson_plan_service.trigger_generation",
        new_callable=AsyncMock
    )
    mock_trigger.side_effect = QuotaExceededError("Free tier limit of 3 reached.")

    payload = {
        "grade_level": "10",
        "subject": "Biologi",
        "topic": "Sel Hewan"
    }
    response = await async_client.post("/api/lesson-plans", json=payload)
    
    assert response.status_code == 403
    assert "limit of 3 reached" in response.json()["detail"]
