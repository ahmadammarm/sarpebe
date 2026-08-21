# SARPEBE — Monorepo Agent Guide

This file provides AI coding agents with context, rules, and conventions for working across the entire SARPEBE monorepo. Read the project-specific AGENTS.md in each subdirectory for deeper directives.

---

## Project Overview

SARPEBE (Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum) is an Educational SaaS that automates curriculum-aligned lesson plan generation for Indonesian educators. It uses Retrieval-Augmented Generation (RAG) powered by Google Gemini, grounded strictly on official curriculum documents.

---

## Repository Layout

```
sarpebe/
├── sarpebe-frontend/   — Next.js 16 + React 19 + TypeScript + Tailwind CSS
├── sarpebe-backend/    — FastAPI + Python 3.11 + Supabase + pgvector + Celery
├── README.md
└── AGENTS.md           — This file
```

Each application is fully independent. They communicate over HTTP only. Do not create shared code at the monorepo root.

---

## Monorepo Rules

- Never add shared source code, utilities, or configuration at the root level. Each application owns its own dependencies, types, and config.
- All changes to the frontend must be scoped to `sarpebe-frontend/`.
- All changes to the backend must be scoped to `sarpebe-backend/`.
- README files exist at the root, in `sarpebe-frontend/`, and in `sarpebe-backend/`. Keep all three up to date when making structural changes.

---

## Coding Principles (Applies to Both Projects)

### DRY (Don't Repeat Yourself)
- Before writing any utility, validation, type, or helper — search whether it already exists in that project. Reuse or extend it rather than duplicating.
- Identify repeated patterns across files and consolidate them into shared modules within their respective project layer (e.g., `base_repository.py` in backend, `lib/api/client.ts` in frontend).

### Layered Architecture
- Both projects enforce strict layer separation. Each layer may only call the layer directly beneath it.
- Backend: Router → Service → Repository → Database
- Frontend: Page → Hook → API Client → Backend HTTP
- Do not skip layers. A router must never query the database directly. A page must never call the API client directly.

### Naming Conventions
- Backend (Python): `snake_case` for files, functions, and variables. `PascalCase` for classes. Pydantic models suffixed with their role (e.g., `LessonPlanCreate`, `LessonPlanResponse`).
- Frontend (TypeScript): `PascalCase` for components and types. `camelCase` for functions and variables. File names match the primary export (e.g., `LessonPlanCard.tsx`).

---

## Commit Conventions

Use Conventional Commits format for all commits:

```
<type>(<scope>): <short description>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`
Scopes: `frontend`, `backend`, `db`, `api`, `rag`, `auth`, `docs`

Examples:
```
feat(backend): add async lesson plan generation endpoint
fix(frontend): correct job polling retry logic
docs(backend): update database schema documentation
refactor(backend): extract cost calculation into utility module
```

---

## What NOT to Do

- Do not commit `.env` files, secrets, or API keys.
- Do not add `node_modules/`, `.next/`, `__pycache__/`, or `.venv/` to git.
- Do not force-push to `main`.
- Do not write business logic inside routers (backend) or pages (frontend).
- Do not use `any` as a TypeScript type without a documented justification.
- Do not swallow exceptions silently — always log or re-raise with context.

---

## Subdirectory Agent Guides

- [Backend AGENTS.md](sarpebe-backend/AGENTS.md)
- [Frontend AGENTS.md](sarpebe-frontend/AGENTS.md)
