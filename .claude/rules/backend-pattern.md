# Backend patterns (sarpebe-backend)

Applies to all Python code under `sarpebe-backend/app/`, `scripts/` and `evals/`. Background: `docs/architecture.md`.

## Layers

```
Router (app/api/routers/) -> Service (app/core/services/) -> Repository (app/db/repositories/) -> Database
```

- A layer calls only the layer directly below it. Never skip one.
- **Router**: request parsing, `Depends()` injection, status codes, response models. No business logic, no SQL, no model imports for queries. Returns data or calls a service.
- **Service**: business logic, RAG, Gemini calls (through `app/core/llm_client.py`), cost logging. No SQL strings, no `Request`/`Response`, no imports from `app/api/`. Never touches the database without a repository.
- **Repository**: one method is one query; subclass `BaseRepository` (`base_repository.py`: `get`, `get_multi`, `create`, `update`, `delete`) and add only domain-specific queries (vector and keyword search, owner-scoped lookups). No business conditionals: the service decides which method to call.
- Do not call Gemini from a router. The chain is Router -> Service -> `llm_client.py` / `llm_service.py` -> SDK.

## Dependencies and configuration

- All `Depends()` declarations live in `app/api/deps.py` (`get_db`, `get_current_user`, `require_admin`). Never redefine them in a router.
- Every private endpoint declares `current_user: Profile = Depends(get_current_user)`; admin endpoints use `require_admin`.
- Every environment variable is a field of `Settings` in `app/config.py`. Read settings through `settings`; never call `os.environ` elsewhere. Add new variables to `.env.example` and `docs/configuration.md`.

## Schemas

- Pydantic v2. Name by role: `XCreate` (input), `XUpdate` (partial input), `XResponse` (output). Use `ConfigDict(from_attributes=True)` when reading ORM objects.
- List endpoints return `PaginatedResponse[T]` from `app/schemas/common.py`.
- Strict type hints on every function signature; avoid `Any`.

## Errors

- Raise a subclass of `AppError` from `app/core/exceptions.py` with a stable `code` for domain errors. `app/main.py` maps the class to an HTTP status in `ERROR_STATUS_CODES`; a new class that should not be a 400 must be added there.
- Catch specific exceptions. No bare `except Exception` without logging or re-raising. Never let raw SQLAlchemy errors reach the response.
- Messages in exceptions are English developer text; the frontend maps `code` to Indonesian. Messages that are shown to users as a plan's failure text (see `docs/ai-pipeline.md`) are Indonesian.

## Database use

- Multi-write operations are atomic: one transaction (`async with session.begin():` or a single commit at the end). Do not call `session.rollback()` inside a `begin()` block.
- Never lazy-load relationships in list queries; use `joinedload` or `selectinload`.
- Commit before dispatching a Celery task so the worker sees the row. Job status is derived from the `lesson_plans` row, never from Celery state.
- If a quota or other concurrent limit is ever added, read and change it under `.with_for_update()`.
- Ownership is enforced in repositories (`get_by_id_and_user`); other users' rows are 404.
- In production connect through the Supabase pooler (port 6543).

## Async and Celery

- Never block the event loop: no `requests`, no sync file or CPU-heavy work in async code (use `asyncio.to_thread`, as bcrypt and PDF parsing do).
- Work longer than a request (generation, ingestion) runs in Celery. The endpoint returns `202 Accepted` with an id.
- A Celery task builds its engine inside `asyncio.run()` through `task_session_scope()` (`app/db/session.py`); never use the module-level engine in a task.
- Tasks are idempotent: a redelivered task for a completed plan returns without work. Permanent errors mark the plan failed and return; only infrastructure faults are retried (`MAX_RETRIES = 1`).
- Services that need an independent session (cost logging) get the factory from `get_session_factory()`.

## Code style

- Modules, functions, variables: `snake_case`; classes: `PascalCase`.
- Write short docstrings for service methods and non-trivial queries; comments explain why, not what.
- Use `logging`; never `print()` in application code (scripts may print).
- Reuse before writing: search for an existing helper (`utils/labels.py`, `utils/fase.py`, `utils/text.py`, `utils/time.py`) first.
- Pricing math lives only in `app/utils/cost_calculator.py`.

## Do not

- Write SQL in services or routers; SQL lives in repositories (ORM or `text()` with bound parameters).
- Store secrets in source; read them from settings.
- Trust a client-provided `user_id` in a body; derive it from the token.
- Return `password_hash` or tokens in logs or responses.
