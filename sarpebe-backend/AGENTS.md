# SARPEBE Backend — Agent Guide

This file provides AI coding agents with all necessary context, architectural rules, and engineering directives to work safely and correctly on the SARPEBE backend.

---

## Project Context

You are working on the backend of SARPEBE, an educational platform. The backend is a Python/FastAPI REST API whose primary responsibility is to automate the generation of curriculum-aligned lesson plans using Retrieval-Augmented Generation (RAG).

The core constraint is: the learning objectives and assessment content of a plan must be grounded in official curriculum documents uploaded by administrators, and every citation must be traceable to a retrieved passage. Activities, worksheets and rubrics may be the model's own design and are marked as such (`grounded: false`). If the documents do not cover the topic, the job fails with a clear message instead of generating.

---

## Tech Stack

| Tool | Version | Role |
|---|---|---|
| Python | 3.11+ | Runtime |
| FastAPI | latest | Async HTTP API framework |
| Pydantic | v2 | Request/response validation |
| SQLAlchemy | 2.0 | Async ORM |
| Alembic | latest | Database schema migrations |
| Supabase | — | PostgreSQL host + file Storage (no auth provider; auth lives in this backend) |
| pgvector | — | Vector similarity search in PostgreSQL |
| Google GenAI SDK | latest | Gemini structured generation, rerank and embeddings |
| pdfplumber / pypdf | pinned | PDF text and table extraction (pypdf is the fallback) |
| fpdf2 + DejaVu fonts | pinned | PDF export (Unicode font bundled in `app/assets/fonts/`) |
| Celery | latest | Background task queue for async generation |
| Redis | latest | Celery broker and result backend |

---

## Architecture

The project strictly follows Clean Architecture with four layers. Each layer may only call the layer directly below it — never skip a layer.

```
Router (app/api/v1/routers/)
    Handles: HTTP concerns only — input validation, auth injection, response formatting
    |
    v
Service (app/core/services/)
    Handles: Business logic, RAG orchestration, Gemini API calls, cost calculation
    No SQL. No HTTP response logic.
    |
    v
Repository (app/db/repositories/)
    Handles: Pure database access — CRUD queries and pgvector similarity search
    No business logic. One method = one query.
    |
    v
Database (Supabase — PostgreSQL + pgvector)
```

### Directory Reference

```
app/
├── main.py                     # Entrypoint: registers routers, middleware, lifespan events
├── config.py                   # All env vars via pydantic-settings — single source of truth
├── api/
│   ├── deps.py                 # All FastAPI Depends() declarations (DB session, current user)
│   └── v1/routers/             # One file per resource domain
├── core/
│   ├── security.py             # JWT validation helpers
│   ├── exceptions.py           # Custom exception classes
│   ├── llm_client.py           # Shared Gemini client: retry policy, structured calls, cost logging
│   ├── prompts/                # Versioned prompt text and builders (pure functions)
│   └── services/               # Business logic — one service per domain
│       ├── ingestion_service.py    # PDF -> chunks -> embeddings
│       ├── rag_service.py          # Retrieval entry point (uses retrieval/)
│       ├── retrieval/              # candidates, fusion, rerank, passage selection
│       ├── llm_service.py          # Generation, repair call, outcome
│       └── lesson_plan_checks.py   # Server-side checks and references
├── db/
│   ├── session.py              # AsyncEngine + AsyncSession factory
│   ├── base.py                 # SQLAlchemy declarative base
│   ├── models/                 # ORM table definitions
│   └── repositories/           # DB access layer
│       └── base_repository.py  # Generic CRUD — all repositories inherit from this
├── schemas/
│   ├── common.py               # Shared Pydantic types (pagination, base responses)
│   └── lesson_plan_content.py  # Modul Ajar schema: sent to Gemini and used to validate the answer
├── tasks/
│   ├── celery_app.py           # Celery factory
│   └── generation_tasks.py     # Async lesson plan generation task
└── utils/
    ├── pdf_extract.py          # Table-aware PDF reading
    ├── chunking.py             # Structure-aware chunking (headings, tables, overlap)
    ├── modul_pdf.py            # PDF export of a v2 Modul Ajar
    └── cost_calculator.py      # Token-to-fiat cost formula
evals/                          # Offline evaluation harness (python -m evals.run); never run in CI
scripts/                        # seed_users.py, reindex_documents.py
```

