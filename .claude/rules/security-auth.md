# Security and authentication rules

Applies to anything touching accounts, tokens, sessions, uploads, secrets, or user data. Background: `docs/authentication-security.md`.

## Ownership of auth

The backend owns authentication (`app/api/routers/auth.py`, `app/core/services/auth_service.py`, `app/core/security.py`). Supabase is only the Postgres host and Storage. Do not reintroduce Supabase Auth.

## Passwords

- bcrypt through `hash_password` and `verify_password` (run in a thread). New passwords are 8 characters minimum and 72 bytes maximum. Login applies no strength rules (imported accounts).
- Always perform a bcrypt comparison, even for unknown emails, and hash on register before checking for an existing email, so timing does not reveal accounts.
- Never log, return, or store a plain password; never return `password_hash`.

## Tokens

- Access token: JWT HS256 from `create_access_token`, claims `sub`, `iss`, `type`, `iat`, `exp`, `jti`, 15 minutes. Verify with `decode_access_token` (signature, expiry, issuer, type); `get_current_user` then loads the profile, so deleted accounts are rejected.
- Refresh, verification and reset tokens are random opaque strings (`generate_opaque_token`); store only their SHA-256 (`hash_token`).
- Refresh tokens are single use and rotate; read with `SELECT ... FOR UPDATE`. Replay after the grace window revokes the whole family. Logout and password reset revoke sessions.
- Issuing a new email token invalidates earlier unused ones of the same purpose.

## Account status and sensitive actions

- `profiles.disabled_at` blocks an account. Check it in `get_current_user`, in `login` (only after the password is verified, like the email-verified check), and in `refresh` (revoke the login session and refuse). Disabling revokes all refresh tokens.
- Changing the password and deleting the account require the current password through `UserService._check_password`, which counts wrong guesses in Redis and locks the action like failed logins. A wrong password is `400 invalid_password`; never answer it with 401, because the client treats 401 as an expired session. A password change cancels unused reset links and revokes every refresh token.
- Role, status and deletion by an administrator go through `user_service`: nobody changes their own role or status, and the last active administrator is never demoted, disabled or deleted (lock the admin rows with `lock_active_admin_ids`; `FOR UPDATE` cannot be combined with a count).

## Anti-enumeration

`register`, `resend-verification` and `forgot-password` must answer identically whether or not the email exists, with the same status and message. Reveal "email not verified" only after a correct password. Do not add endpoints or error messages that disclose whether an email is registered.

## Rate limiting

Redis counters in `app/core/rate_limit.py` for login failures (5, then 15 minutes) and email actions (3 per hour). They fail open when Redis is down, with a logged warning; keep that behaviour so an outage does not lock everyone out.

## Authorization

- Private endpoints use `Depends(get_current_user)`; admin endpoints use `require_admin`.
- Ownership is enforced in repositories (`get_by_id_and_user`, `get_by_job_id_and_user`). Another user's plan or job is a 404, not a 403.
- Never trust a client-provided `user_id`; derive it from the token. UUIDs for all keys.
- The API uses a privileged DB role, so database row-level security does not protect data; do not expose the database to clients directly.

## Uploads

Validate on the server: `.pdf` name, `%PDF-` magic bytes, size within `MAX_UPLOAD_MB`; do not trust `Content-Type`. Store under a server-generated path, never the client filename. Only admins upload.

## Prompt injection

Teacher input and document text are untrusted. Keep rules in `system_instruction`, escape and tag all data, validate output against a schema, and build citations on the server. See `ai-pipeline.md` in this folder.

## Secrets

- Never commit `.env`, `.env.local`, keys, or tokens. Never print secrets in logs or answers.
- Do not edit the user's `.env` files unless they ask. Add new variables to `.env.example` instead, and tell the user what to set.
- Settings come only from `app/config.py`.
- The frontend keeps tokens in the signed NextAuth cookie, never in `localStorage`; the refresh token is not exposed to browser code.

## Errors

Return stable `code` values and generic messages; no stack traces or SQL in responses. Do not swallow exceptions silently: log with context or re-raise.

## Review checklist for auth-related changes

- Does any new response differ between existing and non-existing accounts?
- Can a user read or change another user's data through a new query?
- Is a new secret or token stored hashed, expiring, and single use where applicable?
- Is there a test for the failure path?
