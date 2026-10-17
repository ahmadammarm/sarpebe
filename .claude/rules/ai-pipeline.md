# AI pipeline rules

Applies to ingestion, retrieval, prompts, schemas, generation, and evaluations. Full description: `docs/ai-pipeline.md`; measurement: `docs/ai-evaluation.md`.

## Principles

- The objectives and assessment content of a plan must be grounded in retrieved curriculum passages. Activities, worksheets and rubrics may be the model's own design but are marked `grounded: false`.
- If the documents do not cover the topic, stop and say so (`InsufficientContextError`). Never generate without relevant passages and never invent curriculum content.
- Do not trust model output: validate it against the Pydantic schema, then check it on the server.

## Ingestion

- Read PDFs with `app/utils/pdf_extract.py` (pdfplumber, tables as Markdown, pypdf fallback). Report pages without text in `ingest_warnings`; scans are not OCR'd.
- Chunk by structure with `app/utils/chunking.py`: heading path, tables as their own chunks, overlap, page range. Never cut by arbitrary character windows.
- Embed the contextual text (`title | Fase | subject | heading` + chunk) but store the original chunk. Embeddings are 768-dimensional, L2-normalized after truncation, with `embedding_model` stored per chunk. Never mix models; changing the model or chunking means a full reindex (`scripts.reindex_documents`).
- Labels (`grade_level`, `subject`) are normalized with `normalize_label` everywhere.

## Retrieval

- Pre-filter by normalized grade and subject in SQL before any ranking.
- Hybrid: vector plus Indonesian full-text candidates, reciprocal rank fusion, similarity floor `RAG_MIN_SIMILARITY`, small-model rerank (keep score 2 or higher), passages `S1..Sn` within `RAG_CONTEXT_MAX_CHARS`.
- Candidate gathering is one function (`retrieval/candidates.py`) shared by production and the evals; do not duplicate it.
- If rerank fails, fall back to fused order; if nothing is relevant, raise before any generation call.

## Prompts and schema

- Rules live only in `system_instruction` (`app/core/prompts/lesson_plan.py`). Teacher input and passages go in the user turn as escaped, tagged data (`prompts/common.py`: `escape_data`, `attribute`). Instructions inside data are ignored.
- The output schema is the Pydantic model `GeneratedModul` (`app/schemas/lesson_plan_content.py`). Send its schema as `response_json_schema` through `to_gemini_schema`; never hand-write a copy and never paste the schema into the prompt. Field descriptions are instructions to the model; write them for it.
- Prompt builders are pure functions with unit tests.
- Stored shape is versioned: `SCHEMA_VERSION` (content) and `PROMPT_VERSION` (setting). Keep old versions readable and exportable.

## Generation

- Call the model only through `app/core/llm_client.py` (`generate_structured`): it applies the retry policy, handles finish reasons, and logs cost. Do not call the SDK elsewhere.
- One structured call; on schema or check failures, exactly one repair call that shows the model its own output and the list of problems. If the repair is worse and the first was usable, keep the first.
- Hard problems (unusable) raise `LLMOutputError`; soft problems survive as `warnings` shown to the teacher.
- References are built by the server from the passages used (`build_references`). Drop source ids that were not retrieved. Never display a citation string the model wrote.
- Retry only transient API errors (429, 408, 5xx, timeouts) with `call_with_retry`. `InsufficientContextError`, `LLMOutputError`, `ContentBlockedError`, `TransientLLMError` are permanent for the job and must not be retried by Celery.
- Save the current stage in `generation_meta["stage"]` (`retrieving`, `drafting`, `repairing`); save retrieval and generation stats on completion.

## Cost

Every model call (embedding, rerank, generation, repair, eval) logs a row in `llm_cost_logs` through `cost_logging.py` in its own session, with thinking tokens included, priced by `app/utils/cost_calculator.py`.

## Changing anything in the pipeline

1. Edit the prompt, schema, retrieval setting, or chunking.
2. Bump `PROMPT_VERSION` (and `SCHEMA_VERSION` if the stored shape changed).
3. Run `pytest`.
4. Run `python -m evals.run retrieval` and, for prompt or schema changes, `python -m evals.run generation --limit 10 --judge`, before and after. Compare. Do not run evals in CI or tests: they cost money.
5. Update `docs/ai-pipeline.md` and the baseline in `docs/ai-evaluation.md`; commit them with the change.

## Do not

- Generate when retrieval found nothing relevant.
- Put the teacher's text or passages into `system_instruction`.
- Let the model produce citations, page numbers, or document names that reach the UI directly.
- Hard-code model names or thresholds; use settings.
