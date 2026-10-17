# Authentication and security

Authentication is implemented by the backend (`app/api/routers/auth.py`, `app/core/services/auth_service.py`, `app/core/security.py`). Supabase is only the database host and file storage. The frontend never talks to Supabase.

## Accounts and roles

- A `profiles` row is an account. `email` is stored lower-case; `password_hash` is a bcrypt hash; `email_verified_at` is set once the address is proven.
- Roles: `user` (teacher, default) and `admin`. Admin-only routes use the `require_admin` dependency in `app/api/deps.py`: document upload, list, delete, and the all-users cost report. The frontend also redirects non-admins away from `/curriculum` (`proxy.ts`), but that is convenience only; the backend is the enforcement point.
- Accounts imported from the former Supabase Auth keep their ids and bcrypt hashes (migration `b7e2f4a91c35`). An account with a null `password_hash` has no password until it uses password reset.
- Create accounts with `python -m scripts.seed_users`, `scripts.create_user`, or by registering. Change a role with `scripts.upgrade_user`.

## Passwords

- bcrypt, hashed in a worker thread so the event loop is not blocked.
- New passwords (register, reset) must be at least 8 characters and at most 72 bytes (bcrypt's limit). Login deliberately applies no strength rules, because imported accounts may have older, shorter passwords.
- Registering hashes the password before checking whether the email exists, so the "already registered" path takes the same time as a new account. Login does the same dummy verification for unknown emails.
- Hashes and tokens are never logged or returned.

## Tokens

| Token | Format | Lifetime | Stored |
|---|---|---|---|
| Access token | JWT, HS256, claims `sub`, `iss`, `type`, `iat`, `exp`, `jti` | 15 minutes (`ACCESS_TOKEN_TTL_MINUTES`) | Not stored; verified by signature. |
| Refresh token | Random opaque string | 14 days (`REFRESH_TOKEN_TTL_DAYS`) | Only its SHA-256 in `refresh_tokens`. |
| Email verification token | Random opaque string | 24 hours | SHA-256 in `auth_tokens`, purpose `verify_email`. |
| Password reset token | Random opaque string | 60 minutes | SHA-256 in `auth_tokens`, purpose `reset_password`. |

Access token verification (`decode_access_token`) checks signature, expiry, issuer and `type`; `get_current_user` then loads the profile, so a deleted account is rejected even with a valid token.

### Refresh token rotation

Every refresh exchanges the token for a new pair and marks the old one `revoked` and `rotated`. All tokens of one login share a `family_id`.

```
refresh(token)
  unknown                          -> 401 invalid_refresh_token
  revoked and rotated < 30 s ago   -> accepted (two tabs refreshing at once)
  revoked otherwise                -> revoke the whole family, 401 (the token leaked)
  expired                          -> 401
  valid                            -> mark rotated, issue a new pair in the same family
```

The row is read with `SELECT ... FOR UPDATE`, so concurrent refreshes serialize. Logout revokes the whole family. A password reset revokes every refresh token of the user.

## Email flows and anti-enumeration

`register`, `resend-verification` and `forgot-password` return the same message and status whether or not the email exists, so they cannot be used to discover who has an account. Resend and forgot-password allow 3 emails per hour per address and purpose (Redis counters); over the limit the response is unchanged and no email is sent. Only a correct password reveals whether an account is unverified (`email_not_verified`).

Issuing a new token of a purpose invalidates earlier unused ones. Following a reset link also marks the email as verified.

## Brute-force protection

Failed logins are counted in Redis per email: after `LOGIN_MAX_FAILED_ATTEMPTS` (5) the account answers `429 too_many_attempts` for `LOGIN_LOCKOUT_MINUTES` (15). A successful login or a password reset clears the counter. If Redis is unreachable the counters fail open: sign-in keeps working without rate limiting rather than locking everyone out. Treat Redis availability as part of the security posture in production.

## The frontend session

NextAuth (JWT strategy, credentials provider) calls `/api/auth/login`. The access and refresh tokens live inside the NextAuth session cookie, which is signed with `NEXTAUTH_SECRET`; they are never put in `localStorage`, and the refresh token is not exposed to browser code. `lib/authOptions.ts` renews the access token through `/api/auth/refresh` shortly before it expires and revokes the refresh token on sign out. If renewal is refused, the session gets an `error` flag and `SessionGuard` (`app/providers.tsx`) signs the user out. `lib/api/client.ts` attaches `Authorization: Bearer <accessToken>` to every request. `proxy.ts` (Next.js middleware) requires a session for `/lesson-plans` and `/curriculum`.

## Authorization and data isolation

- The API connects with a privileged database role, so database row-level security is not the barrier. Ownership is checked in the application: plan queries are scoped by `user_id` in `lesson_plan_repository.py` (`get_by_id_and_user`, `get_by_job_id_and_user`), and a plan or job that belongs to someone else is a 404, not a 403, so ids cannot be probed.
- A client-supplied `user_id` is never trusted for writes; it always comes from the verified token.
- Primary keys are UUIDs, so ids are not enumerable.
- Never expose the database to browsers directly (for example through Supabase's public API) without re-enabling row-level security policies.

## Upload safety

`POST /api/curriculum/upload` (admin only) requires a `.pdf` name, the `%PDF-` magic bytes (the `Content-Type` header is not trusted), and a size within `MAX_UPLOAD_MB`. The file is stored under a server-generated name (`curriculum_storage_path(doc_id)`), never the client's filename. PDFs are parsed with pdfplumber and pypdf in a worker; a parse failure marks the document failed with a message.

## Prompt injection

Text from teachers (topic, class notes) and from documents (passages) reaches the model. Defences, all in `app/core/prompts/`:

- Rules appear only in `system_instruction`; user content is sent as XML-tagged data, and both teacher text and passage text are escaped (`escape_data`, `attribute`) so they cannot close a tag or open a new one.
- The system instruction tells the model to treat tagged content as data and to ignore instructions inside it.
- The output must match a JSON schema, and the server validates it. Citations are rebuilt by the server from passage ids, so injected text cannot add a source.
- Classroom notes are limited to 500 characters.

This reduces risk; it does not make a model immune. Teachers are told the plan is a draft to review.

## Secrets and configuration

- `.env` and `.env.local` are never committed. Required secrets: `AUTH_JWT_SECRET`, `NEXTAUTH_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`, `REDIS_URL`.
- Settings are read only through `app/config.py`.
- Rotating `AUTH_JWT_SECRET` invalidates all access tokens; rotating `NEXTAUTH_SECRET` signs everyone out of the web app.
- CORS allows only `CORS_ORIGINS`.

## Known limits

- Access tokens cannot be revoked before they expire (15 minutes); logout and reset revoke refresh tokens only.
- The Storage bucket is public, so a curriculum PDF is readable by anyone who has its URL. Curriculum documents are official public standards, so this is accepted; do not upload confidential files.
- Rate limiting covers login and email actions only, not the rest of the API.
- Email verification relies on `EMAIL_BACKEND=smtp` being configured in production.
