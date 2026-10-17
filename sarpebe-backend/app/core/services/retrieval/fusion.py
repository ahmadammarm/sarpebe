from typing import Hashable, Sequence, TypeVar

K = TypeVar("K", bound=Hashable)


def reciprocal_rank_fusion(rankings: Sequence[Sequence[K]], k: int = 60) -> list[tuple[K, float]]:
    """
    Merges several ranked lists into one by summing 1 / (k + rank) for every list an item appears in.
    Needs no score calibration between the lists (cosine similarity and full-text rank are not
    comparable), and rewards items that several retrievers agree on. Ties keep first-seen order.
    """
    scores: dict[K, float] = {}
    for ranking in rankings:
        for rank, key in enumerate(ranking, start=1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
