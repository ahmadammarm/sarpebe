import json
import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ContentBlockedError, InsufficientContextError, LLMOutputError
from app.core.llm_client import ModelResponse
from app.core.services import llm_service as module
from app.core.services.llm_service import STILL_INVALID_MESSAGE, llm_service
from app.schemas.lesson_plan_content import ModulContent
from tests.factories import activities_table, make_modul_dict, make_passage, make_request

async_test = pytest.mark.asyncio(loop_scope="session")
USER_ID = uuid.uuid4()
PLAN_ID = uuid.uuid4()


def reply(data=None, *, text=None, finish_reason="STOP", block_reason=None):
    body = text if text is not None else json.dumps(data if data is not None else make_modul_dict())
    return ModelResponse(text=body, finish_reason=finish_reason, block_reason=block_reason, prompt_tokens=1000, completion_tokens=2000)


def wrong_minutes(meeting_index: int = 1) -> dict:
    data = make_modul_dict()
    data["meetings"][meeting_index]["activities"] = activities_table(minutes=(15, 50, 10))  # adds up to 75
    return data


@pytest.fixture
def model(mocker):
    """Replaces the model call; set `.side_effect` to a list of replies."""
    return mocker.patch.object(module, "generate_structured", new_callable=AsyncMock)


async def generate(passages=None, request=None, on_stage=None):
    return await llm_service.generate_modul(
        request=request or make_request(),
        passages=passages or [make_passage("S1")],
        user_id=USER_ID,
        lesson_plan_id=PLAN_ID,
        on_stage=on_stage,
    )


# --- the normal path ------------------------------------------------------------------------------------------

@async_test
async def test_a_valid_answer_needs_one_call_and_becomes_stored_content(model):
    model.side_effect = [reply()]

    outcome = await generate()

    assert model.await_count == 1
    content = ModulContent.model_validate(outcome.content)
    assert content.schema_version == 2
    assert content.identity.subject == "IPS" and content.identity.meetings == 2 and content.identity.fase == "D"
    assert [r.id for r in content.references] == ["S1"]
    assert content.references[0].document_title == "CP IPS.pdf" and content.references[0].page == 14
    assert content.warnings == []
    assert outcome.meta["calls"] == 1 and outcome.meta["repaired"] is False
    assert outcome.meta["prompt_tokens"] == 1000 and outcome.meta["completion_tokens"] == 2000


@async_test
async def test_the_call_is_made_with_the_configured_model_instructions_and_schema(model):
    model.side_effect = [reply()]
    await generate()

    kwargs = model.await_args.kwargs
    assert kwargs["operation_type"] == "generation"
    assert kwargs["lesson_plan_id"] == PLAN_ID and kwargs["user_id"] == USER_ID
    assert kwargs["system_instruction"] == module.SYSTEM_INSTRUCTION
    assert kwargs["json_schema"] is module.MODUL_SCHEMA
    assert isinstance(kwargs["contents"], list) and "<sumber>" in kwargs["contents"][0]


@async_test
async def test_invented_source_ids_never_reach_the_stored_references(model):
    data = make_modul_dict()
    data["learning_objectives"][0]["source_ids"] = ["S1", "S42"]
    model.side_effect = [reply(data)]

    outcome = await generate([make_passage("S1")])

    assert outcome.content["learning_objectives"][0]["source_ids"] == ["S1"]
    assert [r["id"] for r in outcome.content["references"]] == ["S1"]
    assert outcome.meta["dropped_source_ids"] == 1


# --- repair ----------------------------------------------------------------------------------------------------------

