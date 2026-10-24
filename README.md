# SARPEBE

**Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum**

SARPEBE helps Indonesian teachers write a complete Modul Ajar (Kurikulum Merdeka) from the official curriculum documents. A teacher gives a class, subject and topic; the system finds the relevant parts of the Capaian Pembelajaran (CP), ATP or Buku Guru PDFs that an administrator uploaded, and drafts the module with those sources. Every learning objective can be traced to a page, and if the documents do not cover the topic the system says so instead of inventing content.

## What a generated module contains

General information (identity, initial competencies, Pancasila profile, facilities, learning model), core components (learning objectives with sources, meaningful understanding, trigger questions, preparation), activities per meeting as tables with minutes that add up, assessment (diagnostic, formative, summative, overview and rubric tables), enrichment and remedial activities, reflection, and attachments (worksheet, reading material, glossary). The teacher edits everything in the browser, including table cells, and exports a PDF or a Word document.

## How it works

```
Browser (Next.js)  -->  FastAPI  -->  Celery worker  -->  Gemini
                          |               |
                          +----  Supabase PostgreSQL + pgvector, Storage  ----+      Redis
```

1. An administrator uploads a CP PDF with its class and subject. A worker reads the text and tables, splits it by structure, and stores embeddings.
2. A teacher submits a topic with the number of meetings, minutes per meeting, teaching model and notes. The API answers at once with a job id.
3. The worker retrieves the best passages (class and subject filter, vector plus keyword search, relevance floor, rerank), asks Gemini for a structured module, checks it (tables, minutes, sources), repairs it once if needed, and saves it with server-built references.
4. The browser follows progress live (finding sources, drafting, checking) and opens the editor when it is ready. Generation takes about 20 to 60 seconds.

Quality is measured with an offline evaluation harness, and every prompt and schema change is versioned. See [docs/ai-pipeline.md](docs/ai-pipeline.md) and [docs/ai-evaluation.md](docs/ai-evaluation.md).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, TanStack Query, NextAuth |
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | Supabase PostgreSQL with pgvector (HNSW) and Indonesian full-text search |
| Storage | Supabase Storage (curriculum PDFs) |
| AI | Google Gemini: embeddings, small-model rerank, structured generation |
| Background work | Celery with Redis |
| Authentication | Backend-issued JWT access tokens and rotating refresh tokens, bcrypt passwords |

## Repository layout

```
sarpebe/
  sarpebe-frontend/   web application
  sarpebe-backend/    API, worker, migrations, evaluation harness
  docs/               detailed documentation
  .claude/            project instructions and code rules for AI coding assistants
  README.md           this file
```

The two applications are independent: each has its own dependencies and configuration, and they communicate only over HTTP.

## Quick start

Prerequisites: Python 3.11+, Node.js 20+, pnpm, Redis, a Supabase project (with the `vector` extension and a public Storage bucket `sarpebe-storage`), and a Gemini API key.

```bash
# backend, from sarpebe-backend/
python -m venv .venv && .venv\Scripts\activate      # Unix: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                                # fill in the values
alembic upgrade head
python -m scripts.seed_users                        # an admin and a teacher
uvicorn app.main:app --reload --port 8000
celery -A app.tasks.celery_app worker --loglevel=info    # second terminal

# frontend, from sarpebe-frontend/
pnpm install
cp .env.local.example .env.local                    # fill in NEXTAUTH_SECRET
pnpm dev
```

Open http://localhost:3000. The full walkthrough, including uploading a first document and generating a plan, is in [docs/getting-started.md](docs/getting-started.md).

## Documentation

All detailed documentation is in [docs/](docs/README.md):

| Document | Contents |
|---|---|
| [Architecture](docs/architecture.md) | System, layers, end-to-end flows. |
| [Getting started](docs/getting-started.md) | Setup and first lesson plan. |
| [Configuration](docs/configuration.md) | Every environment variable and constant. |
| [Operations](docs/operations.md) | Running, deploying, migrating, reindexing, monitoring. |
| [API reference](docs/api-reference.md) | Endpoints, bodies, error codes. |
| [Authentication and security](docs/authentication-security.md) | Tokens, sessions, rate limiting, security model. |
| [AI pipeline](docs/ai-pipeline.md) | Ingestion, retrieval, generation, checks, failures, costs, export. |
| [AI evaluation](docs/ai-evaluation.md) | Measuring retrieval and generation quality. |
| [Database](docs/database.md) | Schema, indexes, migrations. |
| [Frontend](docs/frontend.md) | Routes, data flow, editors. |
| [Design system](docs/design-system.md) | Visual language, motion, copy. |
| [Testing](docs/testing.md) | Running and writing tests. |
| [Troubleshooting](docs/troubleshooting.md) | Common problems and fixes. |

Application READMEs: [sarpebe-backend/README.md](sarpebe-backend/README.md), [sarpebe-frontend/README.md](sarpebe-frontend/README.md).

## Contributing

Use Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf` with scopes `frontend`, `backend`, `db`, `api`, `rag`, `auth`, `docs`). Run `pytest` for backend changes and `npx tsc --noEmit`, `pnpm lint`, `pnpm build` for frontend changes. Never commit `.env` files or secrets. Code conventions are in `.claude/rules/`.
