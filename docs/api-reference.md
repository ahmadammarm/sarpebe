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
| `invalid_email_token` | 400 | Verification or reset link invalid, used, or expired. |
| `not_owner` | 403 | Resource belongs to another user. |
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

### `GET /api/users/me/costs`
Aggregated model usage of the current user: `{ "prompt_tokens": int, "completion_tokens": int, "total_cost": number }`.

### `GET /api/users/costs` (admin)
A list of `{ user_id, prompt_tokens, completion_tokens, total_cost }`, one per user.

## Curriculum documents (admin)

### `POST /api/curriculum/upload` (202)
`multipart/form-data`: `file` (PDF), `grade_level` (text), `subject` (text), `document_type` (`CP`, `ATP`, or `BUKU_GURU`, default `CP`). The labels are normalized (trimmed, case-folded) and must match what teachers type. The file is validated (extension, `%PDF-` header, size), stored, and ingested in the background. Response: the document with `status: "processing"`.

```json
{ "id": "uuid", "title": "CP IPS.pdf", "document_type": "CP", "url_path": "https://...",
  "grade_level": "9", "subject": "ips", "status": "processing", "uploaded_at": "..." }
```

`status` becomes `completed` or `failed`. Poll `GET /api/curriculum` for it.

### `GET /api/curriculum`
List of all documents (same shape).

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

Response: `{ "job_id": "string", "id": "uuid" }`. The plan row exists immediately with `status: "pending"`.

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

`status` is `pending`, `processing`, `completed`, or `failed`. For a failed plan `generated_content` is `{ "error": "<message>" }`.

`generated_content` depends on `schema_version`:

- **1** (older plans): `title`, `objectives[]`, `materials[]`, `activities[{duration, description}]`, `assessment`, `citations[]`.
- **2**: the full Modul Ajar. Top-level fields: `schema_version`, `insufficient_context`, `insufficient_reason`, `title`, `initial_competencies[]`, `pancasila_profile[{dimension, how}]`, `facilities[]`, `target_students`, `learning_model{name, rationale}`, `learning_objectives[{text, source_ids[], grounded}]`, `meaningful_understanding[]`, `trigger_questions[]`, `preparation[]`, `meetings[{number, title, activities: Table}]`, `assessment{diagnostic, formative, summative, overview: Table, rubric: Table}`, `enrichment[]`, `remedial[]`, `reflection{teacher[], students[]}`, `attachments{worksheet{title, instructions, tasks[]}, reading_material, glossary[{term, definition}]}`, `identity{subject, grade_level, fase, topic, meetings, minutes_per_meeting, teaching_model}`, `references[{id, document_title, page, page_end, heading}]`, `warnings[]`. A `Table` is `{ caption, columns[], rows[][] }` and every row has exactly one cell per column. The authoritative definition is `sarpebe-backend/app/schemas/lesson_plan_content.py`, mirrored in `sarpebe-frontend/types/lesson-plan.ts`.

### `PUT /api/lesson-plans/{id}`
Body: `{ "generated_content": { ... } }`. The content is validated against the plan's schema version (version 2 against `ModulContent`) and stored. Returns the updated plan. Errors: `invalid_content` (422), `lesson_plan_not_found`.

### `DELETE /api/lesson-plans/{id}` (204)
Deletes the plan. Its cost log rows stay with `lesson_plan_id` set to null.

### `GET /api/lesson-plans/{id}/export/pdf`
Returns `application/pdf` with `Content-Disposition: attachment`. Version 1 plans use the original layout; version 2 plans export every section with real tables (header row repeated across pages). Only completed plans can be exported (`invalid_state` otherwise).

### `GET /api/lesson-plans/jobs/{job_id}`
Current job state, read from the plan row:

```json
{ "job_id": "string", "status": "processing", "stage": "drafting",
  "lesson_plan_id": "uuid", "error": null }
```

`stage` is set only while `status` is `processing`: `retrieving`, `drafting`, or `repairing`. `error` is set when `status` is `failed`. A plan unfinished after 15 minutes is reported as failed with a timeout message.

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
