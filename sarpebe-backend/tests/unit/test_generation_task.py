import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.core.exceptions import (
    ContentBlockedError,
    InsufficientContextError,
    LLMOutputError,
    TransientLLMError,
)
from app.core.services.llm_service import GenerationOutcome
from app.core.services.retrieval.types import RetrievalResult
from app.db.models.lesson_plan import LessonPlan
from app.tasks import generation_tasks
from tests.factories import make_modul_dict, make_passage

async_test = pytest.mark.asyncio(loop_scope="session")


class FakeSession:
    def __init__(self, on_commit):
        self.commit = AsyncMock(side_effect=on_commit)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


@pytest.fixture
def plan():
    return LessonPlan(
        id=uuid.uuid4(), user_id=uuid.uuid4(), grade_level="9", subject="IPS", topic="Pelaku ekonomi",
        status="pending", schema_version=1,
        request_options={"meeting_count": 2, "minutes_per_meeting": 80, "teaching_model": "pjbl", "class_notes": "kelas aktif"},
    )


@pytest.fixture
def pipeline(mocker, plan):
    """Wires the task to fakes; `snapshots` records (status, stage) at every commit."""
    snapshots = []
    session = FakeSession(lambda: snapshots.append((plan.status, (plan.generation_meta or {}).get("stage"))))

    @asynccontextmanager
    async def fake_scope():
        yield lambda: session

    outcome = GenerationOutcome(content={"schema_version": 2, "title": "Modul"}, meta={"calls": 1, "repaired": False})
    retrieval = RetrievalResult(passages=[make_passage("S1")], stats={"kept": 1, "top_similarity": 0.8})

    mocker.patch.object(generation_tasks, "task_session_scope", fake_scope)
    mocker.patch.object(generation_tasks.lesson_plan_repo, "get", new_callable=AsyncMock, return_value=plan)
    retrieve = mocker.patch.object(generation_tasks.rag_service, "retrieve_context", new_callable=AsyncMock, return_value=retrieval)
    generate = mocker.patch.object(generation_tasks.llm_service, "generate_modul", new_callable=AsyncMock, return_value=outcome)
    return type("Pipeline", (), {"snapshots": snapshots, "retrieve": retrieve, "generate": generate, "outcome": outcome})


async def run(plan, final=False):
    await generation_tasks._run_generation(str(plan.id), str(plan.user_id), is_final_attempt=final)


# --- success ---------------------------------------------------------------------------------------------------

@async_test
async def test_success_stores_the_module_with_its_provenance(pipeline, plan):
    await run(plan)

    assert plan.status == "completed"
    assert plan.generated_content == pipeline.outcome.content
    assert plan.schema_version == 2
    assert plan.prompt_version == settings.prompt_version
    assert plan.model_name == settings.gemini_generation_model
    assert plan.generation_meta == {
        "retrieval": {"kept": 1, "top_similarity": 0.8},
        "generation": {"calls": 1, "repaired": False},
    }


@async_test
async def test_the_stage_is_saved_before_each_step(pipeline, plan):
    await run(plan)

    assert pipeline.snapshots == [
        ("processing", "retrieving"),
        ("processing", "drafting"),
        ("completed", None),
    ]


@async_test
async def test_a_repair_is_reported_as_a_stage(pipeline, plan):
    async def generate(**kwargs):
        await kwargs["on_stage"]("repairing")
        return pipeline.outcome

    pipeline.generate.side_effect = generate
    await run(plan)

    assert ("processing", "repairing") in pipeline.snapshots


@async_test
async def test_the_request_is_built_from_what_the_teacher_asked_for(pipeline, plan):
    await run(plan)

    request = pipeline.generate.await_args.kwargs["request"]
    assert (request.grade_level, request.fase, request.subject, request.topic) == ("9", "D", "IPS", "Pelaku ekonomi")
    assert (request.meeting_count, request.minutes_per_meeting) == (2, 80)
    assert (request.teaching_model, request.class_notes) == ("pjbl", "kelas aktif")
    assert pipeline.generate.await_args.kwargs["passages"] == pipeline.retrieve.return_value.passages


