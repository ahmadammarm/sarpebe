# API reference

Base URL: `http://localhost:8000` in development. Every route is under `/api`. Interactive documentation generated from the code is served at `/docs` (Swagger) and `/redoc`.

## Conventions

**Authentication.** Protected routes need `Authorization: Bearer <access token>`, obtained from `POST /api/auth/login`. Access tokens last 15 minutes by default; renew with `POST /api/auth/refresh`. Routes marked *admin* also need the `admin` role (403 otherwise).

**Errors.** Domain errors return JSON with a human-readable English `detail` and a stable machine-readable `code`. Clients (including the frontend) should branch on `code`, never on `detail`.

```json
{ "detail": "Invalid email or password.", "code": "invalid_credentials" }
```

Request bodies that fail Pydantic validation return FastAPI's standard `422` with `detail` as a list of `{loc, msg, type}` items and no `code`. A plan update whose content fails schema validation returns `422` with `code: invalid_content`.

| `code` | Status | Raised when |
|---|---|---|
| `invalid_credentials` | 401 | Wrong email or password. |
| `invalid_token` | 401 | Access token missing, expired, malformed, wrong issuer or type, or the account was deleted. |
| `invalid_refresh_token` | 401 | Refresh token unknown, expired, revoked, or replayed after the grace window. |
| `email_not_verified` | 403 | Correct password but the address is not verified (only when verification is required). |
| `too_many_attempts` | 429 | Login lockout after repeated failures. |
| `quota_exceeded` | 429 | The user has started all the lesson plans allowed in the last 24 hours. |
| `invalid_email_token` | 400 | Verification or reset link invalid, used, or expired. |
| `not_owner` | 403 | Resource belongs to another user. |
| `forbidden` | 403 | The endpoint needs the admin role. |
| `account_disabled` | 403 | An administrator disabled the account. Raised at login (after a correct password), at refresh, and on any request that carries its access token. |
| `invalid_password` | 400 | The current password given for changing the password or deleting the account is wrong. Never 401, so a client does not mistake it for an expired session. |
| `user_not_found` | 404 | An administrator named a user that does not exist. |
| `last_admin` | 409 | The action would leave no active administrator (demoting, disabling or deleting the last one). |
| `self_action_forbidden` | 409 | An administrator tried to change their own role or status, or to delete themselves through the admin endpoint. |
| `lesson_plan_not_found` | 404 | No such plan or job for this user. |
| `document_not_found` | 404 | No such curriculum document. |
| `invalid_state` | 409 | Action not allowed in the resource's current status (for example exporting an unfinished plan). |
| `invalid_upload` | 400 | Not a PDF, bad magic bytes, too large, missing labels, or storage failure. |
| `invalid_content` | 422 | Edited plan content does not match the schema. |

The codes below never reach HTTP clients; they are stored as the failure text of a plan (see [ai-pipeline.md](ai-pipeline.md)): `insufficient_context`, `llm_output_invalid`, `content_blocked`, `llm_unavailable`.

**Timestamps** are ISO 8601 in UTC. **Ids** are UUIDs.

## Auth

None of these need a token. The endpoints that take an email answer the same way whether or not the account exists.

### `POST /api/auth/register` (202)
Body: `{ "email": string, "password": string (8 to 72 bytes), "full_name": string (2 to 100) }`. Creates an unverified account and emails a verification link. Response: `{ "message": "If the email can be registered, a verification link has been sent." }`, also when the email already exists.

### `POST /api/auth/login`
Body: `{ "email", "password" }` (no strength rules, so imported legacy passwords work). Response:

```json
{
  "access_token": "...", "refresh_token": "...", "token_type": "bearer",
  "expires_in": 900,
  "user": { "id": "uuid", "email": "a@b.id", "full_name": "Nama", "role": "user" }
}
```

Errors: `invalid_credentials`, `email_not_verified`, `too_many_attempts`.

### `POST /api/auth/refresh`
Body: `{ "refresh_token" }`. Rotates the pair: the old refresh token stops working (a replay within 30 seconds is tolerated, later replays revoke the whole session). Response as login. Error: `invalid_refresh_token`.

### `POST /api/auth/logout` (204)
Body: `{ "refresh_token" }`. Revokes the session the token belongs to. Unknown tokens are ignored.

### `POST /api/auth/verify-email`
Body: `{ "token" }` from the emailed link. Response `{ "message": "Email verified." }`. Error: `invalid_email_token`.

### `POST /api/auth/resend-verification` (202)
Body: `{ "email" }`. At most 3 emails per hour per address and purpose; beyond that the request still returns 202 and nothing is sent.

### `POST /api/auth/forgot-password` (202)
Body: `{ "email" }`. Same limits and same uniform response.

### `POST /api/auth/reset-password`
Body: `{ "token", "password" }`. Sets the password, marks the email verified, invalidates other reset links, and signs out every session of the user. Error: `invalid_email_token`.

## Users

### `GET /api/users/me`
The current profile: `id`, `email`, `full_name`, `school_name`, `subscription_tier`, `role`, `created_at`.

