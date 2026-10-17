# AI pipeline

How a curriculum PDF becomes searchable knowledge, how a teacher's request becomes a Modul Ajar, where each decision lives in the code, and how to change any of it safely. Everything here runs in the Celery worker; the API only creates jobs.

Quality is measured with the offline evaluations described in [ai-evaluation.md](ai-evaluation.md). Settings are listed in [configuration.md](configuration.md).

## The six AI flows at a glance

| # | Flow | Entry point | Main code |
|---|---|---|---|
| 1 | Document ingestion | `POST /api/curriculum/upload` | `ingestion_service.py`, `curriculum_tasks.py` |
| 2 | Retrieval | start of a generation job | `rag_service.py`, `retrieval/` |
| 3 | Generation, checks, repair | after retrieval | `llm_service.py`, `lesson_plan_checks.py`, `prompts/` |
| 4 | Failure handling | any stage | `generation_tasks.py`, `llm_client.py` |
| 5 | Cost logging | every model call | `llm_client.py`, `cost_logging.py`, `cost_calculator.py` |
| 6 | Editing and export | after completion | `lesson_plan_service.py`, `modul_pdf.py` |

## Flow 1: document ingestion

```
admin uploads PDF
  validate (.pdf, %PDF- header, size) -> store in Supabase Storage -> insert document (processing) -> COMMIT -> enqueue
worker (process_curriculum_document_task)
  download PDF
  pdf_extract.extract_pdf        pdfplumber per page: tables -> Markdown, other text in reading order
                                 any pdfplumber error -> pypdf fallback
                                 pages without text -> warnings ("mungkin hasil pindai")
  no text at all                 -> document failed with a clear message
  chunking.chunk_document        keeps a heading path; each table is its own chunk (long tables split by rows,
                                 header repeated); prose cut near 1,500 characters with overlap;
                                 records page_number and page_end
  contextual header              text to embed = "{title} | Fase X | {subject} | {heading}\n{chunk}"
                                 (stored chunk_content is the original text)
  embedding_service.embed_texts  Gemini embedding, 768 dimensions, L2-normalized, model name kept
  replace chunks in one transaction, set ingest_version=2, ingest_warnings, status=completed
```

Notes:

- The unit of retrieval is a chunk with a `chunk_type` of `text` or `table`, a `heading`, a page range, labels, an embedding, and a generated `search_vector` for keyword search.
- Scanned PDFs are detected and reported but not OCR'd.
- Re-ingest existing documents with `python -m scripts.reindex_documents --all`. It is idempotent: it deletes the document's chunks and rebuilds them.

## Flow 2: retrieval

`rag_service.retrieve_context(db, topic, grade_level, subject, user_id, lesson_plan_id)`:

```
1  build_query            "IPS kelas 9 (Fase D): pelaku ekonomi"      (retrieval/query.py, utils/fase.py)
2  embed the query        purpose="query"
3  gather_candidates      (retrieval/candidates.py; the evals call the same function)
     pre-filter           WHERE grade_level and subject equal the normalized labels
     vector search        top RAG_CANDIDATE_K by cosine distance (HNSW, iterative scan)
     keyword search       top RAG_CANDIDATE_K by Indonesian full-text rank (any-word match)
     fuse                 reciprocal rank fusion, k = 60
4  similarity floor       drop candidates under RAG_MIN_SIMILARITY
5  rerank                 top RAG_RERANK_SHORTLIST sent to a small model; each passage scored 0 to 3;
                          keep score 2 or higher, up to RAG_TOP_K; if the call fails use fused order
6  select                 passages S1..S6 within RAG_CONTEXT_MAX_CHARS
7  empty?                 no documents for the labels  -> InsufficientContextError (NO_DOCUMENTS_MESSAGE)
                          nothing relevant             -> InsufficientContextError (NOT_COVERED_MESSAGE)
```

Why each stage exists: the pre-filter guarantees a plan for class 9 never uses class 7 material; vector search finds meaning, keyword search finds exact terms (names, legal phrases) that embeddings blur; the floor and the reranker keep irrelevant text out of the prompt; abstaining is better than inventing a plan. The result carries `stats` (hit counts, top similarity, whether rerank ran, passage ids and scores) that are saved on the plan.

## Flow 3: generation, checks and repair

```
user turn:   <permintaan> kelas, fase, mapel, topik, pertemuan, menit, model </permintaan>
             <catatan_guru> ... </catatan_guru>
             <sumber> <passage id="S1" dokumen="..." halaman="14" bagian="..."> ... </passage> ... </sumber>
system:      SYSTEM_INSTRUCTION (rules, in Indonesian)
config:      response_json_schema = schema of GeneratedModul, thinking level, max output tokens

call 1 (operation "generation")
  finish reason MAX_TOKENS / SAFETY / RECITATION / empty  -> specific error
  parse with GeneratedModul                  invalid JSON/schema -> problems
  insufficient_context = true                -> InsufficientContextError(model's reason)
  sanitize_sources                           drop source ids that are not in S1..Sn, count them
  check_modul                                hard and soft problems
call 2 only if there are problems (operation "repair", stage "repairing")
  multi-turn: original request, the model's answer, "fix these problems, output the full document"
  if the repaired answer is worse and the first was usable, keep the first
hard problems left   -> LLMOutputError
soft problems left   -> kept as warnings shown to the teacher
build ModulContent   = GeneratedModul + identity + references (built by the server) + warnings
```

Server-side checks (`lesson_plan_checks.py`):

