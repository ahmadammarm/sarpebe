# SARPEBE Backend: AI Pipeline

How a Modul Ajar is produced, where each decision lives, and how to change any of it safely.

## 1. Ingestion (`ingestion_service.py`)

```
PDF -> pdfplumber (text + tables as Markdown) -> structure-aware chunks -> embeddings -> document_chunks
```

- `app/utils/pdf_extract.py` reads each page with `pdfplumber`: tables become Markdown, the remaining text is ordered by position. If `pdfplumber` fails it falls back to `pypdf`. Pages with no text are recorded in `curriculum_documents.ingest_warnings` (likely scans; there is no OCR).
- `app/utils/chunking.py` keeps a running heading path, makes every table its own chunk (long tables split by rows, header repeated), and cuts prose at about 1,500 characters with a short overlap. A chunk records its first page and, if it spans pages, its last.
- **Contextual header:** the text that is embedded is `"{document} | Fase X | {subject} | {heading}\n{chunk}"`. Only `chunk_content` (the original text) is stored and shown.
- Embeddings (`embedding_service.py`) are truncated to 768 dimensions and then L2-normalized; the model name is stored per chunk.
- Existing documents: `python -m scripts.reindex_documents --all` (or `--id <uuid>`).

## 2. Retrieval (`rag_service.py`, `retrieval/`)

1. **Query**: `"IPS kelas 9 (Fase D): topik"` instead of the bare topic.
2. **Candidates** (`candidates.py`, shared with the evals): pre-filter by normalized grade and subject, then vector top-20 and Indonesian full-text top-20.
3. **Fusion**: reciprocal rank fusion (k=60).
4. **Floor**: candidates under `RAG_MIN_SIMILARITY` are dropped.
5. **Rerank** (`rerank.py`): a small model scores each shortlisted passage 0-3; passages scoring 2 or more are kept (up to `RAG_TOP_K`). If the call fails the fused order is used.
6. **Abstain**: if nothing is relevant, `InsufficientContextError` is raised and **no generation call is made**.
7. **Passages** get stable ids `S1..S6` within `RAG_CONTEXT_MAX_CHARS`.

## 3. Generation (`llm_service.py`, `prompts/`, `schemas/lesson_plan_content.py`)

- **Single source of truth:** `GeneratedModul` (Pydantic) defines the output. Its JSON Schema (`to_gemini_schema`) is sent as `response_json_schema`, and the same class validates the answer. Field descriptions are instructions to the model.
- **Prompt layout:** rules live only in `system_instruction` (`prompts/lesson_plan.py`). The user turn holds the request, the teacher's notes and the passages as XML-tagged, escaped *data*, so text inside a PDF or in the notes cannot rewrite the rules. The schema is not repeated in the prompt.
- **Abstention:** the model may set `insufficient_context`; the plan then fails with the "dokumen belum cukup" message.
- **Checks** (`lesson_plan_checks.py`): table shape, activity minutes per meeting equal `minutes_per_meeting`, `source_ids` exist. Hard problems trigger **one repair call** (previous answer + the list of problems). Soft problems that survive become `warnings` shown to the teacher. If the repaired answer is worse, the first usable one is kept.
- **References are built by the server** from the passages whose ids the model used. Unknown ids are dropped and counted, so an invented citation cannot reach the UI.
- **Failures:** MAX_TOKENS, SAFETY and RECITATION finishes raise specific errors. Only transient API errors (429, 408, 5xx, timeouts) are retried (`call_with_retry`, `LLM_MAX_ATTEMPTS`); Celery retries once, only for infrastructure faults.
- **Cost:** every model call (generation, repair, rerank, embedding, eval) is logged to `llm_cost_logs`, including thinking tokens.
- **Traceability:** each plan stores `schema_version`, `prompt_version`, `model_name`, `request_options` and `generation_meta`.

## 4. Changing a prompt, schema or retrieval setting

1. Edit the prompt or schema. Bump `PROMPT_VERSION` (and `SCHEMA_VERSION` if the stored shape changed; old plans keep rendering by their own `schema_version`).
2. Run `pytest`.
3. Run the evaluations below before and after, and compare the numbers.
4. Commit the change together with the new baseline in the section below.

## 5. Evaluations (`evals/`)

These call the live models and the database and cost tokens, so they are run on demand, never in CI. Cost is logged against the first admin account. Reports go to `evals/reports/` (git-ignored).

```bash
python -m evals.run questions                  # synthetic teacher topics from the indexed chunks (+ off-topic ones)
python -m evals.run retrieval                  # hit@k and MRR: vector vs keyword vs hybrid vs hybrid+rerank
python -m evals.run generation --limit 10      # schema-valid, repair, warnings, grounding on real runs
python -m evals.run generation --limit 10 --judge   # also: is each objective supported by its cited passage?
```

- Open `evals/data/retrieval_set.jsonl` after `questions` and delete any off-topic example that your documents do cover.
- The retrieval report prints a similarity-floor sweep and a suggested `RAG_MIN_SIMILARITY`; set it in `.env`.
- `EMBEDDING_USE_TASK_TYPES` and `GENERATION_THINKING_LEVEL` are settings so they can be decided by these numbers, not assumed.
- Synthetic questions lean toward the wording of the documents. Add real teacher topics to the JSONL file over time.

### Baseline

Not recorded yet. After the first run on real documents, write the date, document set and these numbers here: hit@1/hit@6/MRR per configuration, chosen floor, schema-valid rate, repair rate, mean grounded ratio, judged-supported ratio.
