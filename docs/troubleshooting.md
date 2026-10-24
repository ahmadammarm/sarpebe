# Troubleshooting

Symptoms, causes, and fixes, ordered by area. Most come from problems that actually occurred while building the project.

## Starting the services

| Symptom | Cause | Fix |
|---|---|---|
| API exits at startup with a validation error naming `auth_jwt_secret` | `AUTH_JWT_SECRET` missing or shorter than 32 characters. | Set it in `sarpebe-backend/.env` (`python -c "import secrets; print(secrets.token_urlsafe(48))"`). |
| Other `ValidationError` for `database_url`, `gemini_api_key`, `redis_url`, `supabase_*` | A required variable is missing. | Compare `.env` with `.env.example`; see [configuration.md](configuration.md). |
| Worker starts but jobs stay `pending` | The worker is not running, or API and worker use different `REDIS_URL`. | Start `celery -A app.tasks.celery_app worker --loglevel=info`; use the same Redis URL in both. On Windows add `--pool=solo`. |
| Frontend sign-in fails immediately or the session is empty | `NEXTAUTH_SECRET` or `NEXTAUTH_URL` missing in `.env.local`. | Fill them in and restart `pnpm dev`. |
| Browser shows CORS errors | The frontend origin is not in `CORS_ORIGINS`. | Add it (a JSON list) and restart the API. |
| `pnpm build` or dev server complains about stale types in `.next/types` after moving routes | Cached generated types. | Delete `sarpebe-frontend/.next` and rebuild. |

## Accounts and sign-in

| Symptom | Cause | Fix |
|---|---|---|
| "Email Anda belum diverifikasi" | `REQUIRE_EMAIL_VERIFICATION=true` and the link was not opened. | With `EMAIL_BACKEND=console` copy the link from the API log; or create a verified account with `scripts.create_user`; or request a new link. |
| No verification or reset email arrives | `EMAIL_BACKEND=console` logs emails instead of sending, or SMTP settings are wrong. | Use `EMAIL_BACKEND=smtp` with valid `SMTP_*`. Note the limit of 3 emails per hour per address. |
| "Terlalu banyak percobaan" | 5 failed logins for that email; locked for 15 minutes. | Wait, or sign in correctly once the window ends; a password reset also clears it. |
| Signed out unexpectedly | Refresh token expired, revoked (logout elsewhere or password reset), or replayed. | Sign in again. If it happens constantly, check that the API and the frontend clocks are sane and that `AUTH_JWT_SECRET` did not change. |
| Imported account cannot sign in | Its `password_hash` is null. | Use "Lupa password" to set one. |
| Login throttling does not work | Redis unreachable; counters fail open (a warning appears in the log). | Fix Redis; see [authentication-security.md](authentication-security.md). |

## Uploading documents

| Symptom | Cause | Fix |
|---|---|---|
| "File tidak dapat diunggah" | Not a real PDF (header check), larger than `MAX_UPLOAD_MB`, or Storage failed. | Check the file; check the bucket `sarpebe-storage` exists and is public; check the service role key. |
| Document ends `failed` | See the reason in `ingest_warnings`: unreadable PDF, no text and OCR could not read the pages, or an unexpected error (see the worker log). | For a scan, press "Proses ulang" once the model API is reachable, or upload a clearer file. Check `OCR_ENABLED` and `GEMINI_OCR_MODEL` if OCR never succeeds. |
| Completed with "N halaman dibaca dengan OCR" | Those pages were scans and were transcribed by the model. | Read the document's chunks or a generated module for mistakes (numbers, table cells); replace the file with a text PDF if accuracy matters. |
| Completed but with "tidak berisi teks" warnings | Those pages could not be read: past `OCR_MAX_PAGES`, blank, refused by the model, or OCR is off. | Acceptable if those pages are not needed; otherwise raise `OCR_MAX_PAGES`, reprocess, or replace the file. |
| OCR is slow or fails with rate limits | `OCR_CONCURRENCY` pages are sent at once. | Lower `OCR_CONCURRENCY`; transient errors are retried up to `LLM_MAX_ATTEMPTS` times and then the page is skipped. |
| Chunks lack headings or tables after an upgrade | The document was ingested by version 1. | `python -m scripts.reindex_documents --all`. |

