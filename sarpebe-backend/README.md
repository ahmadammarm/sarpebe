# SARPEBE Backend

FastAPI REST API, Celery worker, migrations and evaluation harness for SARPEBE. It handles authentication, curriculum ingestion, retrieval-augmented generation of lesson plans with Google Gemini, PDF export, and cost logging.

This file is a short orientation. The full documentation is in the repository's [docs](../docs/README.md) folder.

## Stack

FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, Supabase PostgreSQL with pgvector, Supabase Storage, Celery and Redis, Google GenAI SDK, pdfplumber and pypdf, fpdf2.

## Layout

```
sarpebe-backend/
  app/
    api/            routers and dependencies (HTTP only)
    core/           security, rate limiting, storage, llm_client, prompts, services/
    db/             session, models, repositories
    schemas/        Pydantic request, response and content models
    tasks/          Celery app, generation and ingestion tasks
    utils/          PDF reading, chunking, labels, fase, cost math, PDF export
    assets/fonts/   bundled DejaVu fonts for PDF export
  alembic/          migrations
  evals/            offline evaluation harness
  scripts/          seed_users, create_user, upgrade_user, reindex_documents
  tests/            unit and integration tests
```

Layers: Router -> Service -> Repository -> Database. See [architecture](../docs/architecture.md).

## Run it

```bash
python -m venv .venv && .venv\Scripts\activate     # Unix: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                               # required: DATABASE_URL, SUPABASE_*, GEMINI_API_KEY, REDIS_URL, AUTH_JWT_SECRET
alembic upgrade head
python -m scripts.seed_users
uvicorn app.main:app --reload --port 8000          # docs at http://localhost:8000/docs
celery -A app.tasks.celery_app worker --loglevel=info
```

Run the tests with `pytest` (no network, Gemini key, Redis or PostgreSQL needed).

## More

| Topic | Document |
|---|---|
| Setup walkthrough | [getting-started](../docs/getting-started.md) |
| Every setting | [configuration](../docs/configuration.md) |
| Endpoints and error codes | [api-reference](../docs/api-reference.md) |
| Tokens and security | [authentication-security](../docs/authentication-security.md) |
| RAG, prompts, generation | [ai-pipeline](../docs/ai-pipeline.md), [ai-evaluation](../docs/ai-evaluation.md) |
| Schema and migrations | [database](../docs/database.md) |
| Running in production | [operations](../docs/operations.md) |
| Tests | [testing](../docs/testing.md) |
| Problems | [troubleshooting](../docs/troubleshooting.md) |

Frontend: [sarpebe-frontend](../sarpebe-frontend/README.md). Project overview: [root README](../README.md).
