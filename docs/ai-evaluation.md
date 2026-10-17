# AI evaluation

Unit tests prove the code does what we wrote. They cannot tell whether retrieval finds the right page or whether a prompt change made plans better or worse. The evaluation harness in `sarpebe-backend/evals/` measures that on your real documents.

These runs call the live models and the database, so they cost tokens. Run them on demand, never in CI or in `pytest`. Their cost is logged against the first admin account (`operation_type = eval`).

## Commands

Run from `sarpebe-backend/` with the virtual environment active and a populated database.

```bash
python -m evals.run questions                       # build the evaluation set
python -m evals.run retrieval                       # measure retrieval
python -m evals.run generation --limit 10           # measure real generations
python -m evals.run generation --limit 10 --judge   # also check faithfulness with a judge model
python -m evals.run --help
```

Options: `--dataset PATH` (default `evals/data/retrieval_set.jsonl`), `questions --chunks-per-document N --seed N`, `retrieval --k N`, `generation --limit N --judge`.

Outputs are written to `evals/reports/` as a Markdown summary and a JSON file with every detail. Both `evals/data/*.jsonl` and `evals/reports/` are git-ignored.

## The evaluation set

`python -m evals.run questions` reads the indexed chunks, samples text chunks evenly across each document's pages, and asks the small model for short topics a teacher might type that the chunk can answer. Each line of `retrieval_set.jsonl` is:

```json
{"topic": "Peran keluarga dalam masyarakat", "grade_level": "9", "subject": "ips", "kind": "positive", "gold": [["<document uuid>", 14]]}
```

- `positive`: the documents cover this topic; `gold` lists where (document id and page). A retrieved chunk is a hit if its page range contains a gold page.
- `negative`: topics from unrelated subjects paired with the same labels. The right behaviour is to find nothing relevant. The list is `NEGATIVE_TOPICS` in `evals/generate_questions.py`; edit it for your documents.

After generating, open the file and delete any negative example that your documents actually cover. The questions are synthetic and lean toward the documents' own wording, so add real teacher topics over time; the harness reads any file in this format.

## What the retrieval run reports

Using the same candidate gathering as production (`retrieval/candidates.py`):

| Section | Meaning | Want |
|---|---|---|
| Ranking quality, per configuration | hit@1, hit@3, hit@k and MRR for vector only, keyword only, hybrid, and hybrid with rerank, on the positive queries. | Each added stage should improve on the one before; if rerank or keyword search does not help, question keeping it. |
| Similarity floor sweep | For floors 0.30 to 0.80: share of positive queries that keep at least one candidate, and share of negative queries rejected. | A floor that keeps at least 95% of positives while rejecting as many negatives as possible. |
| Suggested floor | The strictest floor that keeps 95% of positives, preferring the one that rejects the most negatives. | Set it as `RAG_MIN_SIMILARITY`. |
| Rerank as a judge | Share of negative queries where the reranker found nothing relevant, share of positives wrongly left with nothing, failed rerank calls. | High, low, zero. |

Decisions this informs: `RAG_MIN_SIMILARITY`, whether `RAG_USE_RERANK` pays for itself, `RAG_CANDIDATE_K` and `RAG_TOP_K`, and `EMBEDDING_USE_TASK_TYPES` (run once with it off and once on, compare hit rates, keep the better).

## What the generation run reports

It runs retrieval and generation on up to N positive examples with 2 meetings of 80 minutes:

| Measure | Meaning |
|---|---|
| Status counts | `ok`, `insufficient` (abstained), `invalid` (unusable after repair), `error`. |
| Schema-valid rate | Share of runs that ended with a valid plan or a clean abstention. |
| Repair rate | Share of produced plans that needed the second call. High means the prompt or schema is fighting the model. |
| No-warning rate | Share of produced plans with no remaining soft problems (for example minutes that do not add up). |
| Hard-problem rate | Share of produced plans that still fail a hard check (should be zero; the pipeline rejects them). |
| Mean grounded objectives | Average share of objectives that cite at least one valid source. |
| Invented source ids dropped | Count of ids the model made up and the server removed. |
| Mean judged-supported (with `--judge`) | Share of cited objectives that a judge model finds supported by the passage they cite. The closest automatic measure of faithfulness. |
| Mean seconds | Wall time per plan. |

## Baseline

Not recorded yet. After the first run on real documents, add a dated table here with the document set, the chosen `RAG_MIN_SIMILARITY`, hit@1, hit@k and MRR per configuration, schema-valid rate, repair rate, mean grounded objectives and judged-supported ratio. Future prompt or retrieval changes are compared against it.

## Process for a change

1. Run `retrieval` and, for prompt changes, `generation --judge` before the change; keep the reports.
2. Make the change; bump `PROMPT_VERSION` if a prompt or schema changed.
3. Run the same commands again and compare. A change that lowers hit rate, grounding, or judged-supported, or raises the repair rate, needs a reason.
4. Update the baseline table and commit it with the change.

## Code map

| File | Role |
|---|---|
| `evals/run.py` | Command line entry point. |
| `evals/dataset.py` | `Example` and JSONL load and save. |
| `evals/generate_questions.py` | Builds positive and negative examples. |
| `evals/metrics.py` | Pure metric functions (hit@k, MRR, threshold sweep, best threshold, page matching). |
| `evals/retrieval_eval.py` | Retrieval run. |
| `evals/generation_eval.py` | Generation run and the optional judge. |
| `evals/report.py` | Markdown and JSON reports. |
| `tests/unit/test_evals.py` | Tests for the pure parts only. |
