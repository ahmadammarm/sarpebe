import uuid
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from unittest.mock import AsyncMock

from app.db.models.lesson_plan import LessonPlan
from app.schemas.lesson_plan_content import GeneratedModul, Identity, ModulContent
from tests.factories import make_modul_dict

pytestmark = pytest.mark.asyncio(loop_scope="session")

VALID_PAYLOAD = {"grade_level": "10", "subject": "Biologi", "topic": "Sel Hewan"}

def make_plan(user_id, status="completed", job_id="job-1", content=None, age_minutes=0, schema_version=1):
    return LessonPlan(
        id=uuid.uuid4(),
        user_id=user_id,
        grade_level="10",
        subject="Biologi",
        topic="Sel Hewan",
        status=status,
        job_id=job_id,
        generated_content=content,
        schema_version=schema_version,
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


# --- request options (meetings, minutes, teaching model, class notes) ----------------------------------

async def test_create_passes_the_teachers_options_to_the_service(async_client: AsyncClient, override_auth, mocker):
    mock_trigger = mocker.patch(
        "app.api.routers.lesson_plans.lesson_plan_service.trigger_generation",
        new_callable=AsyncMock, return_value=("job-1", uuid.uuid4()),
    )

    response = await async_client.post("/api/lesson-plans", json={
        **VALID_PAYLOAD, "meeting_count": 3, "minutes_per_meeting": 90,
        "teaching_model": "pjbl", "class_notes": "  kelas aktif  ",
    })

    assert response.status_code == 202
    payload = mock_trigger.call_args.args[2]
    assert (payload.meeting_count, payload.minutes_per_meeting, payload.teaching_model.value) == (3, 90, "pjbl")
    assert payload.class_notes == "kelas aktif"


async def test_create_without_options_uses_the_defaults(async_client: AsyncClient, override_auth, mocker):
    mock_trigger = mocker.patch(
        "app.api.routers.lesson_plans.lesson_plan_service.trigger_generation",
        new_callable=AsyncMock, return_value=("job-1", uuid.uuid4()),
    )
    await async_client.post("/api/lesson-plans", json=VALID_PAYLOAD)
    payload = mock_trigger.call_args.args[2]
    assert (payload.meeting_count, payload.minutes_per_meeting, payload.teaching_model.value) == (1, 80, "otomatis")


@pytest.mark.parametrize("extra", [
    {"meeting_count": 0}, {"meeting_count": 9}, {"minutes_per_meeting": 5},
    {"teaching_model": "ceramah"}, {"class_notes": "x" * 501},
])
async def test_create_rejects_invalid_options(async_client: AsyncClient, override_auth, extra):
    response = await async_client.post("/api/lesson-plans", json={**VALID_PAYLOAD, **extra})
    assert response.status_code == 422


# --- editing a version-2 module ---------------------------------------------------------------------------

def stored_module(user_id) -> LessonPlan:
    content = ModulContent(
        **GeneratedModul.model_validate(make_modul_dict()).model_dump(),
        identity=Identity(
            subject="IPS", grade_level="9", fase="D", topic="Ekonomi", meetings=2,
            minutes_per_meeting=80, teaching_model="otomatis",
        ),
    ).model_dump(mode="json")
    return make_plan(user_id, status="completed", content=content, schema_version=2)


async def test_editing_a_module_so_a_table_loses_a_cell_is_rejected(async_client: AsyncClient, override_auth, mock_user, mocker):
    plan = stored_module(mock_user.id)
    mocker.patch(
        "app.core.services.lesson_plan_service.lesson_plan_repo.get_by_id_and_user",
        new_callable=AsyncMock, return_value=plan,
    )
    broken = dict(plan.generated_content)
    broken["meetings"][0]["activities"]["rows"][0] = broken["meetings"][0]["activities"]["rows"][0][:-1]

    response = await async_client.put(f"/api/lesson-plans/{plan.id}", json={"generated_content": broken})

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_content"
    assert "meetings.0.activities" in response.json()["detail"]


async def test_a_module_response_tells_the_client_which_format_it_is(async_client: AsyncClient, override_auth, mock_user, mocker):
    plan = stored_module(mock_user.id)
    plan.request_options = {"meeting_count": 2, "minutes_per_meeting": 80, "teaching_model": "otomatis", "class_notes": ""}
    mocker.patch(
        "app.core.services.lesson_plan_service.lesson_plan_repo.get_by_id_and_user",
        new_callable=AsyncMock, return_value=plan,
    )

    body = (await async_client.get(f"/api/lesson-plans/{plan.id}")).json()

    assert body["schema_version"] == 2
    assert body["generated_content"]["identity"]["fase"] == "D"
    assert body["request_options"]["meeting_count"] == 2
