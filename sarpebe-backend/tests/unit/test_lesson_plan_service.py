import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from app.core.exceptions import InvalidContentError, InvalidStateError
from app.core.services import lesson_plan_service as service_module
from app.core.services.lesson_plan_service import lesson_plan_service
from app.db.models.lesson_plan import LessonPlan
from app.schemas.lesson_plan import LessonPlanCreate, TeachingModel
from app.schemas.lesson_plan_content import GeneratedModul, Identity, ModulContent
from tests.factories import make_modul_dict

pytestmark = pytest.mark.asyncio(loop_scope="session")

USER_ID = uuid.uuid4()


def stored_content() -> dict:
    return ModulContent(
        **GeneratedModul.model_validate(make_modul_dict()).model_dump(),
        identity=Identity(
            subject="IPS", grade_level="9", fase="D", topic="Ekonomi", meetings=2,
            minutes_per_meeting=80, teaching_model="otomatis",
        ),
    ).model_dump(mode="json")


def make_plan(**overrides) -> LessonPlan:
    values = dict(
        id=uuid.uuid4(), user_id=USER_ID, grade_level="9", subject="IPS", topic="Ekonomi",
        status="completed", schema_version=2, generated_content=stored_content(), job_id="job-1",
        created_at=datetime.now(timezone.utc),
    )
    values.update(overrides)
    return LessonPlan(**values)


@pytest.fixture
def repo(mocker):
    plan = make_plan()
    mocker.patch.object(service_module.lesson_plan_repo, "get_by_id_and_user", new_callable=AsyncMock, return_value=plan)
    mocker.patch.object(
        service_module.lesson_plan_repo, "update", new_callable=AsyncMock,
        side_effect=lambda db, obj, data: setattr(obj, "generated_content", data["generated_content"]) or obj,
    )
    return plan


# --- creating ----------------------------------------------------------------------------------------------------

async def test_generation_is_dispatched_only_after_commit(mocker):
    """Regression: dispatching before commit let the worker run before the plan row existed."""
    order = []
    db = AsyncMock()
    db.commit.side_effect = lambda: order.append("commit")

    plan = MagicMock(id=uuid.uuid4())
    mocker.patch.object(service_module.lesson_plan_repo, "create", new_callable=AsyncMock, return_value=plan)
    apply_async = mocker.patch(
        "app.tasks.generation_tasks.generate_lesson_plan_task.apply_async",
        side_effect=lambda *a, **k: order.append("dispatch"),
    )

    user_id = uuid.uuid4()
    job_id, plan_id = await lesson_plan_service.trigger_generation(
        db, user_id, LessonPlanCreate(grade_level="9", subject="Biologi", topic="Sel")
    )

    assert order == ["commit", "dispatch"]
    assert plan_id == plan.id
    kwargs = apply_async.call_args.kwargs
    assert kwargs["task_id"] == job_id
    assert kwargs["args"] == [str(plan.id), str(user_id)]
    created = service_module.lesson_plan_repo.create.call_args[0][1]
    assert created["job_id"] == job_id and created["status"] == "pending"


async def test_the_teachers_options_and_the_prompt_version_are_stored_on_the_plan(mocker):
    db = AsyncMock()
    mocker.patch.object(service_module.lesson_plan_repo, "create", new_callable=AsyncMock, return_value=MagicMock(id=uuid.uuid4()))
    mocker.patch("app.tasks.generation_tasks.generate_lesson_plan_task.apply_async")

    await lesson_plan_service.trigger_generation(
        db, uuid.uuid4(),
        LessonPlanCreate(
            grade_level="9", subject="IPS", topic="Ekonomi", meeting_count=3, minutes_per_meeting=90,
            teaching_model=TeachingModel.PJBL, class_notes="kelas aktif",
        ),
    )

    created = service_module.lesson_plan_repo.create.call_args[0][1]
    assert created["request_options"] == {
        "meeting_count": 3, "minutes_per_meeting": 90, "teaching_model": "pjbl", "class_notes": "kelas aktif",
    }
    assert created["prompt_version"] == settings.prompt_version
    assert created["model_name"] == settings.gemini_generation_model


# --- editing -------------------------------------------------------------------------------------------------------

async def test_a_valid_edit_to_a_module_is_saved(repo):
    content = stored_content()
    content["title"] = "Judul yang disunting guru"
    content["meetings"][0]["activities"]["rows"][0][2] = "Kegiatan baru"

    updated = await lesson_plan_service.update_content(AsyncMock(), repo.id, USER_ID, content)

    assert updated.generated_content["title"] == "Judul yang disunting guru"
    assert updated.generated_content["meetings"][0]["activities"]["rows"][0][2] == "Kegiatan baru"
    assert updated.generated_content["schema_version"] == 2