---

## Engineering Directives

### 1. Layer Boundaries

- Routers must not import from `db/` directly. All data access goes through a service, which calls a repository.
- Services must not import from `api/` or reference `Request`/`Response` objects.
- Repositories must not contain conditionals or business logic. If a query varies by business condition, the caller (service) decides which repository method to invoke.

### 2. RAG and Vector Search

- Pre-filtering is mandatory. Always apply `WHERE grade_level = :grade AND subject = :subject` via SQL before computing vector distances. Never run a similarity search across the full embedding table.
- Use cosine distance (`<=>`) for semantic similarity with Gemini embeddings (768 dimensions).
- Chunk curriculum documents by structure (headings, tables as their own chunks, overlap) — never by arbitrary character counts. The text embedded carries a contextual header; the stored text is the original.
- Retrieval is hybrid (vector + Indonesian full-text, reciprocal rank fusion), cut by `RAG_MIN_SIMILARITY`, then reranked. Candidate gathering lives in `retrieval/candidates.py` and is shared with the evals so they measure what production does. If nothing is relevant, raise `InsufficientContextError` before any generation call.
- Normalize embeddings (L2) after truncation and store `embedding_model` with each chunk.
- Citations are built by the server from passage ids (`S1`...). The model only returns ids; unknown ids are dropped. Never display a citation string written by the model.
- Prompts: rules live only in `system_instruction`. Teacher input and passages are escaped (`prompts/common.py`) and tagged as data. Do not repeat the output schema in the prompt; the JSON Schema comes from the Pydantic model (`to_gemini_schema`), the single source of truth.
- Changing a prompt, schema or retrieval setting: bump `PROMPT_VERSION` (and `SCHEMA_VERSION` if the stored shape changes; old plans keep rendering by their `schema_version`), run `pytest`, then the evals before and after (see `docs/AI.md`).

### 3. Async LLM Flow

- Generation takes about 20–60 seconds (rerank, generation, possibly one repair call). Never await it in the HTTP request lifecycle.
- Lesson plan generation endpoints must return `202 Accepted` immediately with a `job_id`.
- The actual RAG pipeline (retrieve → prompt → generate → check/repair → save) runs inside a Celery task, which records `generation_meta["stage"]` for the status endpoint.
- Expose an authenticated `GET /lesson-plans/jobs/{job_id}` (and `/stream` for SSE) endpoint. Status is read from the owner's `lesson_plans` row; other users get 404.

### 4. Database Transactions

- Any operation involving more than one write (e.g., create plan + dispatch job) must be wrapped in a single transaction: `async with session.begin():`.
- On any exception within the block, SQLAlchemy automatically rolls back. Never manually call `session.rollback()` inside a `begin()` block.

### 5. Concurrency and Row-Level Locking

- Generation is currently unlimited; there is no quota to deduct. If one is reintroduced, read-and-decrement it with `SELECT ... FOR UPDATE` (SQLAlchemy: `.with_for_update()`) so concurrent requests cannot double-spend it.
- Always `commit()` before dispatching a Celery task: the worker runs in another process and must see the committed row.

### 6. Cost Logging

- Every call to the Gemini API (generation, repair, rerank, embedding, eval) must insert a row into `llm_cost_logs`, thinking tokens included. Use `llm_client.generate_structured` rather than calling the SDK directly.
- Required fields: `user_id`, `lesson_plan_id` (nullable for embeddings), `operation_type`, `prompt_tokens`, `completion_tokens`, `total_cost`.
- Use `utils/cost_calculator.py` for the cost formula. Never hardcode token pricing inline.

### 7. Authentication and Authorization

- All private endpoints must declare `current_user: Profile = Depends(get_current_user)` in their signature.
- `get_current_user` in `api/deps.py` verifies the access token issued by `/api/auth/login` (signature, expiry, issuer, type) and loads the profile; a deleted account gets 401.
- Passwords are bcrypt hashes (`core/security.py`); never log or return `password_hash`. Refresh, verification and reset tokens are random, single-use, and only their SHA-256 is stored.
- Auth endpoints must not reveal whether an email is registered (register, forgot-password and resend answer identically either way).
- Never trust client-provided `user_id` in request bodies for write operations. Always derive it from the authenticated token.

