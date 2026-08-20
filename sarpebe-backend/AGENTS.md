# SARPEBE Backend: Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum

## 1. Project Context & AI Persona
You are an expert Python/FastAPI developer building an Educational SaaS. 
**Core Goal:** Automate curriculum-aligned lesson plans via Retrieval-Augmented Generation (RAG) with zero hallucinations. All output must strictly cite official curriculum documents.

## 2. Tech Stack & Tooling
- **API Framework:** FastAPI (Python 3.11+)
- **Database & Auth:** Supabase (PostgreSQL + JWT Authentication)
- **Vector DB:** pgvector (PostgreSQL extension)
- **AI Engine:** Google Gemini API (Pro/Flash for generation, Text Embeddings for RAG) via official Google GenAI SDK.
- **Background Tasks:** Celery + Redis
- **ORM & Migrations:** SQLAlchemy 2.0 + Alembic

## 3. Architecture (Clean Architecture)
Strictly separate concerns. Do not use Fat Controllers.
- `api/routers/`: HTTP routing, Pydantic validation, Auth injection.
- `core/services/`: Business logic, RAG orchestration, Gemini API calls, token counting. No SQL here.
- `db/repositories/`: Pure database access (CRUD) and pgvector similarity queries.
- `schemas/`: Pydantic V2 models for I/O validation.
- `db/models/`: SQLAlchemy ORM definitions.

## 4. Strict Engineering Directives
### A. RAG & Vector Search
- **Pre-filtering is Mandatory:** Always filter by metadata (`grade_level`, `subject`) via SQL *before* computing vector distances (`<=>` or `<->`).
- **Semantic Chunking:** Chunk by logical boundaries (paragraphs/sections), not arbitrary character counts.
- **Citations:** Instruct Gemini to append citations based on chunk metadata (`document_name`, `page_number`).

### B. API & Performance
- **Async LLM Flow:** Gemini API calls take 10-30s. Never block the main HTTP thread. Return `202 Accepted` with a `job_id`, process RAG via background tasks (Celery).
- **Pagination:** Always paginate list endpoints (`GET /lesson-plans`).

### C. Observability & Security
- **Cost Logging:** Every Gemini call MUST record `prompt_tokens`, `completion_tokens`, and calculate `total_cost` in the database.
- **Auth:** Validate Supabase JWTs in FastAPI using `Depends()`. Protect all private routes.

## 5. Coding Standards
- Use strict Python type hints (`-> dict`, `list[str]`, etc.).
- Catch specific exceptions and raise `fastapi.HTTPException`. Never leak raw DB errors.
- Document complex RAG logic with concise docstrings.
- Keep commits atomic and use Conventional Commits.
