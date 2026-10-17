import uuid
import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

from app.db.models.lesson_plan import LessonPlan
from app.tasks import generation_tasks

pytestmark = pytest.mark.asyncio(loop_scope="session")

class FakeSession:
    def __init__(self):
        self.commit = AsyncMock()
    async def __aenter__(self):
        return self
    async def __aexit__(self, *exc):
        return False

@pytest.fixture
def plan():
    return LessonPlan(
        id=uuid.uuid4(), user_id=uuid.uuid4(), grade_level="10", subject="Biologi",
        topic="Sel Hewan", status="pending",
    )

@pytest.fixture
def wired(mocker, plan):
    session = FakeSession()

    @asynccontextmanager
    async def fake_scope():
        yield lambda: session

    mocker.patch.object(generation_tasks, "task_session_scope", fake_scope)
    mocker.patch.object(generation_tasks.lesson_plan_repo, "get", new_callable=AsyncMock, return_value=plan)
    return session

async def test_no_context_fails_plan_without_calling_llm(mocker, wired, plan):
    mocker.patch.object(generation_tasks.rag_service, "retrieve_context", new_callable=AsyncMock, return_value=[])
    llm = mocker.patch.object(generation_tasks.llm_service, "generate_lesson_plan", new_callable=AsyncMock)

    await generation_tasks._run_generation(str(plan.id), str(plan.user_id), is_final_attempt=False)

    llm.assert_not_called()
    assert plan.status == "failed"
    assert plan.generated_content == {"error": generation_tasks.NO_CONTEXT_ERROR}

async def test_success_marks_completed(mocker, wired, plan):
    mocker.patch.object(generation_tasks.rag_service, "retrieve_context", new_callable=AsyncMock, return_value=[MagicMock()])
    mocker.patch.object(
        generation_tasks.llm_service, "generate_lesson_plan",
        new_callable=AsyncMock, return_value={"title": "T", "citations": ["doc p.1"]},
    )

    await generation_tasks._run_generation(str(plan.id), str(plan.user_id), is_final_attempt=False)

    assert plan.status == "completed"
    assert plan.generated_content["title"] == "T"

async def test_llm_error_payload_marks_failed_without_raising(mocker, wired, plan):
    mocker.patch.object(generation_tasks.rag_service, "retrieve_context", new_callable=AsyncMock, return_value=[MagicMock()])
    mocker.patch.object(
        generation_tasks.llm_service, "generate_lesson_plan",
        new_callable=AsyncMock, return_value={"error": "Failed to parse structured JSON from Gemini"},
    )

    await generation_tasks._run_generation(str(plan.id), str(plan.user_id), is_final_attempt=False)

    assert plan.status == "failed"

async def test_transient_error_is_raised_for_retry_and_plan_not_failed(mocker, wired, plan):
    mocker.patch.object(generation_tasks.rag_service, "retrieve_context", new_callable=AsyncMock, side_effect=RuntimeError("429"))

    with pytest.raises(RuntimeError):
        await generation_tasks._run_generation(str(plan.id), str(plan.user_id), is_final_attempt=False)

    assert plan.status == "processing"

async def test_final_attempt_marks_failed_instead_of_raising(mocker, wired, plan):
    mocker.patch.object(generation_tasks.rag_service, "retrieve_context", new_callable=AsyncMock, side_effect=RuntimeError("429"))

    await generation_tasks._run_generation(str(plan.id), str(plan.user_id), is_final_attempt=True)

    assert plan.status == "failed"
    assert "429" in plan.generated_content["error"]