### 8. Error Handling

- Catch specific exception types. Never use a bare `except Exception` without re-raising or logging.
- Raise `fastapi.HTTPException` with appropriate status codes. Never let raw SQLAlchemy or database errors propagate to the HTTP response.
- Use the custom exception classes in `core/exceptions.py` for domain-level errors (e.g., `DocumentNotFoundError`, `InvalidStateError`); `app/main.py` maps them to HTTP status codes.
- Model failures: only transient errors (429, 408, 5xx, timeouts) are retried, by `call_with_retry`. `InsufficientContextError`, `LLMOutputError`, `ContentBlockedError` and `TransientLLMError` are permanent for that job: mark the plan failed with a user-readable Indonesian message and do not let Celery retry them.

### 9. Configuration

- All environment variables must be declared in `app/config.py` as fields on the `Settings` Pydantic model.
- Access settings via the injected settings instance — never call `os.environ.get()` directly anywhere else in the codebase.

### 10. Connection Pooling

- In production, connect to Supabase via the Supavisor pooler (port 6543, transaction mode) — not the raw PostgreSQL port 5432.
- Configure `AsyncEngine` with explicit `pool_size` and `max_overflow` values aligned with the pooler's capacity.

---

## DRY Conventions

- `base_repository.py` provides generic `get(id)`, `get_multi(skip, limit)`, `create(schema)`, `update(id, schema)`, `delete(id)` methods. All domain repositories inherit from it. Only add methods for queries that are genuinely domain-specific.
- `api/deps.py` is the single location for all `Depends()` declarations. Never redefine the DB session or current user injection in individual routers.
- `schemas/common.py` defines `PaginatedResponse[T]`, `BaseResponse`, and shared field types. All list endpoints must return `PaginatedResponse`.
- `utils/cost_calculator.py` is the single source for token cost math. If pricing changes, it changes in exactly one place.

---

## Coding Standards

- Use strict Python type hints on all function signatures: `-> None`, `-> LessonPlan`, `-> list[DocumentChunk]`, etc. Avoid `-> Any`.
- Pydantic models must use `model_config = ConfigDict(from_attributes=True)` when reading from ORM objects.
- Name schemas by role: `LessonPlanCreate` (input), `LessonPlanUpdate` (partial input), `LessonPlanResponse` (output).
- Write concise docstrings for all service methods and any non-trivial repository query.
- Use `loguru` or Python's `logging` module for structured logs. Never use `print()` in production code.

---

## Security Rules

- The API connects with a privileged database role, so Row Level Security does not protect these tables. The application layer must enforce ownership — never return rows belonging to another user.
- UUIDs are used as primary keys across all tables. Never expose sequential integer IDs.
- Curriculum document uploads must validate MIME type server-side. Do not trust the `Content-Type` header alone.

---

## What NOT to Do

- Do not write SQL strings directly in services or routers. All SQL lives in repositories via SQLAlchemy ORM or `text()` with bound parameters.
- Do not store secrets or API keys in source code. All secrets come from environment variables via `config.py`.
- Do not use synchronous `requests` or blocking I/O anywhere in the async FastAPI application.
- Do not use lazy loading for SQLAlchemy relationships in list queries. Always use `joinedload` or `selectinload` to prevent N+1 queries.
- Do not call Gemini directly from a router. The call chain must be: Router -> Service -> `llm_client.py` / `llm_service.py` -> Gemini SDK.
- Do not write the output JSON schema by hand or paste it into a prompt; derive it from the Pydantic models.
- Do not run the evals in CI or in tests: they call live models and cost money.

---

## Related

- [Root AGENTS.md](../AGENTS.md)
- [Frontend AGENTS.md](../sarpebe-frontend/AGENTS.md)
- [AI Pipeline](docs/AI.md)
- [Database Architecture](docs/DATABASE.md)
- [Backend README](README.md)
