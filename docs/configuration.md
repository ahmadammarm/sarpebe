# Configuration

All backend settings are fields of `Settings` in `sarpebe-backend/app/config.py`, read from environment variables (names are the field names in upper case) or from `sarpebe-backend/.env`. Unknown variables in `.env` are ignored. `.env.example` lists every variable; copy it to `.env`. Never commit `.env`.

## Backend

### Required (the app does not start without them)

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL with the asyncpg driver, for example `postgresql+asyncpg://user:pass@host:6543/postgres`. In production use the Supabase transaction pooler (port 6543). |
| `SUPABASE_URL` | Project URL. Used for Storage only. |
| `SUPABASE_SERVICE_ROLE_KEY` | Service key for Storage uploads. Keep it server-side. |
| `GEMINI_API_KEY` | Google Gemini API key. |
| `REDIS_URL` | Celery broker and result backend, and login rate-limit counters. `rediss://` URLs get relaxed certificate checking for hosted Redis. |
| `AUTH_JWT_SECRET` | Signs access tokens; at least 32 characters. Changing it signs everyone out. |

### Models

| Variable | Default | Meaning |
|---|---|---|
| `GEMINI_GENERATION_MODEL` | `gemini-3.8-flash` | Writes the Modul Ajar. |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | Document and query embeddings (truncated to 768 dimensions). |
| `GEMINI_RERANK_MODEL` | `gemini-2.5-flash-lite` | Scores passage relevance. Small and cheap on purpose. |
| `GEMINI_JUDGE_MODEL` | `gemini-3.8-flash` | Only used by `python -m evals.run generation --judge`. |

### Retrieval

| Variable | Default | Meaning |
|---|---|---|
| `RAG_CANDIDATE_K` | 20 | Candidates fetched by each of vector and keyword search. |
| `RAG_RERANK_SHORTLIST` | 12 | Fused candidates sent to the reranker. |
| `RAG_TOP_K` | 6 | Passages given to the generator at most. |
| `RAG_MIN_SIMILARITY` | 0.45 | Cosine similarity floor. Calibrate with `python -m evals.run retrieval`; see [ai-evaluation.md](ai-evaluation.md). |
| `RAG_CONTEXT_MAX_CHARS` | 14000 | Total size of passages in the prompt. |
| `RAG_USE_RERANK` | true | Turn the reranker off to compare, or if its model is unavailable. |
| `RAG_HNSW_ITERATIVE_SCAN` | true | Sets `hnsw.iterative_scan` (pgvector 0.8 or newer) so filtered searches still return enough rows. |
| `EMBEDDING_USE_TASK_TYPES` | false | Send document or query task types to the embedding model. It may ignore them, so enable only after the retrieval eval shows a gain. |

### Generation

| Variable | Default | Meaning |
|---|---|---|
| `GENERATION_THINKING_LEVEL` | `MEDIUM` | `MINIMAL`, `LOW`, `MEDIUM`, `HIGH`, or empty to use the model default. Higher is slower and costlier. |
| `GENERATION_MAX_OUTPUT_TOKENS` | 16000 | Output limit. A full multi-meeting module needs a large budget; hitting it fails the job with a clear message. |
| `GENERATION_TEMPERATURE` | unset | Unset means the model default. |
| `PROMPT_VERSION` | `lesson_plan.v2` | Stored on every plan. Change it whenever the prompt or schema changes. |
| `LLM_MAX_ATTEMPTS` | 3 | Attempts per model call for transient errors only (429, 408, 5xx, timeouts). |

### Authentication

| Variable | Default | Meaning |
|---|---|---|
| `AUTH_JWT_ISSUER` | `sarpebe` | The `iss` claim; tokens with another issuer are rejected. |
| `ACCESS_TOKEN_TTL_MINUTES` | 15 | Access token lifetime. |
| `REFRESH_TOKEN_TTL_DAYS` | 14 | Refresh token lifetime. |
| `REFRESH_REUSE_GRACE_SECONDS` | 30 | A just-rotated refresh token presented again inside this window is treated as two tabs refreshing together, not theft. |
| `VERIFICATION_TOKEN_TTL_HOURS` | 24 | Email verification link lifetime. |
| `RESET_TOKEN_TTL_MINUTES` | 60 | Password reset link lifetime. |
| `REQUIRE_EMAIL_VERIFICATION` | true | Users must open the emailed link before signing in. |
| `LOGIN_MAX_FAILED_ATTEMPTS` | 5 | Failed logins allowed per email address before lockout (counted in Redis). |
| `LOGIN_LOCKOUT_MINUTES` | 15 | Lockout window. |

### Email

| Variable | Default | Meaning |
|---|---|---|
| `FRONTEND_URL` | `http://localhost:3000` | Base of the links inside emails. |
| `EMAIL_BACKEND` | `console` | `console` only logs emails (development). Use `smtp` in production, or nobody receives verification and reset links. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | -, 587, -, - | SMTP server credentials. |
| `SMTP_FROM` | `SARPEBE <no-reply@sarpebe.local>` | Sender. |
| `SMTP_USE_STARTTLS` | true | STARTTLS on connect. |

### HTTP and uploads

| Variable | Default | Meaning |
|---|---|---|
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON list of allowed browser origins. |
| `MAX_UPLOAD_MB` | 20 | Maximum PDF size. The frontend limit (`MAX_UPLOAD_MB` in `lib/utils/validators.ts`) should match. |

### Seeding (only for `scripts.seed_users`)

`SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, `SEED_USER_EMAIL`, `SEED_USER_PASSWORD`. An empty password is generated and printed once. The script reads them from the environment or `.env`; they are not part of `Settings`.

## Frontend

Defined in `sarpebe-frontend/.env.local` (copy `.env.local.example`). Never commit it.

| Variable | Meaning |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL, used by the browser and by NextAuth on the server. |
| `NEXTAUTH_URL` | Public URL of the frontend. |
| `NEXTAUTH_SECRET` | Signs the session cookie, which also carries the access and refresh tokens. Required. |

## Fixed values worth knowing

These are constants in code, not settings:

| Value | Where | Meaning |
|---|---|---|
| Embedding size 768 | `embedding_service.py`, `document_chunk.py` | Changing it needs a migration and a full reindex. |
| Reciprocal rank fusion k = 60 | `retrieval/fusion.py` | Standard constant. |
| Rerank keep score 2 or higher | `retrieval/passages.py` | Scores run 0 to 3. |
| Generation task limits 420 s soft, 480 s hard | `generation_tasks.py` | Two model calls plus rerank plus a possible repair. |
| Ingestion task limits 1500 s soft, 1800 s hard | `curriculum_tasks.py` | Large PDFs. |
| Plan timeout 15 minutes | `lesson_plan_service.py` | An unfinished plan older than this is reported as failed. |
| Meetings 1 to 6, minutes 20 to 240, notes up to 500 characters | `schemas/lesson_plan.py` | Request limits, mirrored in the frontend Zod schema. |

## Choosing values for production

- `EMAIL_BACKEND=smtp` with working credentials, and a real `FRONTEND_URL`.
- A long random `AUTH_JWT_SECRET` and `NEXTAUTH_SECRET`, kept in a secret manager.
- `CORS_ORIGINS` listing only the real frontend origin.
- `DATABASE_URL` through the pooler. See [operations.md](operations.md).
