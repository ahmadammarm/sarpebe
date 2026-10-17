import uuid
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from unittest.mock import AsyncMock

from app.db.models.lesson_plan import LessonPlan

pytestmark = pytest.mark.asyncio(loop_scope="session")

VALID_PAYLOAD = {"grade_level": "10", "subject": "Biologi", "topic": "Sel Hewan"}

def make_plan(user_id, status="completed", job_id="job-1", content=None, age_minutes=0):
    return LessonPlan(
        id=uuid.uuid4(),
        user_id=user_id,
        grade_level="10",
        subject="Biologi",
        topic="Sel Hewan",
        status=status,
        job_id=job_id,
        generated_content=content,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=age_minutes),
    )

async def test_create_lesson_plan(async_client: AsyncClient, override_auth, mocker):
    plan_id = uuid.uuid4()
    mock_trigger = mocker.patch(
        "app.api.routers.lesson_plans.lesson_plan_service.trigger_generation",
        new_callable=AsyncMock,
        return_value=("fake-job-123", plan_id),
    )

    response = await async_client.post("/api/lesson-plans", json=VALID_PAYLOAD)

    assert response.status_code == 202
    assert response.json() == {"job_id": "fake-job-123", "id": str(plan_id)}
    mock_trigger.assert_called_once()

async def test_create_lesson_plan_rejects_blank_topic(async_client: AsyncClient, override_auth):
    response = await async_client.post("/api/lesson-plans", json={**VALID_PAYLOAD, "topic": "   "})
    assert response.status_code == 422

async def test_job_endpoints_require_auth(async_client: AsyncClient):
    status_response = await async_client.get("/api/lesson-plans/jobs/job-1")
    stream_response = await async_client.get("/api/lesson-plans/jobs/job-1/stream")
    assert status_response.status_code in (401, 403)
    assert stream_response.status_code in (401, 403)

async def test_job_status_of_other_users_job_is_404(async_client: AsyncClient, override_auth, mocker):
    mocker.patch(
        "app.core.services.lesson_plan_service.lesson_plan_repo.get_by_job_id_and_user",
        new_callable=AsyncMock,
        return_value=None,
    )
    status_response = await async_client.get("/api/lesson-plans/jobs/someone-elses-job")
    stream_response = await async_client.get("/api/lesson-plans/jobs/someone-elses-job/stream")
    assert status_response.status_code == 404
    assert stream_response.status_code == 404

async def test_job_status_is_derived_from_plan_row(async_client: AsyncClient, override_auth, mock_user, mocker):
    plan = make_plan(mock_user.id, status="failed", content={"error": "Belum ada dokumen kurikulum"})
    mocker.patch(
        "app.core.services.lesson_plan_service.lesson_plan_repo.get_by_job_id_and_user",
        new_callable=AsyncMock,
        return_value=plan,
    )
    response = await async_client.get("/api/lesson-plans/jobs/job-1")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["error"] == "Belum ada dokumen kurikulum"
    assert body["lesson_plan_id"] == str(plan.id)

async def test_stale_unfinished_job_is_reported_failed(async_client: AsyncClient, override_auth, mock_user, mocker):
    plan = make_plan(mock_user.id, status="processing", age_minutes=30)
    mocker.patch(
        "app.core.services.lesson_plan_service.lesson_plan_repo.get_by_job_id_and_user",
        new_callable=AsyncMock,
        return_value=plan,
    )
    response = await async_client.get("/api/lesson-plans/jobs/job-1")
    assert response.json()["status"] == "failed"
    assert response.json()["error"]

@pytest.mark.parametrize("status", ["pending", "processing", "failed"])
async def test_update_requires_completed_plan(async_client: AsyncClient, override_auth, mock_user, mocker, status):
    plan = make_plan(mock_user.id, status=status)
    mocker.patch(
        "app.core.services.lesson_plan_service.lesson_plan_repo.get_by_id_and_user",
        new_callable=AsyncMock,
        return_value=plan,
    )
    response = await async_client.put(f"/api/lesson-plans/{plan.id}", json={"generated_content": {"title": "x"}})
    assert response.status_code == 409

async def test_get_missing_plan_is_404(async_client: AsyncClient, override_auth, mocker):
    mocker.patch(
        "app.core.services.lesson_plan_service.lesson_plan_repo.get_by_id_and_user",
        new_callable=AsyncMock,
        return_value=None,
    )
    response = await async_client.get(f"/api/lesson-plans/{uuid.uuid4()}")
    assert response.status_code == 404
