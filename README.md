# SARPEBE
**Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum**

SARPEBE is an Educational SaaS designed to automate curriculum-aligned lesson plans via Retrieval-Augmented Generation (RAG) with zero hallucinations. All generated lesson plans are strictly grounded in and cited from official curriculum documents.

## Project Architecture

This repository is structured as a monorepo containing both the frontend and backend applications.

### Frontend (Next.js)
- **Directory:** [sarpebe-frontend/](sarpebe-frontend/)
- The frontend application is built using **Next.js**. It serves as the main user interface for educators to interact with the SaaS, manage their generated lesson plans, and upload curriculum documents.

### Backend (FastAPI)
- **Directory:** [sarpebe-backend/](sarpebe-backend/)
- The backend is a high-performance REST API built with **FastAPI**. It handles the RAG orchestration, AI model integrations, and database operations.

#### Tech Stack
- **API Framework:** FastAPI (Python 3.11+)
- **Database & Auth:** Supabase (PostgreSQL + JWT Authentication)
- **Vector DB:** pgvector (PostgreSQL extension for semantic search)
- **AI Engine:** Google Gemini API via official Google GenAI SDK
- **Background Tasks:** Celery + Redis (for asynchronous LLM calls)
- **ORM & Migrations:** SQLAlchemy 2.0 + Alembic

#### Core Features
- **Retrieval-Augmented Generation (RAG):** Pre-filtering by metadata (grade, subject) before semantic chunking and computing vector distances.
- **Asynchronous Processing:** Gemini API requests are offloaded to Celery workers, returning `202 Accepted` to keep the HTTP threads unblocked.
- **Cost Observability:** Every LLM request logs `prompt_tokens`, `completion_tokens`, and fiat costs to the database.

## Documentation

For deeper technical context, refer to the following internal documentation:
- [AI Persona & Engineering Directives](sarpebe-backend/AGENTS.md)
- [Database Schema & Architecture](sarpebe-backend/docs/DATABASE.md)