### `PATCH /api/users/me`
Body with `full_name` (2 to 100 characters, trimmed) and/or `school_name` (up to 150 characters; an empty string clears it); at least one is required. Role and tier cannot be changed here. Returns the profile.

### `POST /api/users/me/change-password` (204)
Body: `{ "current_password", "new_password" }` (the new one follows the usual rules: 8 characters, 72 bytes). Sets the new password, cancels unused reset links, and revokes every refresh token of the user, this device included, so the client must sign in again. Errors: `invalid_password` (400), `too_many_attempts` (429 after 5 wrong passwords in 15 minutes, counted together with account deletion).

### `DELETE /api/users/me` (204)
Body: `{ "password" }`. Deletes the account with its lesson plans, cost logs and sessions. Errors: `invalid_password`, `too_many_attempts`, `last_admin` (the only active administrator cannot delete themselves).

### `GET /api/users/me/quota`
How many lesson plans the user can still start:

```json
{ "limit": 10, "used": 7, "remaining": 3, "unlimited": false, "resets_at": "2026-10-25T08:30:00Z" }
```

`limit` and `remaining` are `null` and `unlimited` is `true` for admins, accounts on a tier other than `free`, and when `GENERATION_DAILY_LIMIT_FREE` is 0. The window is the last 24 hours and plans that failed are not counted. `resets_at` is when the oldest counted plan leaves the window and a slot frees up, or `null` if none is counted.

### `GET /api/users/me/costs`
Aggregated model usage of the current user: `{ "prompt_tokens": int, "completion_tokens": int, "total_cost": number }`.

### `GET /api/users/costs` (admin)
A list of `{ user_id, prompt_tokens, completion_tokens, total_cost }`, one per user.

### `GET /api/users?skip=0&limit=20&q=&role=` (admin)
`{ items, total, skip, limit }`, newest accounts first. `q` matches part of the name or email, ignoring case (at most 100 characters); `role` is `user` or `admin`. Each item has the profile fields plus `email_verified_at` and `disabled_at` (null while the account is active). Password hashes are never returned.

### `PATCH /api/users/{id}` (admin)
Body with any of `role` (`user`, `admin`), `subscription_tier` (`free`, `premium`) and `disabled` (boolean); at least one is required. Disabling signs the account out everywhere. Nobody can change their own role or status (`self_action_forbidden`), and the last active administrator cannot be demoted or disabled (`last_admin`). Returns the account. Error: `user_not_found`.

### `DELETE /api/users/{id}` (admin, 204)
Deletes another account with its lesson plans, cost logs and sessions. Errors: `user_not_found`, `self_action_forbidden` (use `DELETE /api/users/me` for your own account).

## Curriculum documents (admin)

### `POST /api/curriculum/upload` (202)
`multipart/form-data`: `file` (PDF), `grade_level` (text), `subject` (text), `document_type` (`CP`, `ATP`, or `BUKU_GURU`, default `CP`). The labels are normalized (trimmed, case-folded) and must match what teachers type. The file is validated (extension, `%PDF-` header, size), stored, and ingested in the background. Response: the document with `status: "processing"`.

```json
{ "id": "uuid", "title": "CP IPS.pdf", "document_type": "CP", "url_path": "https://...",
  "grade_level": "9", "subject": "ips", "status": "processing", "ingest_version": 2,
  "ingest_warnings": null, "uploaded_at": "..." }
```

`status` becomes `completed` or `failed`. Poll `GET /api/curriculum` for it. `ingest_warnings` lists page warnings for a completed document (for example "2 halaman dibaca dengan OCR; periksa hasilnya.") and holds the reason when `status` is `failed`.

### `GET /api/curriculum?skip=0&limit=20`
`{ items, total, skip, limit }` with documents newest first (same shape as above). `skip` is at least 0 and `limit` is 1 to 100.

### `PATCH /api/curriculum/{id}`
Body with any of `title`, `document_type`, `grade_level`, `subject`; at least one is required. Labels are normalized as at upload. Returns the document. A new `grade_level` or `subject` sets `status` to `processing` and processes the document again; a new title or type changes the row only. Errors: `document_not_found`, `invalid_state` (409) while the document is processing, 422 for an empty or invalid body.

### `POST /api/curriculum/{id}/reindex` (202)
Reads the stored PDF again and replaces the document's chunks (also retries a failed document). Returns the document with `status: "processing"`. Errors: `document_not_found`, `invalid_state` (409) while it is already processing.

### `DELETE /api/curriculum/{id}` (204)
Deletes the document, its chunks (cascade), and the stored file. Error: `document_not_found`.

## Lesson plans

All routes are scoped to the authenticated user; other users' plans return 404.

### `POST /api/lesson-plans` (202)
Body:

| Field | Type | Rules |
|---|---|---|
| `grade_level` | string | 1 to 20 characters, trimmed. |
| `subject` | string | 1 to 100 characters, trimmed. |
| `topic` | string | 1 to 300 characters, trimmed. |
| `meeting_count` | integer | 1 to 6, default 1. |
| `minutes_per_meeting` | integer | 20 to 240, default 80. |
| `teaching_model` | enum | `otomatis` (default), `diskusi_kelompok`, `pjbl`, `pbl`, `inkuiri`, `kooperatif`, `ceramah_interaktif`. |
| `class_notes` | string | Up to 500 characters, trimmed, default empty. |

