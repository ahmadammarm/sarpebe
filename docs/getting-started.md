# Getting started

This guide takes a new machine to a working local setup: backend, worker, frontend, one admin, one teacher, and a first generated lesson plan.

## Prerequisites

| Tool | Version | Used for |
|---|---|---|
| Python | 3.11 or newer | Backend and worker |
| Node.js | 20 or newer | Frontend |
| pnpm | current | Frontend package manager |
| Redis | 6 or newer | Celery broker and rate limiting (local, Docker, or a hosted URL) |
| A Supabase project | - | PostgreSQL with the `vector` extension, and Storage |
| A Gemini API key | - | Embeddings, rerank, generation |

Supabase setup, once:

1. Create a project and enable the `vector` extension (Database, Extensions).
2. Create a **public** Storage bucket named `sarpebe-storage`.
3. Copy the pooled connection string (port 6543, transaction mode), the project URL, and the service role key.

## 1. Backend

Run from `sarpebe-backend/`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Unix: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the values
```

Required values in `.env`: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `REDIS_URL`, `AUTH_JWT_SECRET` (at least 32 characters; generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`). The full list with defaults is in [configuration.md](configuration.md).

Create the schema:

```bash
alembic upgrade head
```

Create the first accounts (an admin and a teacher), using the `SEED_*` values from `.env`:

```bash
python -m scripts.seed_users
```

A password left empty in `.env` is generated and printed once. For a single account use `python -m scripts.create_user`; to change a role use `python -m scripts.upgrade_user`.

Start the API and the worker in two terminals:

```bash
uvicorn app.main:app --reload --port 8000
celery -A app.tasks.celery_app worker --loglevel=info
```

On Windows the worker may need `--pool=solo`. Interactive API docs are at `http://localhost:8000/docs`.

## 2. Frontend

Run from `sarpebe-frontend/`.

```bash
pnpm install
cp .env.local.example .env.local     # fill in NEXTAUTH_SECRET (openssl rand -base64 32)
pnpm dev
```

Open `http://localhost:3000`. `NEXT_PUBLIC_API_BASE_URL` must point to the backend (`http://localhost:8000` by default).

## 3. First lesson plan

1. Sign in as the admin and open **Dokumen kurikulum** (`/curriculum`, visible to admins only).
2. Upload a CP PDF. Use the exact labels you will use later: kelas as a number (for example `9`) and the subject name (for example `IPS`). Labels are matched exactly after normalization, so `9` and `seluruh kelas` are different. Wait until the status is completed.
3. Sign out and sign in as the teacher (or use another browser).
4. Open **Modul ajar**, then **Modul ajar baru**, enter the same kelas and mata pelajaran, a topic that the document covers, and the meeting options.
5. The progress shows the real stages: finding relevant parts, drafting, checking. When it finishes the editor opens.

If email verification is required (`REQUIRE_EMAIL_VERIFICATION=true`) and `EMAIL_BACKEND=console`, the verification link for a newly registered account is printed in the API log instead of being emailed. Seeded accounts are already verified.

## Running the checks

```bash
# backend, from sarpebe-backend/
pytest

# frontend, from sarpebe-frontend/
npx tsc --noEmit
pnpm lint
pnpm build
```

## Existing documents after an upgrade

Documents ingested before ingestion v2 (`curriculum_documents.ingest_version = 1`) still work but lack headings, table chunks and normalized embeddings. Re-ingest them from storage:

```bash
python -m scripts.reindex_documents            # only documents on an older version
python -m scripts.reindex_documents --all      # or --id <document uuid>
```

## Where to go next

- How the system fits together: [architecture.md](architecture.md)
- Every setting: [configuration.md](configuration.md)
- Running it in production: [operations.md](operations.md)
- When something does not work: [troubleshooting.md](troubleshooting.md)
