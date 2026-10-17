import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from google.genai import errors as genai_errors
from tenacity import wait_none

from app.config import settings
from app.core import llm_client
from app.core.exceptions import ContentBlockedError, LLMOutputError, TransientLLMError
from app.core.llm_client import ModelResponse, call_with_retry, ensure_usable, generate_structured, is_transient

async_test = pytest.mark.asyncio(loop_scope="session")
USER_ID = uuid.uuid4()


def api_error(code: int) -> genai_errors.APIError:
    return genai_errors.APIError(code, {"error": {"message": f"status {code}"}})


@pytest.fixture(autouse=True)
def no_waiting(mocker):
    mocker.patch.object(llm_client, "wait_exponential_jitter", lambda **kwargs: wait_none())


# --- what counts as transient --------------------------------------------------------------------------

@pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504])
def test_rate_limits_and_server_errors_are_transient(code):
    assert is_transient(api_error(code))


@pytest.mark.parametrize("code", [400, 401, 403, 404, 422])
def test_client_errors_are_not_transient(code):
    assert not is_transient(api_error(code))


def test_timeouts_and_dropped_connections_are_transient():
    assert is_transient(asyncio.TimeoutError())
    assert is_transient(TimeoutError())
    assert is_transient(ConnectionError())
    assert is_transient(httpx.ConnectTimeout("slow"))
    assert is_transient(httpx.ReadError("dropped"))


def test_ordinary_bugs_are_not_transient():
    assert not is_transient(ValueError("bug"))
    assert not is_transient(KeyError("x"))


# --- retries -----------------------------------------------------------------------------------------------

@async_test
async def test_a_transient_error_is_retried_until_it_succeeds(mocker):
    mocker.patch.object(settings, "llm_max_attempts", 3)
    call = AsyncMock(side_effect=[api_error(429), api_error(503), "ok"])
    assert await call_with_retry(call) == "ok"
    assert call.await_count == 3


@async_test
async def test_retries_stop_at_the_limit_and_become_a_transient_llm_error(mocker):
    mocker.patch.object(settings, "llm_max_attempts", 3)
    call = AsyncMock(side_effect=api_error(429))
    with pytest.raises(TransientLLMError):
        await call_with_retry(call)
    assert call.await_count == 3


@async_test
async def test_a_permanent_error_is_not_retried_and_keeps_its_type(mocker):
    mocker.patch.object(settings, "llm_max_attempts", 3)
    call = AsyncMock(side_effect=api_error(400))
    with pytest.raises(genai_errors.APIError):
        await call_with_retry(call)
    assert call.await_count == 1

    bug = AsyncMock(side_effect=ValueError("bug"))
    with pytest.raises(ValueError):
        await call_with_retry(bug)
    assert bug.await_count == 1


# --- reading a response -------------------------------------------------------------------------------------

def response(text='{"a": 1}', finish_reason="STOP", block_reason=None):
    return ModelResponse(text=text, finish_reason=finish_reason, block_reason=block_reason, prompt_tokens=1, completion_tokens=1)


def test_a_normal_response_returns_its_text():
    assert ensure_usable(response()) == '{"a": 1}'


@pytest.mark.parametrize("reason", ["SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"])
def test_blocked_finish_reasons_raise_content_blocked(reason):
    with pytest.raises(ContentBlockedError):
        ensure_usable(response(finish_reason=reason))


def test_a_prompt_block_raises_content_blocked():
    with pytest.raises(ContentBlockedError):
        ensure_usable(response(text="", finish_reason=None, block_reason="PROHIBITED_CONTENT"))


def test_a_truncated_response_is_never_returned_as_if_complete():
    with pytest.raises(LLMOutputError, match="terpotong"):
        ensure_usable(response(text='{"title": "belum selesai', finish_reason="MAX_TOKENS"))