Response: `{ "job_id": "string", "id": "uuid" }`. The plan row exists immediately with `status: "pending"`. Error: `quota_exceeded` (429) when the user has started `GENERATION_DAILY_LIMIT_FREE` plans in the last 24 hours (see `GET /api/users/me/quota`).

### `GET /api/lesson-plans?skip=0&limit=20`
`{ "items": [LessonPlan], "total": int, "skip": int, "limit": int }`, newest first.

### `GET /api/lesson-plans/{id}`
A `LessonPlan`:

```json
{
  "id": "uuid", "grade_level": "9", "subject": "IPS", "topic": "Pelaku ekonomi",
  "status": "completed",
  "schema_version": 2,
  "request_options": { "meeting_count": 2, "minutes_per_meeting": 80, "teaching_model": "pjbl", "class_notes": "" },
  "generated_content": { "...": "see below" },
  "created_at": "..."
}
```

`status` is `pending`, `processing`, `completed`, or `failed`. For a failed plan `generated_content` is `{ "error": "<Indonesian message>", "code": "<failure code>" }` (`code` is absent on plans that failed before codes existed).

`generated_content` depends on `schema_version`:

- **1** (older plans): `title`, `objectives[]`, `materials[]`, `activities[{duration, description}]`, `assessment`, `citations[]`.
- **2**: the full Modul Ajar. Top-level fields: `schema_version`, `insufficient_context`, `insufficient_reason`, `title`, `initial_competencies[]`, `pancasila_profile[{dimension, how}]`, `facilities[]`, `target_students`, `learning_model{name, rationale}`, `learning_objectives[{text, source_ids[], grounded}]`, `meaningful_understanding[]`, `trigger_questions[]`, `preparation[]`, `meetings[{number, title, activities: Table}]`, `assessment{diagnostic, formative, summative, overview: Table, rubric: Table}`, `enrichment[]`, `remedial[]`, `reflection{teacher[], students[]}`, `attachments{worksheet{title, instructions, tasks[]}, reading_material, glossary[{term, definition}]}`, `identity{subject, grade_level, fase, topic, meetings, minutes_per_meeting, teaching_model}`, `references[{id, document_title, page, page_end, heading}]`, `warnings[]`. A `Table` is `{ caption, columns[], rows[][] }` and every row has exactly one cell per column. The authoritative definition is `sarpebe-backend/app/schemas/lesson_plan_content.py`, mirrored in `sarpebe-frontend/types/lesson-plan.ts`.

### `PUT /api/lesson-plans/{id}`
Body: `{ "generated_content": { ... } }`. The content is validated against the plan's schema version (version 2 against `ModulContent`) and stored. Returns the updated plan. Errors: `invalid_content` (422), `lesson_plan_not_found`.

### `DELETE /api/lesson-plans/{id}` (204)
Deletes the plan. Its cost log rows stay with `lesson_plan_id` set to null.

### `GET /api/lesson-plans/{id}/export/pdf`
Returns `application/pdf` with `Content-Disposition: attachment`; the file name is built from the topic with only ASCII letters, digits, dot, dash and underscore (`safe_filename`). Version 1 plans use the original layout; version 2 plans export every section with real tables (header row repeated across pages). Only completed plans can be exported (`invalid_state` otherwise).

### `GET /api/lesson-plans/{id}/export/docx`
Returns the module as a Word document (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `Content-Disposition: attachment`, same name rules as the PDF). Only plans in the current format (`schema_version` 2) have it; an older plan, or one that is not completed, returns `invalid_state` (409).

### `GET /api/lesson-plans/jobs/{job_id}`
Current job state, read from the plan row:

```json
{ "job_id": "string", "status": "processing", "stage": "drafting",
  "lesson_plan_id": "uuid", "error": null, "error_code": null }
```

`stage` is set only while `status` is `processing`: `retrieving`, `drafting`, or `repairing`. `error` (Indonesian text) and `error_code` (`insufficient_context`, `llm_output_invalid`, `content_blocked`, `llm_unavailable`, `internal_error`, `timeout`) are set when `status` is `failed`. A plan unfinished after 15 minutes is reported as failed with code `timeout`.

### `GET /api/lesson-plans/jobs/{job_id}/stream`
The same object as Server-Sent Events, one `data: {json}` event per second until a terminal status, then the stream ends. Ownership is checked before the stream opens (404 otherwise). Because `EventSource` cannot send headers, clients read it with `fetch` and the bearer token (see `streamJobStatus` in `lib/api/lesson-plans.ts`) and fall back to polling the endpoint above.

## Status values summary

| Resource | Values |
|---|---|
| Lesson plan `status` | `pending`, `processing`, `completed`, `failed` |
| Job `stage` | `retrieving`, `drafting`, `repairing` (only while processing) |
| Curriculum document `status` | `processing`, `completed`, `failed` |
| `role` | `user`, `admin` |
| `document_type` | `CP`, `ATP`, `BUKU_GURU` |
