"""Turns an evaluation result into a readable Markdown summary and a JSON file with every detail."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).parent / "reports"


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def render_retrieval(result: dict[str, Any]) -> str:
    k = result["k"]
    ranking_rows = [
        [name, m["queries"], m["hit@1"], m["hit@3"], m[f"hit@{k}"], m["mrr"]] for name, m in result["ranking"].items()
    ]
    floor = result["similarity_floor"]
    sweep_rows = [[r["threshold"], r["positives_kept"], r["negatives_rejected"]] for r in floor["sweep"]]
    abstention = result["rerank_abstention"]
    suggested = floor["suggested"]

    parts = [
        "# Retrieval evaluation",
        f"On-topic queries: {result['examples']['positive']}. Off-topic queries: {result['examples']['negative']}.",
        "## Ranking quality (on-topic queries)",
        _table(["Configuration", "Queries", "hit@1", "hit@3", f"hit@{k}", "MRR"], ranking_rows),
        "## Similarity floor",
        f"Current `RAG_MIN_SIMILARITY`: {floor['current']}.",
        _table(["Floor", "On-topic kept", "Off-topic rejected"], sweep_rows),
        (
            f"Suggested floor: **{suggested['threshold']}** (keeps {suggested['positives_kept']:.0%} of on-topic, "
            f"rejects {suggested['negatives_rejected']:.0%} of off-topic)."
            if suggested
            else "No floor keeps enough on-topic queries; the embeddings or the documents need attention first."
        ),
        "## Rerank as a judge of relevance",
        f"Off-topic queries where the reranker found nothing relevant: {abstention['negatives_rejected']:.0%} (want high).",
        f"On-topic queries wrongly left with nothing relevant: {abstention['positives_rejected']:.0%} (want low).",
        f"Failed rerank calls (pipeline falls back to fused order): {abstention['failed_calls']}.",
    ]
    return "\n\n".join(parts) + "\n"


def render_generation(result: dict[str, Any]) -> str:
    status = result["status"]
    summary = [
        ["Examples", result["examples"]],
        ["ok / insufficient / invalid / error", f"{status['ok']} / {status['insufficient']} / {status['invalid']} / {status['error']}"],
        ["Schema-valid rate", result["schema_valid_rate"]],
        ["Repair rate (of produced)", result["repair_rate"]],
        ["No-warning rate (of produced)", result["no_warnings_rate"]],
        ["Hard-problem rate (of produced)", result["hard_problems_rate"]],
        ["Mean grounded objectives", result["mean_grounded_ratio"]],
        ["Invented source ids dropped", result["dropped_source_ids_total"]],
        ["Mean judged-supported objectives", result["mean_judged_supported"]],
        ["Mean seconds per module", result["mean_seconds"]],
    ]
    run_rows = [
        [r["topic"], r["status"], r["calls"], r["repaired"], r["warnings"], r["grounded_ratio"], r["judged_supported"], round(r["seconds"], 1)]
        for r in result["runs"]
    ]
    return "\n\n".join([
        "# Generation evaluation",
        _table(["Measure", "Value"], summary),
        "## Runs",
        _table(["Topic", "Status", "Calls", "Repaired", "Warnings", "Grounded", "Judged", "Seconds"], run_rows),
    ]) + "\n"


def write_report(name: str, result: dict[str, Any], markdown: str, directory: Path = REPORT_DIR) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = directory / f"{name}-{stamp}.json"
    md_path = directory / f"{name}-{stamp}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path