| Kind | Examples |
|---|---|
| Hard (document unusable) | No learning objectives; wrong number of meetings; empty activity table; empty rubric; nothing grounded in the sources. |
| Soft (teacher can fix) | Fewer than three activity rows; activity table without a minutes column; minutes cells that are not whole numbers; minutes that do not add up to `minutes_per_meeting`; empty overview table; worksheet without tasks. |

Design points:

- **Single source of truth.** `GeneratedModul` (`app/schemas/lesson_plan_content.py`) defines the output. `to_gemini_schema` turns its JSON Schema into the `response_json_schema` Gemini enforces (dropping `title` and `default` keywords, keeping field names and descriptions), and the same class validates the answer. Field descriptions are instructions to the model. The schema is not repeated in the prompt.
- **Rules versus data.** Rules live only in `system_instruction`. Teacher text and passages are escaped, tagged data.
- **Grounding.** Each learning objective carries `source_ids` and `grounded`. The model may design activities, worksheets and rubrics itself; those are not claimed as sourced. The UI shows an objective's sources, or "rancangan model".
- **References are built by the server** (`build_references`) from the passages whose ids the model used. A citation the model invented cannot reach the user.
- **Abstention.** The model may set `insufficient_context`; the job then fails with its reason.
- **Schema versions.** `schema_version` 1 is the original short format and stays readable and exportable; version 2 is the full Modul Ajar (identity, initial competencies, Pancasila profile, facilities, learning model, objectives, meaningful understanding, trigger questions, preparation, per-meeting activity tables, assessment with overview and rubric tables, enrichment, remedial, reflection, worksheet, reading material, glossary, references, warnings).
- **Traceability.** The plan stores `prompt_version`, `model_name`, `request_options` and `generation_meta` (retrieval stats and generation stats: calls, tokens, repaired, dropped ids, grounded objectives, warnings).

## Flow 4: failures and what the user sees

| Situation | Exception | Retried? | Plan ends as | Message shown (Indonesian) |
|---|---|---|---|---|
| No document for the kelas and mapel | `InsufficientContextError` | No | failed | "Belum ada dokumen kurikulum untuk kelas dan mata pelajaran ini." |
| Documents do not cover the topic | `InsufficientContextError` | No | failed | "Dokumen kurikulum yang tersedia belum membahas topik ini." |
| Output invalid after one repair | `LLMOutputError` | No | failed | "Model belum menghasilkan modul yang valid, bahkan setelah diperbaiki. Coba buat ulang." |
| Truncated or empty output | `LLMOutputError` | No | failed | Specific text from `ensure_usable`. |
| Safety or recitation block | `ContentBlockedError` | No | failed | Specific text from `ensure_usable`. |
| Model API stays down after its own retries | `TransientLLMError` | No | failed | "Layanan model sedang sibuk. Coba lagi sebentar lagi." |
| Infrastructure fault (database, Redis, bug) | any other | Celery once, after 30 s | failed on the last attempt | Technical text; the UI shows a generic message. |
| Unfinished for 15 minutes | - | - | reported failed | "Pembuatan modul ajar melebihi batas waktu." |

Retry policy: `call_with_retry` (tenacity) retries only transient API errors (429, 408, 5xx, timeouts), `LLM_MAX_ATTEMPTS` times with exponential backoff. Permanent errors are not retried, so a job costs at most a few model calls instead of nine. The frontend maps messages in `lib/utils/lesson-plan.ts` (`describeFailure`).

## Flow 5: cost logging

Every call that reaches the model logs a row in `llm_cost_logs` through `app/core/services/cost_logging.py`, which uses its own session so the row survives a rolled-back job:

| `operation_type` | From |
|---|---|
| `embedding` | Document chunks and queries. |
| `rerank` | The relevance scoring call. |
| `generation` | The main structured call. |
| `repair` | The one repair call. |
| `eval` | Offline evaluations. |

Fields: user, optional plan, operation, prompt tokens, completion tokens (thinking tokens included), cost from `app/utils/cost_calculator.py`. `GET /api/users/me/costs` and `GET /api/users/costs` (admin) aggregate them. If pricing changes, change `cost_calculator.py` only.

## Flow 6: editing and export

- The editor chooses its renderer from `schema_version`. Version 2 shows every section, tables editable cell by cell, sources as highlighted chips, warnings in a notice, and a running total of minutes per meeting.
- `PUT /api/lesson-plans/{id}` validates edited content against `ModulContent` (422 `invalid_content` on failure) so a bad edit cannot corrupt a plan.
- `GET /api/lesson-plans/{id}/export/pdf` routes by `schema_version`: `generate_modul_pdf` (fpdf2 tables with a repeating header, bundled DejaVu fonts for Indonesian punctuation) or the original `generate_lesson_plan_pdf`.

## Job stages

While a plan is `processing`, `generation_meta["stage"]` is `retrieving`, then `drafting`, then possibly `repairing`. The status endpoint and SSE stream expose it, and the progress list in the UI follows it.

## Changing the pipeline safely

1. Edit the prompt, schema, or retrieval setting.
2. Bump `PROMPT_VERSION` (and `SCHEMA_VERSION` if the stored shape changes; keep old versions readable).
3. Run `pytest`.
4. Run the evaluations before and after and compare ([ai-evaluation.md](ai-evaluation.md)).
5. Commit the change together with the new baseline numbers.

Rules for contributors are condensed in `.claude/rules/ai-pipeline.md`.
