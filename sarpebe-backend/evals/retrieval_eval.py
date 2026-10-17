"""
Measures retrieval quality on the evaluation set, using the same candidate gathering and reranking as
production (app.core.services.retrieval).

For on-topic ("positive") queries it compares four rankings, so each added stage has to prove it helps:
vector only, keyword only, hybrid (reciprocal rank fusion), hybrid + rerank. For all queries it records
the best cosine similarity, from which the similarity floor is chosen, and whether the reranker found
anything relevant, which measures how well off-topic queries are rejected.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.services.embedding_service import embedding_service
from app.core.services.retrieval.candidates import gather_candidates
from app.core.services.retrieval.passages import MIN_RERANK_SCORE
from app.core.services.retrieval.query import build_query
from app.core.services.retrieval.rerank import rerank_candidates
from app.db.repositories.document_chunk_repository import ScoredChunk
from evals.dataset import Example
from evals.metrics import best_threshold, chunk_matches, summarize_rankings, threshold_sweep

THRESHOLDS = [round(0.30 + 0.05 * step, 2) for step in range(11)]  # 0.30 .. 0.80


def _relevance(example: Example, hits: list[ScoredChunk], k: int) -> list[bool]:
    return [
        chunk_matches(example.gold, str(hit.chunk.document_id), hit.chunk.page_number, hit.chunk.page_end)
        for hit in hits[:k]
    ]


async def evaluate_retrieval(
    db: AsyncSession,
    examples: list[Example],
    user_id: UUID,
    *,
    k: int = 6,
) -> dict:
    rankings: dict[str, list[list[bool]]] = {"vector": [], "keyword": [], "hybrid": [], "hybrid+rerank": []}
    positive_scores: list[float] = []
    negative_scores: list[float] = []
    rerank_found_nothing = {"positive": 0, "negative": 0}
    rerank_failures = 0
    counts = {"positive": 0, "negative": 0}

    for example in examples:
        query = build_query(example.topic, example.grade_level, example.subject)
        embedding = await embedding_service.embed_text(query, user_id, purpose="query")
        candidates = await gather_candidates(
            db,
            embedding=embedding,
            topic=example.topic,
            grade_level=example.grade_level,
            subject=example.subject,
            limit=settings.rag_candidate_k,
        )
        counts[example.kind] += 1

        # The best similarity decides the floor, independent of any reranking.
        best = max((hit.similarity for hit in candidates.fused), default=0.0)
        (positive_scores if example.kind == "positive" else negative_scores).append(best)

        shortlist = list(candidates.fused[: settings.rag_rerank_shortlist])
        scores = await rerank_candidates(query, shortlist, user_id=user_id) if shortlist else {}
        if scores is None:
            rerank_failures += 1
            scores = {}
        elif shortlist and not any(score >= MIN_RERANK_SCORE for score in scores.values()):
            rerank_found_nothing[example.kind] += 1

        if example.kind != "positive":
            continue

        reranked = sorted(range(len(shortlist)), key=lambda i: (-scores.get(i, 0), i))
        rankings["vector"].append(_relevance(example, list(candidates.vector_hits), k))
        rankings["keyword"].append(_relevance(example, list(candidates.keyword_hits), k))
        rankings["hybrid"].append(_relevance(example, list(candidates.fused), k))
        rankings["hybrid+rerank"].append(_relevance(example, [shortlist[i] for i in reranked], k))

    sweep = threshold_sweep(positive_scores, negative_scores, THRESHOLDS)
    return {
        "k": k,
        "examples": counts,
        "ranking": {name: summarize_rankings(values, ks=(1, 3, k)) for name, values in rankings.items()},
        "similarity_floor": {
            "current": settings.rag_min_similarity,
            "sweep": sweep,
            "suggested": best_threshold(sweep),
        },
        "rerank_abstention": {
            "positives_rejected": _share(rerank_found_nothing["positive"], counts["positive"]),
            "negatives_rejected": _share(rerank_found_nothing["negative"], counts["negative"]),
            "failed_calls": rerank_failures,
        },
    }


def _share(part: int, whole: int) -> float:
    return round(part / whole, 4) if whole else 0.0
