"""Retrieval metrics. Pure functions: they take rankings and scores, never touch a database or a model."""
from typing import Sequence

DEFAULT_KS = (1, 3, 6)


def chunk_matches(
    gold: Sequence[tuple[str, int]],
    document_id: str,
    page: int | None,
    page_end: int | None = None,
) -> bool:
    """
    True if a chunk covers any gold (document_id, page). Chunks can span pages, so a gold page matches
    when it falls between the chunk's first and last page.
    """
    if page is None:
        return False
    last = page_end if page_end is not None else page
    return any(doc == document_id and page <= gold_page <= last for doc, gold_page in gold)


def first_hit_rank(ranked: Sequence[bool]) -> int | None:
    """1-based position of the first relevant result, or None if there is none."""
    for position, relevant in enumerate(ranked, start=1):
        if relevant:
            return position
    return None


def hit_at_k(ranked: Sequence[bool], k: int) -> bool:
    rank = first_hit_rank(ranked)
    return rank is not None and rank <= k


def reciprocal_rank(ranked: Sequence[bool]) -> float:
    rank = first_hit_rank(ranked)
    return 1.0 / rank if rank else 0.0


def summarize_rankings(rankings: Sequence[Sequence[bool]], ks: Sequence[int] = DEFAULT_KS) -> dict[str, float | int]:
    """hit@k for each k, and mean reciprocal rank, over a set of queries."""
    count = len(rankings)
    summary: dict[str, float | int] = {"queries": count}
    for k in ks:
        summary[f"hit@{k}"] = round(sum(hit_at_k(r, k) for r in rankings) / count, 4) if count else 0.0
    summary["mrr"] = round(sum(reciprocal_rank(r) for r in rankings) / count, 4) if count else 0.0
    return summary


def threshold_sweep(
    positive_scores: Sequence[float],
    negative_scores: Sequence[float],
    thresholds: Sequence[float],
) -> list[dict[str, float]]:
    """
    For each similarity floor: the share of on-topic queries that still get through (want high) and the
    share of off-topic queries that are rejected (want high). `*_scores` are each query's best
    similarity. The floor to choose is where both are acceptable.
    """
    rows = []
    for threshold in thresholds:
        kept = sum(score >= threshold for score in positive_scores)
        rejected = sum(score < threshold for score in negative_scores)
        rows.append({
            "threshold": threshold,
            "positives_kept": round(kept / len(positive_scores), 4) if positive_scores else 0.0,
            "negatives_rejected": round(rejected / len(negative_scores), 4) if negative_scores else 0.0,
        })
    return rows


def best_threshold(sweep: Sequence[dict[str, float]], min_positives_kept: float = 0.95) -> dict[str, float] | None:
    """
    The strictest floor that still keeps at least `min_positives_kept` of on-topic queries, preferring
    the one that rejects the most off-topic queries. None if no floor qualifies.
    """
    qualifying = [row for row in sweep if row["positives_kept"] >= min_positives_kept]
    if not qualifying:
        return None
    return max(qualifying, key=lambda row: (row["negatives_rejected"], row["threshold"]))