@async_test
async def test_a_fixable_problem_triggers_exactly_one_repair_call_that_shows_the_problem(model):
    model.side_effect = [reply(wrong_minutes()), reply()]
    stages = []

    async def on_stage(stage):
        stages.append(stage)

    outcome = await generate(on_stage=on_stage)

    assert model.await_count == 2
    first, repair = model.await_args_list
    assert first.kwargs["operation_type"] == "generation" and repair.kwargs["operation_type"] == "repair"

    turns = repair.kwargs["contents"]
    assert [turn.role for turn in turns] == ["user", "model", "user"]
    assert "Pertemuan 2: total waktu kegiatan 75 menit, seharusnya 80 menit." in turns[2].parts[0].text
    assert json.loads(turns[1].parts[0].text)["meetings"][1]["activities"]["rows"][1][1] == "50"

    assert stages == ["repairing"]
    assert outcome.meta["repaired"] is True and outcome.meta["calls"] == 2 and outcome.meta["warnings"] == []
    assert outcome.content["warnings"] == []


@async_test
async def test_a_problem_that_survives_the_repair_is_kept_as_a_visible_warning(model):
    model.side_effect = [reply(wrong_minutes()), reply(wrong_minutes())]

    outcome = await generate()

    assert model.await_count == 2
    assert outcome.content["warnings"] == ["Pertemuan 2: total waktu kegiatan 75 menit, seharusnya 80 menit."]


@async_test
async def test_a_schema_violation_is_repaired_with_a_readable_list_of_errors(model):
    broken = make_modul_dict()
    broken["meetings"][0]["activities"]["rows"][0].pop()
    model.side_effect = [reply(broken), reply()]

    outcome = await generate()

    message = model.await_args_list[1].kwargs["contents"][2].parts[0].text
    assert "baris 1 punya 3 sel, seharusnya 4" in message
    assert outcome.meta["repaired"] is True


@async_test
async def test_unparseable_text_is_repaired_too(model):
    model.side_effect = [reply(text="ini bukan json"), reply()]
    outcome = await generate()
    assert outcome.meta["repaired"] is True


@async_test
async def test_two_unusable_answers_fail_with_a_clear_message(model):
    model.side_effect = [reply(text="bukan json"), reply(text="{}")]

    with pytest.raises(LLMOutputError) as error:
        await generate()

    assert error.value.message == STILL_INVALID_MESSAGE
    assert model.await_count == 2  # never a third call


@async_test
async def test_a_repair_that_makes_things_worse_does_not_discard_a_usable_first_answer(model):
    model.side_effect = [reply(wrong_minutes()), reply(text="rusak")]

    outcome = await generate()

    assert outcome.content["warnings"] == ["Pertemuan 2: total waktu kegiatan 75 menit, seharusnya 80 menit."]


@async_test
async def test_a_hard_problem_that_survives_the_repair_fails(model):
    two_meetings_for_three = make_modul_dict(meetings=2)
    model.side_effect = [reply(two_meetings_for_three), reply(two_meetings_for_three)]

    with pytest.raises(LLMOutputError):
        await generate(request=make_request(meeting_count=3))


# --- refusing to write from nothing -----------------------------------------------------------------------------------

@async_test
async def test_an_abstaining_model_stops_the_pipeline_with_its_reason(model):
    abstain = make_modul_dict(meetings=0, insufficient_context=True, insufficient_reason="Sumber tidak memuat ekonomi.")
    abstain["learning_objectives"] = []
    model.side_effect = [reply(abstain)]

    with pytest.raises(InsufficientContextError, match="Sumber tidak memuat ekonomi."):
        await generate()
    assert model.await_count == 1  # an honest "no" is not repaired


@async_test
async def test_an_abstention_without_a_reason_uses_the_standard_message(model):
    abstain = make_modul_dict(meetings=0, insufficient_context=True, insufficient_reason="  ")
    abstain["learning_objectives"] = []
    model.side_effect = [reply(abstain)]

    with pytest.raises(InsufficientContextError, match="belum membahas topik ini"):
        await generate()


@async_test
async def test_a_blocked_or_truncated_answer_is_not_repaired(model):
    model.side_effect = [reply(finish_reason="SAFETY")]
    with pytest.raises(ContentBlockedError):
        await generate()

    model.side_effect = [reply(text='{"title": "terpotong', finish_reason="MAX_TOKENS")]
    with pytest.raises(LLMOutputError, match="terpotong"):
        await generate()
    assert model.await_count == 2  # one call each, no repair attempts
