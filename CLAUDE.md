# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

SARPEBE (Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum) is an educational platform that automates curriculum-aligned lesson plan generation for Indonesian educators using Retrieval-Augmented Generation (RAG) powered by Google Gemini.

This repository is a monorepo containing two decoupled applications:
- `sarpebe-frontend`: Next.js 16 web interface (App Router, React 19, TypeScript, Tailwind CSS 4, shadcn/ui).
- `sarpebe-backend`: FastAPI REST API (Python 3.11+, SQLAlchemy 2.0, Supabase PostgreSQL with pgvector, Celery + Redis, Google GenAI SDK).

Each application manages its own dependencies, configuration, and environment. Never introduce shared source code or shared dependencies at the monorepo root.

---

## Development Commands

### Backend (`sarpebe-backend/`)

Commands are run from the `sarpebe-backend/` directory:

- **Virtual Environment Setup**:
  - Windows: `python -m venv .venv && .venv\Scripts\activate`
  - Unix: `python -m venv .venv && source .venv/bin/activate`
- **Install Dependencies**: `pip install -r requirements.txt`
- **Run Migrations**: `alembic upgrade head`
- **Create New Migration**: `alembic revision --autogenerate -m "<migration_description>"`
- **Start API Server**: `uvicorn app.main:app --reload --port 8000`
- **Start Celery Worker**: `celery -A app.tasks.celery_app worker --loglevel=info`
- **Run All Tests**: `pytest`
- **Run Test Directory**: `pytest tests/unit` or `pytest tests/integration`
- **Run Single Test File**: `pytest tests/unit/test_chunking.py`
- **Run Specific Test Function**: `pytest tests/unit/test_chunking.py -k <test_function_name>`

### Frontend (`sarpebe-frontend/`)

Commands are run from the `sarpebe-frontend/` directory using `pnpm`:

- **Install Dependencies**: `pnpm install`
- **Start Development Server**: `pnpm dev` (runs on `http://localhost:3000`)
- **Build for Production**: `pnpm build`
- **Start Production Server**: `pnpm start`
- **Lint Code**: `pnpm lint`

---

## High-Level Architecture & Layering

Both applications enforce strict layered architecture where a layer may only call the layer immediately below it.

### Backend Architecture

```
Router (app/api/routers/)
    | HTTP concerns: request parsing, dependency injection, status codes
    v
Service (app/core/services/)
    | Business logic, RAG coordination, Gemini LLM calls, cost logging
    v
Repository (app/db/repositories/)
    | Database queries (SQLAlchemy ORM + pgvector similarity)
    v
Database (Supabase PostgreSQL + pgvector)
```

- **Router Layer**: Validates requests and returns HTTP responses. Injects dependencies via `app/api/deps.py` (e.g. `get_db`, `get_current_user`). Never touches database models or executes queries directly.
- **Service Layer**: Implements core business logic. Coordinates RAG, handles document chunking, calls Gemini API, and tracks token costs. Never accesses database without a repository.
- **Repository Layer**: Subclasses `BaseRepository` (`app/db/repositories/base_repository.py`) for generic CRUD. Custom queries (e.g., vector similarity search) live exclusively in domain-specific repositories.
- **Authentication**: The backend owns authentication (`app/api/routers/auth.py`, `app/core/services/auth_service.py`): bcrypt passwords, short-lived HS256 access tokens, rotating single-use refresh tokens, emailed verification and reset links. Supabase is used only for Storage and the Postgres host. Auth endpoints must not reveal whether an email is registered.
- **Async Tasks**: Long-running generation jobs (10-30 seconds) must run in Celery (`app/tasks/generation_tasks.py`). The API endpoint responds immediately with `202 Accepted` and a `job_id`, and clients poll `/api/lesson-plans/jobs/{job_id}`.
- **RAG & Vector Search** (details in `sarpebe-backend/docs/AI.md`):
  - Embedding dimensionality is 768, L2-normalized after truncation; the model name is stored per chunk.
  - Pre-filtering is required: always filter by normalized `grade_level` and `subject` via SQL before any similarity or keyword ranking.
  - Retrieval is hybrid: vector (pgvector `<=>`) plus Indonesian full-text candidates, fused by reciprocal rank fusion, cut by `RAG_MIN_SIMILARITY`, then reranked by a small model. If nothing is relevant, stop before generation (`InsufficientContextError`).
  - Documents are read with table-aware extraction and chunked by structure (headings, tables as their own chunks), not arbitrary character windows.
  - Prompts: rules only in `system_instruction`; user input and passages are escaped, tagged data. Output shape comes from the Pydantic schema (`response_json_schema`), never a hand-written copy.
  - Citations are built by the server from passage ids (`S1`...), never trusted as free text from the model. Bump `PROMPT_VERSION` when a prompt or schema changes and run `python -m evals.run ...` before and after.
- **Database Transactions & Concurrency**:
  - Multi-write operations must use `async with session.begin():`.
  - Generation is currently unlimited (the per-tier quota was removed). If a quota is ever reintroduced, deduct it under pessimistic row locking via `.with_for_update()`.
  - Commit before dispatching a Celery task so the worker is guaranteed to see the row. Job status is derived from the `lesson_plans` row, never from Celery state.
  - Cost logs are written through `app/core/services/cost_logging.py` in their own session so they survive rollbacks.
  - Celery tasks must create their DB engine inside `asyncio.run()` via `task_session_scope()` (`app/db/session.py`).
  - Every Gemini API call must log token counts and calculated cost to `llm_cost_logs` using `app/utils/cost_calculator.py`.

### Frontend Architecture

```
Page (app/)
    | App Router routing, layout assembly, trigger hooks
    v
Custom Hook (lib/hooks/)
    | TanStack Query data fetching, state, polling, mutations
    v
API Client (lib/api/)
    | Centralized HTTP client (client.ts), authentication headers, error handling
    v
Backend REST API
```

- **Page Layer**: Assembles layout and feature components. Must not make direct `fetch()` or API client calls.
- **Hook Layer**: Encapsulates server state and side effects using TanStack Query. Provides job tracking (`useJobStatus.ts`: authenticated SSE with a polling fallback) for async generation jobs.
- **API Client Layer**: `lib/api/client.ts` is the single entry point for backend requests, injecting authentication tokens and handling base URL configurations.
- **State Management**:
  - Server state: TanStack Query inside `lib/hooks/`.
  - Client/UI state: Zustand stores inside `lib/stores/`.
- **Validation**: Shared Zod schemas in `lib/utils/validators.ts` drive both client-side form validation and TypeScript type inferences (`z.infer<...>`).
- **Type Safety**: Centralized interfaces live in `types/` and must mirror backend schemas. Avoid `any`.

---

## Commit Conventions

Use Conventional Commits:
`<type>(<scope>): <short description>`

- **Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`
- **Scopes**: `frontend`, `backend`, `db`, `api`, `rag`, `auth`, `docs`
- **Examples**:
  - `feat(backend): add async lesson plan generation endpoint`
  - `fix(frontend): handle job polling exponential backoff`
  - `refactor(backend): use BaseRepository for curriculum queries`
