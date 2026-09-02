# SARPEBE
**Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum**

SARPEBE is an educational platform that automates the generation of curriculum-aligned lesson plans for Indonesian educators. It leverages Retrieval-Augmented Generation (RAG) powered by Google Gemini to produce structured lesson plans grounded strictly in official curriculum documents (Capaian Pembelajaran, ATP, and Buku Guru), with zero hallucinations.

---

## Overview

Traditional lesson plan creation is time-consuming and often inconsistent with the latest curriculum standards. SARPEBE solves this by allowing educators to specify a grade level, subject, and topic, then automatically generating a complete, standards-compliant lesson plan in the background — fully cited from uploaded official documents.

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
Supabase (PostgreSQL + pgvector + Auth)
```

Long-running AI generation requests are offloaded to Celery background workers, keeping the API non-blocking. The frontend polls job status until completion.

---

## Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend API | FastAPI, Python 3.11+ |
| Database | Supabase (PostgreSQL) |
| Vector Search | pgvector (HNSW index) |
| AI Engine | Google Gemini API (Pro / Flash + Text Embeddings) |
| Background Tasks | Celery + Redis |
| ORM & Migrations | SQLAlchemy 2.0 + Alembic |
| Auth | Supabase JWT (validated in FastAPI via Depends) |

---

## Core Features

**Curriculum-Grounded Generation**
Lesson plans are generated using RAG. The system retrieves the most semantically relevant chunks from official curriculum documents before sending context to Gemini, ensuring every output is traceable and cited.

**Asynchronous Processing**
AI generation can take 10–30 seconds. The API immediately returns `202 Accepted` with a `job_id`. A Celery worker handles the generation in the background. The frontend polls the job status endpoint until the plan is ready.

**Cost Observability**
Every call to the Gemini API records `prompt_tokens`, `completion_tokens`, and the calculated fiat cost to the database, enabling usage and cost analytics.

**Multi-Tenant Security**
Supabase Row Level Security (RLS) ensures users can only access their own data. UUIDs are used as primary keys to prevent ID enumeration attacks.

---

## Getting Started

Refer to the individual README files for setup instructions:

- [Frontend Setup](sarpebe-frontend/README.md)
- [Backend Setup](sarpebe-backend/README.md)

---

## Documentation

- [Backend Engineering Directives](sarpebe-backend/AGENTS.md)
- [Database Schema & Architecture](sarpebe-backend/docs/DATABASE.md)
