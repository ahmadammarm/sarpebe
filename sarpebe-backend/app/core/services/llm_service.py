import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable
from uuid import UUID

from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.core.exceptions import InsufficientContextError, LLMOutputError
from app.core.llm_client import ensure_usable, generate_structured
from app.core.prompts.lesson_plan import (
    SYSTEM_INSTRUCTION,
    ModulRequest,
    build_repair_message,
    build_user_content,
)
from app.core.services.lesson_plan_checks import (
    CheckReport,
    build_references,
    check_modul,
    sanitize_sources,
)
from app.core.services.retrieval.types import Passage
from app.schemas.json_schema import to_gemini_schema
from app.schemas.lesson_plan_content import (
    GeneratedModul,
    Identity,
    ModulContent,
)

logger = logging.getLogger(__name__)

MODUL_SCHEMA = to_gemini_schema(GeneratedModul)

NOT_COVERED_MESSAGE = "Dokumen kurikulum yang tersedia belum membahas topik ini."
STILL_INVALID_MESSAGE = "Model belum menghasilkan modul yang valid, bahkan setelah diperbaiki. Coba buat ulang."

StageCallback = Callable[[str], Awaitable[None]]


@dataclass
class GenerationOutcome:
    content: dict[str, Any]  # ModulContent as JSON-ready data
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Attempt:
    modul: GeneratedModul | None
    text: str
    report: CheckReport | None = None
    schema_problems: list[str] = field(default_factory=list)

    @property
    def hard(self) -> list[str]:
        return self.schema_problems or (self.report.hard if self.report else [])

    @property
    def soft(self) -> list[str]:
        return self.report.soft if self.report and not self.schema_problems else []

    @property
    def problems(self) -> list[str]:
        return [*self.hard, *self.soft]


def describe_validation_errors(error: ValidationError, limit: int = 8) -> list[str]:
    """Readable problem lines for the repair prompt, e.g. "meetings.0.activities: baris 2 punya 3 sel"."""
    lines = []
    for item in error.errors()[:limit]:
        location = ".".join(str(part) for part in item["loc"]) or "dokumen"
        lines.append(f"{location}: {item['msg']}")
    return lines


class LLMService:
    @staticmethod
    async def generate_modul(
        *,
        request: ModulRequest,
        passages: list[Passage],
        user_id: UUID,
        lesson_plan_id: UUID | None,
        on_stage: StageCallback | None = None,
    ) -> GenerationOutcome:
        """
        Writes a Modul Ajar from the retrieved passages.

        One structured call; if the answer does not validate or fails the server-side checks, one
        repair call that shows the model its own output and the list of problems. Source ids the
        model invented are dropped and the reference list is built from the passages, so nothing
        in it can point at a page that was not retrieved.

        Raises InsufficientContextError if the model says the sources do not cover the topic, and
        LLMOutputError if the result is still unusable after the repair.
        """
        user_content = build_user_content(request, passages)
        valid_ids = {passage.id for passage in passages}
        totals = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}

        async def attempt(contents: Any, operation: str) -> _Attempt:
            response = await generate_structured(
                model=settings.gemini_generation_model,
                system_instruction=SYSTEM_INSTRUCTION,
                contents=contents,
                json_schema=MODUL_SCHEMA,
                operation_type=operation,
                user_id=user_id,
                lesson_plan_id=lesson_plan_id,
                temperature=settings.generation_temperature,
                thinking_level=settings.generation_thinking_level,
                max_output_tokens=settings.generation_max_output_tokens,
            )
            totals["prompt_tokens"] += response.prompt_tokens
            totals["completion_tokens"] += response.completion_tokens
            totals["calls"] += 1

            text = ensure_usable(response)
            try:
                modul = GeneratedModul.model_validate_json(text)
            except ValidationError as error:
                return _Attempt(modul=None, text=text, schema_problems=describe_validation_errors(error))

            if modul.insufficient_context:
                return _Attempt(modul=modul, text=text)

            dropped = sanitize_sources(modul, valid_ids)
            report = check_modul(modul, request)
            report.dropped_source_ids = dropped
            return _Attempt(modul=modul, text=text, report=report)

        first = await attempt([user_content], "generation")
        chosen = first
        repaired = False

        if not (first.modul and first.modul.insufficient_context) and first.problems:
            logger.info("Generated module needs repair: %s", first.problems)
            if on_stage:
                await on_stage("repairing")
            repaired = True
            chosen = await attempt(
                [
                    types.Content(role="user", parts=[types.Part(text=user_content)]),
                    types.Content(role="model", parts=[types.Part(text=first.text)]),
                    types.Content(role="user", parts=[types.Part(text=build_repair_message(first.problems))]),
                ],
                "repair",
            )

        # A repair that made things worse must not discard a first answer that was usable.
        first_is_usable = first.modul is not None and not first.hard and not first.modul.insufficient_context
        if repaired and (chosen.modul is None or chosen.hard) and first_is_usable:
            chosen = first

        if chosen.modul and chosen.modul.insufficient_context:
            raise InsufficientContextError(chosen.modul.insufficient_reason.strip() or NOT_COVERED_MESSAGE)

        if chosen.modul is None or chosen.hard:
            logger.warning("Module still invalid after repair: %s", chosen.problems)
            raise LLMOutputError(STILL_INVALID_MESSAGE)

        modul = chosen.modul
        report = chosen.report or CheckReport()
        warnings = list(chosen.soft)

        content = ModulContent(
            **modul.model_dump(),
            identity=Identity(
                subject=request.subject,
                grade_level=request.grade_level,
                fase=request.fase,
                topic=request.topic,
                meetings=request.meeting_count,
                minutes_per_meeting=request.minutes_per_meeting,
                teaching_model=request.teaching_model,
            ),
            references=build_references(modul, passages),
            warnings=warnings,
        )

        return GenerationOutcome(
            content=content.model_dump(mode="json"),
            meta={
                "calls": totals["calls"],
                "prompt_tokens": totals["prompt_tokens"],
                "completion_tokens": totals["completion_tokens"],
                "repaired": repaired,
                "dropped_source_ids": report.dropped_source_ids,
                "grounded_objectives": report.grounded_objectives,
                "total_objectives": report.total_objectives,
                "warnings": warnings,
            },
        )

llm_service = LLMService()
