"""
The one place that talks to Gemini for text generation.

Every call goes through here so that all of them get the same behavior: retries only for
transient failures, a clear error when the output is blocked or cut off, and a cost row in
llm_cost_logs (including rerank and repair calls).
"""
import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar
from uuid import UUID

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from app.config import settings
from app.core.exceptions import ContentBlockedError, LLMOutputError, TransientLLMError
from app.core.services.cost_logging import log_cost

client = genai.Client(api_key=settings.gemini_api_key)

TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
BLOCKED_FINISH_REASONS = {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"}

T = TypeVar("T")


def is_transient(exc: BaseException) -> bool:
    """True for failures worth retrying: rate limits, server errors, timeouts, dropped connections."""
    if isinstance(exc, genai_errors.APIError):
        return exc.code in TRANSIENT_STATUS_CODES
    return isinstance(
        exc,
        (asyncio.TimeoutError, TimeoutError, ConnectionError, httpx.TimeoutException, httpx.TransportError),
    )


async def call_with_retry(call: Callable[[], Awaitable[T]]) -> T:
    """
    Runs a model API call, retrying transient errors with exponential backoff and jitter.
    Anything else (bad request, auth, a bug) fails immediately: retrying cannot fix it, and it
    would only multiply the cost. Exhausted transient errors become TransientLLMError.
    """
    result: T
    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(settings.llm_max_attempts),
            wait=wait_exponential_jitter(initial=2, max=20),
            retry=retry_if_exception(is_transient),
            reraise=True,
        ):
            with attempt:
                result = await call()
        return result
    except Exception as exc:
        if is_transient(exc):
            raise TransientLLMError("Layanan model sedang sibuk. Coba lagi sebentar lagi.") from exc
        raise


@dataclass(frozen=True)
class ModelResponse:
    text: str
    finish_reason: str | None
    block_reason: str | None
    prompt_tokens: int
    completion_tokens: int  # includes thinking tokens, which are billed as output


async def generate_structured(
    *,
    model: str,
    system_instruction: str,
    contents: Any,
    json_schema: dict[str, Any],
    operation_type: str,
    user_id: UUID,
    lesson_plan_id: UUID | None = None,
    temperature: float | None = None,
    thinking_level: str | None = None,
    max_output_tokens: int | None = None,
    seed: int | None = None,
) -> ModelResponse:
    """
    One model call that must answer with JSON matching `json_schema`.
    Instructions go in `system_instruction`; `contents` carries only the data for this request.
    The cost is logged right after the response, whatever the caller does with it.
    """
    config_args: dict[str, Any] = {
        "system_instruction": system_instruction,
        "response_mime_type": "application/json",
        "response_json_schema": json_schema,
    }
    if temperature is not None:
        config_args["temperature"] = temperature
    if max_output_tokens is not None:
        config_args["max_output_tokens"] = max_output_tokens
    if seed is not None:
        config_args["seed"] = seed
    if thinking_level is not None:
        config_args["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level)
    config = types.GenerateContentConfig(**config_args)

    response = await call_with_retry(
        lambda: client.aio.models.generate_content(model=model, contents=contents, config=config)
    )

    usage = response.usage_metadata
    prompt_tokens = (usage.prompt_token_count or 0) if usage else 0
    completion_tokens = ((usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)) if usage else 0
    await log_cost(
        model_name=model,
        operation_type=operation_type,
        user_id=user_id,
        lesson_plan_id=lesson_plan_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    candidate = response.candidates[0] if response.candidates else None
    finish_reason = candidate.finish_reason.name if candidate is not None and candidate.finish_reason else None
    feedback = response.prompt_feedback
    block_reason = feedback.block_reason.name if feedback is not None and feedback.block_reason else None

    return ModelResponse(
        text=response.text or "",
        finish_reason=finish_reason,
        block_reason=block_reason,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )


def ensure_usable(response: ModelResponse) -> str:
    """
    Returns the response text, or raises a specific error when it cannot be trusted:
    blocked by a safety filter, cut off at the token limit, or empty.
    """
    if response.block_reason or response.finish_reason in BLOCKED_FINISH_REASONS:
        raise ContentBlockedError(
            "Permintaan ditolak oleh filter keamanan model. Ubah topik atau catatan kelas, lalu coba lagi."
        )
    if response.finish_reason == "MAX_TOKENS":
        raise LLMOutputError(
            "Keluaran model terpotong sebelum selesai. Coba lagi, atau kurangi jumlah pertemuan."
        )
    if not response.text.strip():
        raise LLMOutputError("Model tidak menghasilkan jawaban. Coba lagi.")
    return response.text
