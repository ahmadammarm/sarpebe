# CLAUDE.md

Guidance for Claude Code when working in this repository. This is the only instruction file; code rules are in `.claude/rules/` and human documentation is in `docs/`.

## Repository overview

SARPEBE (Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum) generates curriculum-aligned lesson plans (Modul Ajar, Kurikulum Merdeka) for Indonesian teachers. It uses Retrieval-Augmented Generation over official curriculum PDFs (CP, ATP, Buku Guru) with Google Gemini, and every learning objective is traceable to a source page.

A monorepo with two decoupled applications that talk only over HTTP:

- `sarpebe-frontend`: Next.js 16 (App Router, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, TanStack Query, NextAuth).
- `sarpebe-backend`: FastAPI (Python 3.11+, SQLAlchemy 2.0 async, Supabase PostgreSQL with pgvector, Celery + Redis, Google GenAI SDK).

Each application manages its own dependencies, configuration and environment. Never add shared source code or shared dependencies at the monorepo root.

The root contains only `README.md`. Detailed documentation lives in `docs/` (index: `docs/README.md`).

## Development commands

### Backend (run from `sarpebe-backend/`)

- Virtual environment: Windows `python -m venv .venv && .venv\Scripts\activate`; Unix `python -m venv .venv && source .venv/bin/activate`
- Install: `pip install -r requirements.txt`
- Migrations: `alembic upgrade head`; new: `alembic revision --autogenerate -m "<description>"`
- API: `uvicorn app.main:app --reload --port 8000`
- Worker: `celery -A app.tasks.celery_app worker --loglevel=info`
- Tests: `pytest`, `pytest tests/unit`, `pytest tests/integration`, `pytest tests/unit/test_chunking.py -k <name>`
- Accounts: `python -m scripts.seed_users`, `scripts.create_user`, `scripts.upgrade_user`
- Reindex documents: `python -m scripts.reindex_documents [--all | --id <uuid>]`
- AI evaluations (cost tokens, run only when asked): `python -m evals.run questions|retrieval|generation`

### Frontend (run from `sarpebe-frontend/`, with `pnpm`)

- Install: `pnpm install`; dev server: `pnpm dev` (port 3000); build: `pnpm build`; start: `pnpm start`; lint: `pnpm lint`; types: `npx tsc --noEmit`

## Architecture in brief

```
Backend:   Router (app/api/routers) -> Service (app/core/services) -> Repository (app/db/repositories) -> Database
Frontend:  Page (app) -> Hook (lib/hooks) -> API client (lib/api) -> Backend REST API
```

A layer calls only the layer directly below it. Long jobs (generation, ingestion) run in Celery; the API answers `202 Accepted` with a `job_id` and clients follow `/api/lesson-plans/jobs/{job_id}` (SSE with a polling fallback). The backend owns authentication (bcrypt, short-lived JWT access tokens, rotating single-use refresh tokens); Supabase provides only Postgres and Storage. Retrieval is hybrid (vector plus Indonesian full-text, fused, filtered by a similarity floor, reranked); generation uses a Pydantic-derived JSON schema, server-side checks, one repair call, and server-built references. Plans carry a `schema_version` (1 short, 2 full Modul Ajar). Details: `docs/architecture.md`, `docs/ai-pipeline.md`.

## Rules

Detailed code rules are in `.claude/rules/`. Read the relevant files before changing code in that area, and update them in the same change when a convention changes.

| Rule file | Read it when |
|---|---|
| `rules/backend-pattern.md` | Writing or changing any Python under `sarpebe-backend/app`, scripts, or tasks: layers, dependencies, errors, transactions, Celery. |
| `rules/frontend-pattern.md` | Writing or changing anything under `sarpebe-frontend/`: layers, hooks, API client, types, Zod, components, server versus client modules. |
| `rules/ai-pipeline.md` | Touching ingestion, retrieval, prompts, schemas, generation, cost logging, or evals. |
| `rules/database-migrations.md` | Changing models, migrations, indexes, pgvector or full-text queries. |
| `rules/testing.md` | Before finishing any change: what to run, how tests are built, what must never run in tests. |
| `rules/security-auth.md` | Touching accounts, tokens, sessions, uploads, secrets, authorization. |
| `rules/design-system.md` | Any UI work: tokens, components, responsiveness, motion, accessibility, Indonesian copy. |
| `rules/git-workflow.md` | Staging, committing, or pushing: message format, scopes, what never to commit, no AI attribution. |

## Documentation

`docs/` holds the human documentation: `architecture.md`, `getting-started.md`, `configuration.md`, `operations.md`, `api-reference.md`, `authentication-security.md`, `ai-pipeline.md`, `ai-evaluation.md`, `database.md`, `frontend.md`, `design-system.md`, `testing.md`, `troubleshooting.md`. Update the matching document in the same change as the code (new endpoint, new setting, schema change, prompt or retrieval change). Write documentation without emojis, and keep each fact in one place with links elsewhere.

## Working agreements with this user

- Respond in Indonesian unless asked otherwise. All user-facing application text is Indonesian.
- Ask clarifying questions first when the user says "berikan saya pertanyaan dulu" or "sebelum itu buatkan pertanyaan".
- Do not start dev servers or take screenshots unless asked; writing code and running `pytest`, `tsc`, `eslint` and builds is fine.
- Never run migrations or write to the user's database without being asked; read-only diagnostic queries are fine. Do not edit the user's `.env` or `.env.local`; add variables to the `.env.example` files and say what to set.
- Commit and push only when asked, in logical Conventional Commits, and never mention an AI assistant in commit messages or pull request text (see `rules/git-workflow.md`).
- Do not use emojis in code, documentation, or user-facing text.

## Commit conventions

`<type>(<scope>): <short description>` with types `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf` and scopes `frontend`, `backend`, `db`, `api`, `rag`, `auth`, `docs`. Examples: `feat(backend): add async lesson plan generation endpoint`, `fix(frontend): handle job polling exponential backoff`, `refactor(backend): use BaseRepository for curriculum queries`.
