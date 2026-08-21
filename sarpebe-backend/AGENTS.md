# SARPEBE Backend — Agent Guide

This file provides AI coding agents with all necessary context, architectural rules, and engineering directives to work safely and correctly on the SARPEBE backend.

---

## Project Context

You are working on the backend of SARPEBE, an Educational SaaS. The backend is a Python/FastAPI REST API whose primary responsibility is to automate the generation of curriculum-aligned lesson plans using Retrieval-Augmented Generation (RAG).

The core constraint is: all generated content must be strictly grounded in official curriculum documents uploaded by administrators. Zero hallucinations. Every lesson plan must be traceable to a source document.

---

## Tech Stack

| Tool | Version | Role |
|---|---|---|
| Python | 3.11+ | Runtime |
| FastAPI | latest | Async HTTP API framework |
| Pydantic | v2 | Request/response validation |
| SQLAlchemy | 2.0 | Async ORM |
| Alembic | latest | Database schema migrations |
| Supabase | — | PostgreSQL host + JWT auth provider |
| pgvector | — | Vector similarity search in PostgreSQL |
| Google GenAI SDK | latest | Gemini generation + text embedding API |
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
│   └── services/               # Business logic — one service per domain
├── db/
│   ├── session.py              # AsyncEngine + AsyncSession factory
│   ├── base.py                 # SQLAlchemy declarative base
│   ├── models/                 # ORM table definitions
│   └── repositories/           # DB access layer
│       └── base_repository.py  # Generic CRUD — all repositories inherit from this
├── schemas/
│   └── common.py               # Shared Pydantic types (pagination, base responses)
├── tasks/
│   ├── celery_app.py           # Celery factory
│   └── generation_tasks.py     # Async lesson plan generation task
└── utils/
    ├── chunking.py             # Semantic text chunking logic
    └── cost_calculator.py      # Token-to-fiat cost formula
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
- Chunk curriculum documents by logical semantic boundaries (paragraphs, sections) — never by arbitrary character counts.
- When prompting Gemini for generation, always instruct it to cite the `document_name` and `page_number` from the retrieved chunk metadata. The prompt must make citation non-optional.

### 3. Async LLM Flow

- Gemini API calls take 10–30 seconds. Never await them in the HTTP request lifecycle.
- Lesson plan generation endpoints must return `202 Accepted` immediately with a `job_id`.
- The actual RAG pipeline (retrieve → prompt → generate → save) runs inside a Celery task.
- Expose a separate `GET /lesson-plans/jobs/{job_id}` endpoint for the frontend to poll status.

### 4. Database Transactions

- Any operation involving more than one write (e.g., save lesson plan + deduct quota + log cost) must be wrapped in a single transaction: `async with session.begin():`.
- On any exception within the block, SQLAlchemy automatically rolls back. Never manually call `session.rollback()` inside a `begin()` block.

### 5. Concurrency and Row-Level Locking

- When reading a user's quota before decrementing it, always use `SELECT ... FOR UPDATE` (SQLAlchemy: `.with_for_update()`).
- This prevents race conditions where two concurrent requests both read "1 quota remaining" and both proceed.

### 6. Cost Logging

- Every call to the Gemini API — whether for generation or embedding — must insert a row into `llm_cost_logs`.
- Required fields: `user_id`, `lesson_plan_id` (nullable for embeddings), `operation_type`, `prompt_tokens`, `completion_tokens`, `total_cost`.
- Use `utils/cost_calculator.py` for the cost formula. Never hardcode token pricing inline.

### 7. Authentication and Authorization

- All private endpoints must declare `current_user: Profile = Depends(get_current_user)` in their signature.
- `get_current_user` in `api/deps.py` validates the Supabase JWT and returns the user profile.
- Never trust client-provided `user_id` in request bodies for write operations. Always derive it from the authenticated token.

### 8. Error Handling

- Catch specific exception types. Never use a bare `except Exception` without re-raising or logging.
- Raise `fastapi.HTTPException` with appropriate status codes. Never let raw SQLAlchemy or database errors propagate to the HTTP response.
- Use the custom exception classes in `core/exceptions.py` for domain-level errors (e.g., `QuotaExceededError`, `DocumentNotFoundError`).

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

- Row Level Security (RLS) is enabled in Supabase. The application layer must also enforce ownership — never return rows belonging to another user, even if RLS would catch it.
- UUIDs are used as primary keys across all tables. Never expose sequential integer IDs.
- Curriculum document uploads must validate MIME type server-side. Do not trust the `Content-Type` header alone.

---

## What NOT to Do

- Do not write SQL strings directly in services or routers. All SQL lives in repositories via SQLAlchemy ORM or `text()` with bound parameters.
- Do not store secrets or API keys in source code. All secrets come from environment variables via `config.py`.
- Do not use synchronous `requests` or blocking I/O anywhere in the async FastAPI application.
- Do not use lazy loading for SQLAlchemy relationships in list queries. Always use `joinedload` or `selectinload` to prevent N+1 queries.
- Do not call Gemini directly from a router. The call chain must be: Router -> Service -> `llm_service.py` -> Gemini SDK.

---

## Related

- [Root AGENTS.md](../AGENTS.md)
- [Frontend AGENTS.md](../sarpebe-frontend/AGENTS.md)
- [Database Architecture](docs/DATABASE.md)
- [Backend README](README.md)
