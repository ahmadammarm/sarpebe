# SARPEBE Backend
**FastAPI REST API**

The backend for SARPEBE is a high-performance, asynchronous REST API that handles all business logic, RAG orchestration, AI generation, and database operations. It is designed for a multi-tenant SaaS environment with strict security, cost observability, and non-blocking AI processing.

---

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| FastAPI | latest | Async HTTP API framework |
| Python | 3.11+ | Runtime |
| Supabase | — | PostgreSQL database + JWT Auth |
| pgvector | — | Vector similarity search extension |
| Google Gemini API | — | LLM generation + text embeddings |
| SQLAlchemy | 2.0 | Async ORM |
| Alembic | latest | Database migrations |
| Celery | latest | Background task queue |
| Redis | latest | Celery broker + result backend |
| Pydantic | v2 | Request/response validation |

---

## Project Structure

The project follows Clean Architecture with strict layer separation. Each layer is allowed to talk only to the layer directly below it.

```
sarpebe-backend/
├── app/
│   ├── main.py                     # App entrypoint: registers routers, middleware, lifespan
│   ├── config.py                   # Centralized settings via pydantic-settings (reads .env)
│   │
│   ├── api/
│   │   ├── deps.py                 # Shared FastAPI Depends(): get_db, get_current_user
│   │   └── v1/
│   │       └── routers/
│   │           ├── auth.py         # /auth — login, register, token refresh
│   │           ├── lesson_plans.py # /lesson-plans — CRUD + generation trigger
│   │           ├── curriculum.py   # /curriculum — document upload and management
│   │           └── users.py        # /users — profile management
│   │
│   ├── core/
│   │   ├── security.py             # JWT validation, Supabase token verification
│   │   ├── exceptions.py           # App-wide custom exception classes
│   │   └── services/               # Business logic layer (no SQL, no HTTP here)
│   │       ├── lesson_plan_service.py  # Coordinates RAG + generation flow
│   │       ├── rag_service.py          # Retrieval: pre-filter + vector search
│   │       ├── embedding_service.py    # Generates Gemini text embeddings
│   │       └── llm_service.py          # Gemini API calls, token counting, cost calculation
│   │
│   ├── db/
│   │   ├── session.py              # AsyncEngine + AsyncSession factory
│   │   ├── base.py                 # SQLAlchemy declarative base
│   │   ├── models/                 # ORM table definitions
│   │   │   ├── profile.py
│   │   │   ├── lesson_plan.py
│   │   │   ├── curriculum_document.py
│   │   │   ├── document_chunk.py
│   │   │   └── llm_cost_log.py
│   │   └── repositories/           # Pure DB access (CRUD + pgvector queries)
│   │       ├── base_repository.py      # Generic CRUD — shared by all repositories (DRY)
│   │       ├── lesson_plan_repository.py
│   │       ├── document_chunk_repository.py
│   │       └── user_repository.py
│   │
│   ├── schemas/                    # Pydantic V2 I/O models
│   │   ├── common.py               # Shared types: pagination, base API response
│   │   ├── lesson_plan.py
│   │   ├── curriculum.py
│   │   └── user.py
│   │
│   ├── tasks/                      # Celery async task definitions
│   │   ├── celery_app.py           # Celery app factory and configuration
│   │   └── generation_tasks.py     # Async lesson plan generation task
│   │
│   └── utils/                      # Pure utility functions (no business logic)
│       ├── chunking.py             # Semantic text chunking by logical boundaries
│       └── cost_calculator.py      # Token-to-fiat cost formula
│
├── alembic/                        # Alembic migration environment
│   └── versions/                   # Auto-generated migration scripts
├── tests/
│   ├── unit/                       # Unit tests per service/repository
│   └── integration/                # End-to-end API tests
├── docs/
│   └── DATABASE.md                 # Full database schema and architecture
├── AGENTS.md                       # AI engineering directives
├── .env.example
├── requirements.txt
└── Dockerfile
```

---

## Layered Architecture