@async_test
async def test_retrieval_is_given_the_labels_and_the_plan_for_cost_tracking(pipeline, plan):
    await run(plan)

    kwargs = pipeline.retrieve.await_args.kwargs
    assert (kwargs["topic"], kwargs["grade_level"], kwargs["subject"]) == ("Pelaku ekonomi", "9", "IPS")
    assert kwargs["lesson_plan_id"] == plan.id and kwargs["user_id"] == plan.user_id


@async_test
async def test_a_plan_without_options_gets_the_defaults(pipeline, plan):
    plan.request_options = None
    await run(plan)
    request = pipeline.generate.await_args.kwargs["request"]
    assert (request.meeting_count, request.minutes_per_meeting, request.teaching_model) == (1, 80, "otomatis")


@async_test
async def test_a_completed_plan_is_not_generated_again(pipeline, plan):
    plan.status = "completed"
    await run(plan)
    pipeline.retrieve.assert_not_awaited()
    pipeline.generate.assert_not_awaited()


@async_test
async def test_a_deleted_plan_is_ignored(pipeline, plan, mocker):
    mocker.patch.object(generation_tasks.lesson_plan_repo, "get", new_callable=AsyncMock, return_value=None)
    await run(plan)
    pipeline.retrieve.assert_not_awaited()


# --- failures that repeating cannot fix -----------------------------------------------------------------------------

@async_test
async def test_nothing_relevant_in_the_documents_fails_without_calling_the_model(pipeline, plan):
    pipeline.retrieve.side_effect = InsufficientContextError("Dokumen kurikulum yang tersedia belum membahas topik ini.")

    await run(plan)  # must not raise, even on the first attempt: retrying cannot help

    pipeline.generate.assert_not_awaited()
    assert plan.status == "failed"
    assert plan.generated_content == {
        "error": "Dokumen kurikulum yang tersedia belum membahas topik ini.",
        "code": "insufficient_context",
    }


@async_test
async def test_insufficient_context_keeps_its_own_message_and_is_not_retried(pipeline, plan):
    pipeline.generate.side_effect = InsufficientContextError("Sumber tidak memuat topik ini.")

    await run(plan, final=False)

    assert plan.status == "failed"
    assert plan.generated_content == {"error": "Sumber tidak memuat topik ini.", "code": "insufficient_context"}
    assert plan.generation_meta == {"failed": True}


@pytest.mark.parametrize("error,code", [
    (LLMOutputError("raw model output: {...}"), "llm_output_invalid"),
    (ContentBlockedError("finish_reason=SAFETY"), "content_blocked"),
    (TransientLLMError("503 Service Unavailable from upstream"), "llm_unavailable"),
])
@async_test
async def test_other_model_failures_show_a_fixed_indonesian_message_not_the_exception_text(pipeline, plan, error, code):
    pipeline.generate.side_effect = error

    await run(plan, final=False)  # not retried: must not raise

    assert plan.status == "failed"
    assert plan.generated_content == {"error": generation_tasks.FAILURE_MESSAGES[type(error)], "code": code}
    assert error.message not in plan.generated_content["error"]
    assert plan.generation_meta == {"failed": True}


# --- unexpected failures ------------------------------------------------------------------------------------------------

@async_test
async def test_an_unexpected_error_is_raised_for_celery_to_retry_and_the_plan_stays_open(pipeline, plan):
    pipeline.retrieve.side_effect = RuntimeError("database connection reset")

    with pytest.raises(RuntimeError):
        await run(plan, final=False)

    assert plan.status == "processing"  # not failed yet: another attempt is coming


@async_test
async def test_an_unexpected_error_on_the_last_attempt_marks_the_plan_failed(pipeline, plan):
    pipeline.retrieve.side_effect = RuntimeError("database connection reset")

    await run(plan, final=True)

    assert plan.status == "failed"
    assert plan.generated_content == {"error": generation_tasks.INTERNAL_ERROR_MESSAGE, "code": "internal_error"}
    assert "database connection reset" not in str(plan.generated_content)


def test_celery_retries_infrastructure_faults_once():
    assert generation_tasks.MAX_RETRIES == 1
    assert generation_tasks.generate_lesson_plan_task.max_retries == 1
    assert generation_tasks.generate_lesson_plan_task.soft_time_limit < generation_tasks.generate_lesson_plan_task.time_limit
