# SARPEBE
**Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum**

SARPEBE is an educational platform that automates the generation of curriculum-aligned lesson plans for Indonesian educators. It leverages Retrieval-Augmented Generation (RAG) powered by Google Gemini to produce structured lesson plans grounded strictly in official curriculum documents (Capaian Pembelajaran, ATP, and Buku Guru), with every objective traceable to its source page.

---

## Overview

Traditional lesson plan creation is time-consuming and often inconsistent with the latest curriculum standards. SARPEBE solves this by allowing educators to specify a grade level, subject, and topic, then automatically generating a complete Modul Ajar (general information, learning objectives, per-meeting activity tables, assessment with rubric, enrichment and remedial, reflection, worksheet, reading material and glossary) in the background, with references taken from the uploaded official documents.

---

## Repository Structure

This repository is a monorepo containing two independent applications.

```
sarpebe/
├── sarpebe-frontend/   — Next.js 16 web application (user interface)
├── sarpebe-backend/    — FastAPI REST API (AI engine & business logic)
└── README.md
```

- [Frontend — sarpebe-frontend/](sarpebe-frontend/)
- [Backend — sarpebe-backend/](sarpebe-backend/)

---

## Architecture

The system follows a clean, layered architecture across both applications. Each layer communicates only with the layer directly beneath it.

```
Browser (Next.js)
    |
    | HTTP/REST
    v
API Layer (FastAPI Routers)
    |
    v
Service Layer (Business Logic, RAG Orchestration)
    |
    v
Repository Layer (Database Queries, pgvector Search)
    |
    v
Supabase (PostgreSQL + pgvector + Storage)
```

Long-running AI generation requests are offloaded to Celery background workers, keeping the API non-blocking. The frontend follows the job over Server-Sent Events and falls back to polling.

---

## Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend API | FastAPI, Python 3.11+ |
| Database | Supabase (PostgreSQL) |
| Search | pgvector (HNSW) + PostgreSQL Indonesian full-text search, fused by reciprocal rank fusion |
| AI Engine | Google Gemini API (structured generation, small-model rerank, embeddings) |
| Background Tasks | Celery + Redis |
| ORM & Migrations | SQLAlchemy 2.0 + Alembic |
| Auth | Backend-issued JWT access tokens + rotating refresh tokens (bcrypt passwords, `/api/auth/*`) |

---

## Core Features

**Curriculum-Grounded Generation**
Lesson plans are generated using RAG. PDFs are read with table-aware extraction; retrieval combines vector and keyword search, drops weak matches and reranks the rest. If the documents do not cover the topic, generation stops instead of inventing content. References are built by the server from the passages the model used, so a citation cannot be fabricated. The output is checked (table shape, minutes per meeting, source ids) and repaired once if needed.

**Measured Quality**
Offline evaluations (`python -m evals.run`) report retrieval hit rate and the right similarity floor, plus schema-valid, repair and grounding rates for real generations. Prompt and schema changes are versioned and compared against them. See [AI pipeline](sarpebe-backend/docs/AI.md).

**Asynchronous Processing**
AI generation takes about 20–60 seconds. The API immediately returns `202 Accepted` with a `job_id`. A Celery worker handles the generation in the background and records its stage (retrieving, drafting, repairing). The frontend follows the job until the plan is ready.

**Cost Observability**
Every call to the Gemini API records `prompt_tokens`, `completion_tokens`, and the calculated fiat cost to the database, enabling usage and cost analytics.

**Multi-Tenant Security**
Every query is scoped to the authenticated user in the repository layer (the API connects with a privileged database role, so Supabase Row Level Security is not relied on). UUIDs are used as primary keys to prevent ID enumeration attacks.

---

## Getting Started

Refer to the individual README files for setup instructions:

- [Frontend Setup](sarpebe-frontend/README.md)
- [Backend Setup](sarpebe-backend/README.md)

---

## Documentation

- [Backend Engineering Directives](sarpebe-backend/AGENTS.md)
- [AI Pipeline: RAG, prompts, evaluations](sarpebe-backend/docs/AI.md)
- [Database Schema & Architecture](sarpebe-backend/docs/DATABASE.md)