## Generating plans

| Symptom | Cause | Fix |
|---|---|---|
| Worker log "Retrieved 0 chunks" or failure "Belum ada dokumen kurikulum untuk kelas dan mata pelajaran ini." | No chunks have exactly these normalized labels. The usual cause is label mismatch: a document uploaded as `seluruh kelas` or `semua mapel` never matches a request for `9` and `IPS`. | Delete the document and upload it again with the exact labels teachers use (kelas as a number, the subject name). Check with `SELECT grade_level, subject, count(*) FROM document_chunks GROUP BY 1,2;`. |
| "Dokumen kurikulum yang tersedia belum membahas topik ini." | Documents exist for the labels but nothing relevant was found: the topic is outside them, or `RAG_MIN_SIMILARITY` is too high. | Try a topic that the CP covers; calibrate the floor with the retrieval evaluation ([ai-evaluation.md](ai-evaluation.md)). |
| "Model belum menghasilkan modul yang valid, bahkan setelah diperbaiki." | Output stayed invalid after the one repair (for example wrong number of meetings). | Retry ("Buat ulang"). If frequent, run the generation evaluation and review the prompt or lower `GENERATION_THINKING_LEVEL`. |
| Message about truncated output | `GENERATION_MAX_OUTPUT_TOKENS` too low for the number of meetings. | Raise it, or reduce meetings. |
| "Layanan model sedang sibuk" | Gemini returned 429 or 5xx through all retries. | Try again later; check quota and key. |
| Plan completes with warnings about minutes | Activity minutes do not add up to the target. | Edit the minute cells; the editor shows a running total. |
| A plan stays `processing` then fails after 15 minutes | Worker died or hung. | Check the worker log; restart the worker; retry the plan. |
| `UnicodeEncodeError` during PDF export | An old build used the core PDF font. | The v2 export bundles DejaVu fonts (`app/assets/fonts`); make sure they are present and the code is up to date. |

## Database

| Symptom | Cause | Fix |
|---|---|---|
| `relation ... does not exist` or `column ... does not exist` | Migrations not applied. | `alembic upgrade head` from `sarpebe-backend/`. |
| `type "vector" does not exist` | `vector` extension not enabled. | Enable it in Supabase (Database, Extensions). |
| "Too many connections" under load | Connecting to port 5432 instead of the pooler, or too many API workers for the pooler. | Use port 6543; reduce workers or pool sizes ([operations.md](operations.md)). |
| Filtered vector search returns fewer rows than expected | pgvector older than 0.8 (no iterative scan). | Upgrade pgvector; the setting `RAG_HNSW_ITERATIVE_SCAN` only applies to 0.8 or newer. |
| Task errors about event loops or closed connections | Using the module-level engine inside a Celery task. | Tasks must use `task_session_scope()` ([backend rules](../.claude/rules/backend-pattern.md)). |

## Frontend

| Symptom | Cause | Fix |
|---|---|---|
| Progress never advances | SSE blocked by a proxy; polling should take over within seconds. | Disable response buffering for `/api/lesson-plans/jobs/*/stream`. |
| Theme switch has no circular animation | Browser lacks the View Transitions API, or reduced motion is on. | Expected; the switch is instant then. |
| Import of a constant from a `"use client"` file into a server component renders nothing useful | Client references are not plain values on the server. | Move shared constants to a plain module without `"use client"` (as `components/landing/menu.ts` does). |

## Collecting information for a bug report

- The plan's row: `SELECT status, generated_content->>'error', generation_meta, prompt_version, model_name FROM lesson_plans WHERE id = '<id>';`
- The worker log lines for the plan id.
- `llm_cost_logs` rows for the plan to see which calls happened.
- The request options (`request_options`) and the labels of the documents involved.
