from typing import Sequence

from app.core.services.retrieval.types import Passage
from app.db.repositories.document_chunk_repository import ScoredChunk

MIN_RERANK_SCORE = 2  # "partial" or better


def choose_passages(
    candidates: Sequence[ScoredChunk],
    scores: dict[int, int] | None,
    *,
    top_k: int,
    max_chars: int,
    min_rerank_score: int = MIN_RERANK_SCORE,
) -> list[Passage]:
    """
    Picks the passages the model will see and gives them their ids (S1, S2, ...).

    With rerank scores, only candidates scored `min_rerank_score` or more are kept, best first (ties
    keep their fused order). Without them (rerank off or failed), the first `top_k` candidates are
    kept. The total text is capped at `max_chars` so the prompt size stays predictable.
    An empty result means nothing relevant was found.
    """
    if scores is None:
        order = list(range(len(candidates)))
    else:
        order = sorted(
            (i for i in range(len(candidates)) if scores.get(i, 0) >= min_rerank_score),
            key=lambda i: (-scores[i], i),
        )

    passages: list[Passage] = []
    used = 0
    for position in order[:top_k]:
        candidate = candidates[position]
        chunk = candidate.chunk
        text = chunk.chunk_content

        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(text) > remaining:
            if passages:
                break  # keep whole passages; the next one does not fit
            text = text[:remaining].rstrip()  # a single huge passage is cut rather than dropped

        passages.append(Passage(
            id=f"S{len(passages) + 1}",
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_title=chunk.document.title if chunk.document else "Dokumen kurikulum",
            page=chunk.page_number,
            page_end=chunk.page_end,
            heading=chunk.heading,
            text=text,
            similarity=candidate.similarity,
            rerank_score=scores.get(position) if scores is not None else None,
            chunk_type=chunk.chunk_type or "text",
        ))
        used += len(text)
    return passages
