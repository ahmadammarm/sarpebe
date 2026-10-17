"""
Offline evaluation of the AI pipeline. Run from sarpebe-backend/:

    python -m evals.run questions                    # build evals/data/retrieval_set.jsonl from the indexed documents
    python -m evals.run retrieval                    # ranking quality, similarity floor, rerank as a relevance judge
    python -m evals.run generation --limit 10        # run the real pipeline on 10 topics and measure the results
    python -m evals.run generation --limit 10 --judge

These call the live models and database and cost tokens, so they are run on demand and never in CI.
Costs are logged against the first admin account. Reports are written to evals/reports/.
"""
import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.models.profile import Profile
from app.db.session import AsyncSessionLocal
from evals.dataset import DEFAULT_DATASET, load_examples, save_examples
from evals.generate_questions import build_examples
from evals.generation_eval import evaluate_generation
from evals.report import render_generation, render_retrieval, write_report
from evals.retrieval_eval import evaluate_retrieval


async def _admin_id(db):
    admin = (await db.execute(select(Profile).where(Profile.role == "admin").limit(1))).scalar_one_or_none()
    if not admin:
        raise SystemExit("No admin account found; evaluation costs need a user to be logged against.")
    return admin.id


async def run_questions(args: argparse.Namespace) -> None:
    async with AsyncSessionLocal() as db:
        examples = await build_examples(
            db, await _admin_id(db), chunks_per_document=args.chunks_per_document, seed=args.seed
        )
    save_examples(examples, args.dataset)
    positives = sum(e.kind == "positive" for e in examples)
    print(f"Wrote {len(examples)} examples ({positives} on-topic, {len(examples) - positives} off-topic) to {args.dataset}")
    print("Review the file: delete any off-topic example that your documents actually cover.")


async def run_retrieval(args: argparse.Namespace) -> None:
    examples = load_examples(args.dataset)
    async with AsyncSessionLocal() as db:
        result = await evaluate_retrieval(db, examples, await _admin_id(db), k=args.k)
    markdown = render_retrieval(result)
    print(markdown)
    print("Report:", *write_report("retrieval", result, markdown))


async def run_generation(args: argparse.Namespace) -> None:
    examples = load_examples(args.dataset)
    async with AsyncSessionLocal() as db:
        result = await evaluate_generation(db, examples, await _admin_id(db), limit=args.limit, judge=args.judge)
    markdown = render_generation(result)
    print(markdown)
    print("Report:", *write_report("generation", result, markdown))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    commands = parser.add_subparsers(dest="command", required=True)

    questions = commands.add_parser("questions", help="build the evaluation set from indexed documents")
    questions.add_argument("--chunks-per-document", type=int, default=8)
    questions.add_argument("--seed", type=int, default=7)
    questions.set_defaults(handler=run_questions)

    retrieval = commands.add_parser("retrieval", help="measure retrieval quality")
    retrieval.add_argument("--k", type=int, default=6)
    retrieval.set_defaults(handler=run_retrieval)

    generation = commands.add_parser("generation", help="measure generated modules")
    generation.add_argument("--limit", type=int, default=10)
    generation.add_argument("--judge", action="store_true", help="also check faithfulness with a judge model")
    generation.set_defaults(handler=run_generation)

    args = parser.parse_args()
    asyncio.run(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