async def test_an_edit_that_breaks_a_table_is_refused_with_a_pointer_to_the_problem(repo):
    content = stored_content()
    content["meetings"][0]["activities"]["rows"][0].pop()

    with pytest.raises(InvalidContentError, match="meetings.0.activities"):
        await lesson_plan_service.update_content(AsyncMock(), repo.id, USER_ID, content)
    service_module.lesson_plan_repo.update.assert_not_awaited()


async def test_an_edit_that_drops_a_required_section_is_refused(repo):
    content = stored_content()
    del content["assessment"]

    with pytest.raises(InvalidContentError):
        await lesson_plan_service.update_content(AsyncMock(), repo.id, USER_ID, content)


async def test_old_format_plans_are_edited_as_before(repo):
    repo.schema_version = 1
    repo.generated_content = {"title": "Lama", "objectives": ["a"]}

    updated = await lesson_plan_service.update_content(AsyncMock(), repo.id, USER_ID, {"title": "Baru", "objectives": ["b"]})

    assert updated.generated_content == {"title": "Baru", "objectives": ["b"]}


async def test_only_completed_plans_can_be_edited(repo):
    repo.status = "processing"
    with pytest.raises(InvalidStateError):
        await lesson_plan_service.update_content(AsyncMock(), repo.id, USER_ID, stored_content())


# --- exporting -----------------------------------------------------------------------------------------------------

async def test_a_new_module_is_exported_with_the_module_renderer(repo, mocker):
    modul_pdf = mocker.patch.object(service_module, "generate_modul_pdf", return_value=b"%PDF-modul")
    old_pdf = mocker.patch.object(service_module, "generate_lesson_plan_pdf", return_value=b"%PDF-lama")

    data, filename = await lesson_plan_service.export_pdf(AsyncMock(), repo.id, USER_ID)

    assert data == b"%PDF-modul" and filename == "Modul_Ajar_Ekonomi.pdf"
    assert isinstance(modul_pdf.call_args.args[0], ModulContent)
    old_pdf.assert_not_called()


async def test_an_old_plan_is_still_exported_with_the_original_renderer(repo, mocker):
    repo.schema_version = 1
    repo.generated_content = {"title": "Lama"}
    modul_pdf = mocker.patch.object(service_module, "generate_modul_pdf")
    old_pdf = mocker.patch.object(service_module, "generate_lesson_plan_pdf", return_value=b"%PDF-lama")

    data, _ = await lesson_plan_service.export_pdf(AsyncMock(), repo.id, USER_ID)

    assert data == b"%PDF-lama"
    assert old_pdf.call_args.kwargs["plan_metadata"]["subject"] == "IPS"
    modul_pdf.assert_not_called()


async def test_export_needs_a_completed_plan(repo):
    repo.status = "failed"
    with pytest.raises(InvalidStateError):
        await lesson_plan_service.export_pdf(AsyncMock(), repo.id, USER_ID)


# --- job status ------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status,meta,expected_stage", [
    ("processing", {"stage": "drafting"}, "drafting"),
    ("processing", {"stage": "repairing"}, "repairing"),
    ("processing", None, None),
    ("pending", {"stage": "drafting"}, None),
    ("completed", {"retrieval": {}, "generation": {}}, None),
])
async def test_job_status_reports_the_stage_only_while_processing(mocker, status, meta, expected_stage):
    plan = make_plan(status=status, generation_meta=meta)
    mocker.patch.object(service_module.lesson_plan_repo, "get_by_job_id_and_user", new_callable=AsyncMock, return_value=plan)

    job = await lesson_plan_service.get_job_status(AsyncMock(), "job-1", USER_ID)

    assert job.status == status and job.stage == expected_stage


async def test_a_stuck_job_is_reported_failed_without_a_stage(mocker):
    plan = make_plan(
        status="processing", generation_meta={"stage": "drafting"},
        created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
    )
    mocker.patch.object(service_module.lesson_plan_repo, "get_by_job_id_and_user", new_callable=AsyncMock, return_value=plan)

    job = await lesson_plan_service.get_job_status(AsyncMock(), "job-1", USER_ID)

    assert job.status == "failed" and job.stage is None and "batas waktu" in job.error


async def test_a_failed_job_reports_its_error(mocker):
    plan = make_plan(status="failed", generated_content={"error": "Dokumen belum cukup."}, schema_version=1)
    mocker.patch.object(service_module.lesson_plan_repo, "get_by_job_id_and_user", new_callable=AsyncMock, return_value=plan)

    job = await lesson_plan_service.get_job_status(AsyncMock(), "job-1", USER_ID)

    assert job.status == "failed" and job.error == "Dokumen belum cukup."