@pytest.mark.parametrize("text", ["", "   \n"])
def test_an_empty_response_raises(text):
    with pytest.raises(LLMOutputError):
        ensure_usable(response(text=text))


# --- generate_structured -------------------------------------------------------------------------------------

def fake_api_response(text='{"ok": true}', *, prompt=100, candidates=40, thoughts=60, finish="STOP", block=None):
    return SimpleNamespace(
        text=text,
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt, candidates_token_count=candidates, thoughts_token_count=thoughts
        ),
        candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name=finish))] if finish else [],
        prompt_feedback=SimpleNamespace(block_reason=SimpleNamespace(name=block)) if block else None,
    )


def install_client(mocker, api_response):
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=api_response)
    mocker.patch.object(llm_client, "client", client)
    mocker.patch.object(llm_client, "log_cost", new_callable=AsyncMock)
    return client


@async_test
async def test_generate_structured_sends_instructions_schema_and_options(mocker):
    client = install_client(mocker, fake_api_response())
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}

    await generate_structured(
        model="m", system_instruction="ATURAN", contents="DATA", json_schema=schema,
        operation_type="generation", user_id=USER_ID, temperature=0.4, thinking_level="MEDIUM",
        max_output_tokens=2000, seed=7,
    )

    kwargs = client.aio.models.generate_content.await_args.kwargs
    config = kwargs["config"]
    assert kwargs["model"] == "m" and kwargs["contents"] == "DATA"
    assert config.system_instruction == "ATURAN"
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == schema
    assert (config.temperature, config.max_output_tokens, config.seed) == (0.4, 2000, 7)
    assert config.thinking_config.thinking_level.name == "MEDIUM"


@async_test
async def test_optional_settings_are_left_out_when_not_given(mocker):
    client = install_client(mocker, fake_api_response())
    await generate_structured(
        model="m", system_instruction="A", contents="D", json_schema={}, operation_type="rerank", user_id=USER_ID,
    )
    config = client.aio.models.generate_content.await_args.kwargs["config"]
    assert config.temperature is None and config.thinking_config is None
    assert config.max_output_tokens is None and config.seed is None


@async_test
async def test_cost_is_logged_with_thinking_tokens_counted_as_output(mocker):
    install_client(mocker, fake_api_response(prompt=100, candidates=40, thoughts=60))
    plan_id = uuid.uuid4()

    result = await generate_structured(
        model="m", system_instruction="A", contents="D", json_schema={},
        operation_type="repair", user_id=USER_ID, lesson_plan_id=plan_id,
    )

    assert (result.prompt_tokens, result.completion_tokens) == (100, 100)
    logged = llm_client.log_cost.await_args.kwargs
    assert logged["operation_type"] == "repair" and logged["lesson_plan_id"] == plan_id
    assert (logged["prompt_tokens"], logged["completion_tokens"]) == (100, 100)


@async_test
async def test_finish_and_block_reasons_are_reported(mocker):
    install_client(mocker, fake_api_response(finish="MAX_TOKENS"))
    result = await generate_structured(
        model="m", system_instruction="A", contents="D", json_schema={}, operation_type="generation", user_id=USER_ID,
    )
    assert result.finish_reason == "MAX_TOKENS" and result.block_reason is None

    install_client(mocker, fake_api_response(text=None, finish=None, block="SAFETY"))
    blocked = await generate_structured(
        model="m", system_instruction="A", contents="D", json_schema={}, operation_type="generation", user_id=USER_ID,
    )
    assert blocked.block_reason == "SAFETY" and blocked.text == ""


@async_test
async def test_a_response_without_usage_metadata_logs_zero_tokens(mocker):
    api_response = fake_api_response()
    api_response.usage_metadata = None
    install_client(mocker, api_response)
    result = await generate_structured(
        model="m", system_instruction="A", contents="D", json_schema={}, operation_type="generation", user_id=USER_ID,
    )
    assert (result.prompt_tokens, result.completion_tokens) == (0, 0)
