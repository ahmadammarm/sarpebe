import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.services import lesson_plan_service as service_module
from app.core.services.lesson_plan_service import lesson_plan_service
from app.schemas.lesson_plan import LessonPlanCreate

pytestmark = pytest.mark.asyncio(loop_scope="session")

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
        db, user_id, LessonPlanCreate(grade_level="10", subject="Biologi", topic="Sel")
    )

    assert order == ["commit", "dispatch"]
    assert plan_id == plan.id
    kwargs = apply_async.call_args.kwargs
    assert kwargs["task_id"] == job_id
    assert kwargs["args"] == [str(plan.id), str(user_id)]
    created = service_module.lesson_plan_repo.create.call_args[0][1]
    assert created["job_id"] == job_id and created["status"] == "pending"
