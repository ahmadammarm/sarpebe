# Architecture

SARPEBE is a monorepo with two applications that talk only over HTTP. Neither imports code from the other, and the repository root holds no shared source code.

```
sarpebe/
  sarpebe-frontend/   Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui
  sarpebe-backend/    FastAPI, SQLAlchemy 2.0 (async), Celery, Redis, Google GenAI SDK
  docs/               this documentation
  .claude/            project instructions and code rules for AI coding assistants
```

## System overview

```
Browser (Next.js, NextAuth session cookie)
   |  HTTPS, Authorization: Bearer <access token>
   v
FastAPI  (/api/auth, /api/users, /api/lesson-plans, /api/curriculum)
   |                         |
   | enqueue (after commit)  | read/write
   v                         v
Redis  <---- Celery worker   Supabase PostgreSQL + pgvector      Supabase Storage (PDF files)
                |  |
                |  +--> Google Gemini: embeddings, rerank, structured generation
                +-----> same database (own sessions)
```

Components and what each owns:

| Component | Responsibility |
|---|---|
| Next.js app | Pages, forms, editors, session (NextAuth), job tracking (SSE with polling fallback). |
| FastAPI | Authentication, authorization, validation, job creation, reading plans, PDF and Word export. |
| Celery worker | Document ingestion and lesson plan generation, which are too slow for a request. |
| Redis | Celery broker and result backend, plus login rate-limit counters. |
| PostgreSQL + pgvector | All data: users, tokens, documents, chunks and embeddings, plans, cost logs. |
| Supabase Storage | The uploaded curriculum PDFs (public bucket `sarpebe-storage`). |
| Gemini | `gemini-embedding-2` for vectors, a small model for rerank, `gemini-3.8-flash` for writing the plan. |

Supabase provides only the Postgres host and Storage. Authentication is implemented by the backend (see [authentication-security.md](authentication-security.md)).

## Backend layers

A layer may only call the layer directly below it.

```
Router      app/api/routers/       HTTP only: parse request, inject dependencies, return status code
  |
Service     app/core/services/     business logic, RAG, Gemini calls, cost logging
  |
Repository  app/db/repositories/   database queries (SQLAlchemy ORM, pgvector, full-text search)
  |
Database    PostgreSQL + pgvector
```

Supporting modules:

| Path | Purpose |
|---|---|
| `app/main.py` | App creation, CORS, one handler that turns `AppError` subclasses into JSON `{detail, code}`. |
| `app/api/deps.py` | `get_db`, `get_current_user`, `require_admin`. The only place for `Depends()` declarations. |
| `app/config.py` | All settings (pydantic-settings). Nothing else reads `os.environ`. |
| `app/core/security.py` | bcrypt hashing, access-token creation and verification, opaque token hashing. |
| `app/core/rate_limit.py` | Redis counters for login lockout; fails open when Redis is down. |
| `app/core/llm_client.py` | The only code that calls the Gemini SDK: retry policy, structured calls, cost logging. |
| `app/core/prompts/` | Versioned prompt text and builders (pure functions). |
| `app/core/storage.py` | Supabase Storage upload, public URL, delete. |
| `app/schemas/` | Pydantic request and response models. `lesson_plan_content.py` is the Modul Ajar schema. |
| `app/tasks/` | Celery app and the two tasks (`generation_tasks.py`, `curriculum_tasks.py`). |
| `app/utils/` | Pure helpers: PDF reading, chunking, labels, fase mapping, cost math, PDF and Word export. |
| `evals/` | Offline evaluation harness (not part of the running service). |
| `scripts/` | Operator scripts: seed users, create or upgrade a user, reindex documents. |

Error handling: services raise subclasses of `AppError` (`app/core/exceptions.py`), each with a stable `code`. `app/main.py` maps the class to an HTTP status. Routers never build error responses themselves. The full list of codes is in [api-reference.md](api-reference.md).

## Frontend layers

```
Page        app/                    routing and layout assembly
  |
Hook        lib/hooks/              TanStack Query, polling and SSE, mutations
  |
API client  lib/api/                one axios instance (client.ts) plus one file per resource
  |
Backend REST API
```

Other frontend locations: `components/ui` (primitives), `components/features` (domain components), `components/brand` (the notebook-paper design pieces), `components/landing`, `types/` (mirrors of backend schemas), `lib/utils/validators.ts` (Zod schemas). See [frontend.md](frontend.md).

## End-to-end flow: generating a lesson plan

```
1  Teacher submits the form (kelas, mapel, topik, pertemuan, menit, model, catatan)
2  POST /api/lesson-plans
     validate (Zod in the browser, Pydantic on the server)
     insert lesson_plans row: status=pending, job_id, request_options, prompt_version, model_name
     COMMIT
     enqueue Celery task  ->  respond 202 {job_id, id}
3  Browser opens GET /api/lesson-plans/jobs/{job_id}/stream (SSE), polling if the stream fails
4  Worker: status=processing, stage=retrieving
     embed the query, gather vector + keyword candidates, fuse, apply floor, rerank
     nothing relevant  ->  status=failed with a clear message, no generation call
5  Worker: stage=drafting   one structured Gemini call (schema from Pydantic)
     validate, run server checks
     problems  ->  stage=repairing, one repair call
6  Worker: build references from the passages used, save generated_content (schema_version 2),
     generation_meta, status=completed
7  Browser sees completed, opens /lesson-plans/{id}; the editor chooses v1 or v2 by schema_version
```

Key properties:

- The job status is read from the `lesson_plans` row, never from Celery state. A plan unfinished after 15 minutes is reported as timed out.
- The row is committed before the task is enqueued, so the worker always finds it.
- Every model call (embedding, rerank, generation, repair) writes a row in `llm_cost_logs` through its own session, so costs survive a rolled-back transaction.
- Failures are classified: permanent ones (no relevant document, unusable output, blocked content) end the job at once; only transient API errors are retried. Details in [ai-pipeline.md](ai-pipeline.md).

## End-to-end flow: ingesting a curriculum document

```
1  Admin uploads a PDF with kelas, mapel, jenis (CP, ATP, BUKU_GURU)   POST /api/curriculum/upload
     check extension, "%PDF-" magic bytes, size limit; normalize labels
     store the file in Supabase Storage, insert curriculum_documents (status=processing), COMMIT
     enqueue ingestion  ->  202
2  Worker: read PDF (tables as Markdown), chunk by structure, embed, insert document_chunks
     status=completed (or failed with the reason); page warnings saved in ingest_warnings
```

## Data ownership and multi-tenancy

The API connects to the database with a privileged role, so database-level row security is not used. Ownership is enforced in repositories: plan queries always filter by the authenticated `user_id`, and other users get 404. Documents and chunks are written only through admin endpoints. See [database.md](database.md).

## Design decisions in brief

| Decision | Reason |
|---|---|
| Async generation with 202 and job id | A plan takes 20 to 60 seconds; requests must not wait. |
| Commit before enqueue | The worker is another process and must see the row. |
| Pre-filter by grade and subject before ranking | Correctness and speed; documents for other classes can never leak into a plan. |
| Hybrid retrieval with a relevance floor and abstention | Better recall, and an honest failure beats an invented plan. |
| Pydantic schema as the single source of the output format | The schema sent to Gemini and the validator cannot drift apart. |
| References built by the server | A model cannot fabricate a citation that reaches the user. |
| `schema_version` on every plan | Old plans keep working while the format evolves. |
| Backend-owned authentication | No dependency on an external auth provider; full control of tokens. |
