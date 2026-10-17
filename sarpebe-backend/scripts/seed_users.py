"""
Seeds the default accounts: one admin and one teacher. Safe to run repeatedly; an account that
already exists is left alone unless --reset-passwords is given. Run from sarpebe-backend/:

    python -m scripts.seed_users [--reset-passwords]

Emails and passwords come from the environment or .env:

    SEED_ADMIN_EMAIL   (default admin@example.com)   SEED_ADMIN_PASSWORD
    SEED_USER_EMAIL    (default guru@example.com)    SEED_USER_PASSWORD

A password that is not provided is generated and printed once, only for accounts created in
this run. There are no built-in default passwords. Seeded accounts are email-verified, so they
can sign in immediately.
"""
import argparse
import asyncio
import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import MAX_PASSWORD_BYTES, normalize_email
from app.schemas.auth import MIN_PASSWORD_LENGTH
from scripts.create_user import Action, upsert_user

@dataclass(frozen=True)
class SeedUser:
    env_prefix: str  # SEED_<PREFIX>_EMAIL / SEED_<PREFIX>_PASSWORD
    default_email: str
    full_name: str
    role: str

SEED_USERS = [
    SeedUser("ADMIN", "admin@example.com", "Administrator", "admin"),
    SeedUser("USER", "guru@example.com", "Guru Contoh", "user"),
]

@dataclass(frozen=True)
class SeedResult:
    email: str
    role: str
    action: Action
    generated_password: str | None  # only set when a new account got a generated password

def _validate_password(password: str, source: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH or len(password.encode()) > MAX_PASSWORD_BYTES:
        raise SystemExit(
            f"{source} must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_BYTES} bytes long."
        )
    return password

def resolve_users(environ: dict[str, str]) -> list[tuple[SeedUser, str, str | None]]:
    """Returns (spec, email, password_from_env_or_None) for every seed user."""
    resolved = []
    emails: set[str] = set()
    for spec in SEED_USERS:
        email = normalize_email(environ.get(f"SEED_{spec.env_prefix}_EMAIL") or spec.default_email)
        if email in emails:
            raise SystemExit(f"Seed users must have different emails (duplicate: {email}).")
        emails.add(email)

        password_var = f"SEED_{spec.env_prefix}_PASSWORD"
        password = environ.get(password_var)
        if password:
            _validate_password(password, password_var)
        resolved.append((spec, email, password or None))
    return resolved

async def seed(
    db: AsyncSession,
    users: list[tuple[SeedUser, str, str | None]],
    *,
    reset_passwords: bool = False,
) -> list[SeedResult]:
    """Creates the accounts. The caller commits."""
    results = []
    for spec, email, password in users:
        generated = None
        if password is None:
            generated = secrets.token_urlsafe(12)
        _, action = await upsert_user(
            db,
            email=email,
            password=password or generated,
            role=spec.role,
            name=spec.full_name,
            update_existing=reset_passwords,
        )
        # A generated password is only meaningful if it was actually stored.
        shown = generated if action in ("created", "updated") else None
        results.append(SeedResult(email=email, role=spec.role, action=action, generated_password=shown))
    return results

async def main(reset_passwords: bool) -> None:
    from app.db.session import AsyncSessionLocal

    users = resolve_users(dict(os.environ))
    async with AsyncSessionLocal() as db:
        results = await seed(db, users, reset_passwords=reset_passwords)
        await db.commit()

    for result in results:
        line = f"{result.action:<8} {result.role:<6} {result.email}"
        if result.generated_password:
            line += f"   password: {result.generated_password}"
        print(line)

    if any(r.generated_password for r in results):
        print("\nGenerated passwords are shown only once. Store them now, or set SEED_*_PASSWORD.")
    if any(r.action == "skipped" for r in results):
        print("Existing accounts were left unchanged (use --reset-passwords to overwrite).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--reset-passwords",
        action="store_true",
        help="also reset the password and role of seed accounts that already exist",
    )
    load_dotenv()
    asyncio.run(main(parser.parse_args().reset_passwords))