```
Router (api/v1/routers/)
  |
  | calls
  v
Service (core/services/)
  |
  | calls
  v
Repository (db/repositories/)
  |
  | SQL / pgvector
  v
Supabase — PostgreSQL + pgvector
```

Routers handle HTTP concerns only (validation, auth injection, response formatting). Services contain all business logic. Repositories contain all database access. No layer skips another.

---

## DRY Principles Applied

- `base_repository.py` implements generic `get`, `get_multi`, `create`, `update`, and `delete` methods. Domain-specific repositories inherit from it and only add their own specialized queries.
- `api/deps.py` centralizes all `Depends()` declarations. Auth checks and DB session injection are never duplicated across routers.
- `config.py` is the single source of truth for all environment variables. Nothing reads from `os.environ` directly — everything goes through the settings object.
- `schemas/common.py` defines shared Pydantic types (paginated responses, base error models) used across all endpoints.
- `utils/cost_calculator.py` centralizes the token-to-cost formula so it cannot diverge between generation and embedding operations.

---

## Key Engineering Decisions

**Async LLM Processing**
Gemini API calls take 10–30 seconds. Routers immediately return `202 Accepted` with a `job_id`. Celery workers execute the RAG pipeline and generation in the background. Clients poll the job status endpoint until the result is ready.

**RAG Pre-Filtering**
Vector similarity search is always preceded by a SQL `WHERE` clause filtering by `grade_level` and `subject`. This avoids computing cosine distances across the entire embedding table and keeps search accurate and fast as the dataset scales.

**Pessimistic Locking for Quotas**
When checking and decrementing a user's generation quota, the repository uses `SELECT ... FOR UPDATE` (`with_for_update()`) to prevent race conditions from concurrent requests double-spending quota.

**Connection Pooling**
In production, the app connects to Supabase via the Supavisor connection pooler (port 6543, transaction mode) rather than directly to PostgreSQL. SQLAlchemy's `pool_size` and `max_overflow` are tuned to match the pooler's capacity.

**Cost Logging**
Every call to the Gemini API — whether for generation or embedding — records `prompt_tokens`, `completion_tokens`, `operation_type`, and `total_cost` in the `llm_cost_logs` table, enabling per-user billing and spend analytics.

---

## Database Schema

Refer to [docs/DATABASE.md](docs/DATABASE.md) for the full ERD, table definitions, index strategy, Row Level Security policies, and architectural trade-off rationale.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Redis (for Celery)
- A Supabase project with `pgvector` extension enabled

### Installation

```bash
cd sarpebe-backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase PostgreSQL connection string (Supavisor port 6543) |
| `SUPABASE_JWT_SECRET` | JWT secret from your Supabase project settings |
| `GEMINI_API_KEY` | Google Gemini API key |
| `REDIS_URL` | Redis connection URL for Celery |
| `GEMINI_EMBEDDING_MODEL` | Embedding model name (e.g. `text-embedding-004`) |
| `GEMINI_GENERATION_MODEL` | Generation model name (e.g. `gemini-1.5-pro`) |

### Running Database Migrations

```bash
alembic upgrade head
```

### Running the API Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000).  
Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Running the Celery Worker

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

---

## API Endpoints (Overview)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/v1/users/me` | Get current user profile |
| `GET` | `/api/v1/lesson-plans` | List lesson plans (paginated) |
| `POST` | `/api/v1/lesson-plans` | Trigger async lesson plan generation |
| `GET` | `/api/v1/lesson-plans/{id}` | Get a single lesson plan |
| `GET` | `/api/v1/lesson-plans/jobs/{job_id}` | Poll background job status |
| `POST` | `/api/v1/curriculum/upload` | Upload a curriculum document (PDF) |
| `GET` | `/api/v1/curriculum` | List uploaded curriculum documents |

---

## Related

- [Main Repository README](../README.md)
- [Frontend — sarpebe-frontend](../sarpebe-frontend/README.md)
- [Database Schema](docs/DATABASE.md)
- [Engineering Directives](AGENTS.md)
