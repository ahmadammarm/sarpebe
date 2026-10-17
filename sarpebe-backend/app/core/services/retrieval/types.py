from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Passage:
    """A piece of curriculum text handed to the model, with a stable id it must cite."""

    id: str  # "S1", "S2", ... in the order the model sees them
    chunk_id: UUID
    document_id: UUID
    document_title: str
    page: int | None
    page_end: int | None
    heading: str | None
    text: str
    similarity: float
    rerank_score: int | None
    chunk_type: str = "text"


@dataclass
class RetrievalResult:
    passages: list[Passage]
    # What happened, for traceability (stored in lesson_plans.generation_meta).
    stats: dict[str, Any] = field(default_factory=dict)
