import random
from types import SimpleNamespace

from evals.dataset import Example, load_examples, save_examples
from evals.generate_questions import MIN_CHUNK_CHARS, clean_topics, sample_chunks
from evals.metrics import (
    best_threshold,
    chunk_matches,
    first_hit_rank,
    hit_at_k,
    reciprocal_rank,
    summarize_rankings,
    threshold_sweep,
)
from evals.report import render_generation, write_report


def test_chunk_matches_uses_page_range():
    gold = [("doc", 5)]
    assert chunk_matches(gold, "doc", 5)
    assert chunk_matches(gold, "doc", 4, 6)
    assert not chunk_matches(gold, "doc", 6, 8)
    assert not chunk_matches(gold, "other", 5)
    assert not chunk_matches(gold, "doc", None)


def test_ranking_metrics():
    assert first_hit_rank([False, False, True]) == 3
    assert first_hit_rank([False]) is None
    assert hit_at_k([False, True], 1) is False
    assert hit_at_k([False, True], 2) is True
    assert reciprocal_rank([False, True]) == 0.5
    assert reciprocal_rank([False]) == 0.0


def test_summarize_rankings():
    summary = summarize_rankings([[True], [False, True], [False, False]], ks=(1, 2))
    assert summary["queries"] == 3
    assert summary["hit@1"] == round(1 / 3, 4)
    assert summary["hit@2"] == round(2 / 3, 4)
    assert summary["mrr"] == round((1 + 0.5 + 0) / 3, 4)
    assert summarize_rankings([], ks=(1,))["hit@1"] == 0.0


def test_threshold_sweep_and_best_threshold():
    sweep = threshold_sweep([0.8, 0.7, 0.6, 0.5], [0.4, 0.55, 0.3], [0.3, 0.5, 0.6, 0.9])
    by_threshold = {row["threshold"]: row for row in sweep}
    assert by_threshold[0.3]["positives_kept"] == 1.0
    assert by_threshold[0.3]["negatives_rejected"] == 0.0
    assert by_threshold[0.5]["negatives_rejected"] == round(2 / 3, 4)
    assert by_threshold[0.9]["positives_kept"] == 0.0

    best = best_threshold(sweep, min_positives_kept=0.95)
    assert best["threshold"] == 0.5
    assert best_threshold(sweep, min_positives_kept=1.1) is None


def test_dataset_round_trip(tmp_path):
    path = tmp_path / "nested" / "set.jsonl"
    examples = [
        Example("Peran keluarga", "9", "IPS", "positive", (("doc-1", 12),)),
        Example("Sistem tata surya", "9", "IPS", "negative"),
    ]
    save_examples(examples, path)
    assert load_examples(path) == examples


def test_load_examples_missing_file_explains_how_to_create(tmp_path):
    try:
        load_examples(tmp_path / "missing.jsonl")
    except FileNotFoundError as error:
        assert "evals.run questions" in str(error)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_clean_topics_dedupes_trims_and_limits():
    topics = ["  Peran keluarga. ", "Peran   keluarga", "ab", "x" * 200, "Gotong royong", "Hak dan kewajiban"]
    assert clean_topics(topics, 2) == ["Peran keluarga", "Gotong royong"]


def _chunk(page, text_len=MIN_CHUNK_CHARS + 10, chunk_type="text", ident="a"):
    return SimpleNamespace(id=f"{ident}{page}", page_number=page, chunk_content="x" * text_len, chunk_type=chunk_type)


def test_sample_chunks_skips_short_table_and_pageless_chunks():
    chunks = [_chunk(1, text_len=10), _chunk(2, chunk_type="table"), _chunk(None), _chunk(3)]
    assert [c.page_number for c in sample_chunks(chunks, 5, random.Random(1))] == [3]


def test_sample_chunks_spreads_across_pages_deterministically():
    chunks = [_chunk(page) for page in range(1, 41)]
    first = sample_chunks(chunks, 4, random.Random(7))
    again = sample_chunks(chunks, 4, random.Random(7))
    assert [c.id for c in first] == [c.id for c in again]
    pages = [c.page_number for c in first]
    assert len(pages) == 4
    assert pages == sorted(pages)
    assert pages[0] <= 10 and pages[-1] > 30


def test_write_report_creates_json_and_markdown(tmp_path):
    result = {
        "examples": 1,
        "status": {"ok": 1, "insufficient": 0, "invalid": 0, "error": 0},
        "schema_valid_rate": 1.0,
        "repair_rate": 0.0,
        "no_warnings_rate": 1.0,
        "hard_problems_rate": 0.0,
        "mean_grounded_ratio": 1.0,
        "dropped_source_ids_total": 0,
        "mean_judged_supported": None,
        "mean_seconds": 12.3,
        "runs": [{
            "topic": "Peran keluarga", "status": "ok", "calls": 1, "repaired": False,
            "warnings": 0, "grounded_ratio": 1.0, "judged_supported": None, "seconds": 12.3,
        }],
    }
    markdown = render_generation(result)
    assert "Peran keluarga" in markdown
    json_path, md_path = write_report("generation", result, markdown, directory=tmp_path / "reports")
    assert json_path.exists() and md_path.read_text(encoding="utf-8") == markdown
