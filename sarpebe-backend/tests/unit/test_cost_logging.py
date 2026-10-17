import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.core.services import cost_logging
from app.db.models.llm_cost_log import LLMCostLog

pytestmark = pytest.mark.asyncio(loop_scope="session")

async def test_log_cost_commits_in_its_own_session(mocker):
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    mocker.patch.object(cost_logging, "get_session_factory", return_value=lambda: session_cm)

    user_id, plan_id = uuid.uuid4(), uuid.uuid4()
    cost = await cost_logging.log_cost(
        model_name="gemini-2.5-flash-lite",
        operation_type="generation",
        user_id=user_id,
        lesson_plan_id=plan_id,
        prompt_tokens=1000,
        completion_tokens=500,
    )

    session.commit.assert_awaited_once()
    logged = session.add.call_args[0][0]
    assert isinstance(logged, LLMCostLog)
    assert logged.user_id == user_id and logged.lesson_plan_id == plan_id
    assert logged.operation_type == "generation"
    assert float(logged.total_cost) == cost > 0
