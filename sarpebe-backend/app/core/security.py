import asyncio
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

import bcrypt
from jose import jwt, JWTError

from app.config import settings
from app.core.exceptions import InvalidAccessTokenError
from app.utils.time import utc_now

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
BCRYPT_ROUNDS = 12
MAX_PASSWORD_BYTES = 72  # bcrypt ignores (or rejects) anything longer

# Verified against when a login names an unknown email, so response time does not reveal
# which emails are registered.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password-for-timing", bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def normalize_email(email: str) -> str:
    return email.strip().lower()


# --- Passwords -------------------------------------------------------------------------
# Hashes are plain bcrypt so accounts imported from Supabase Auth ($2a$ hashes) keep working.

def _hash_password_sync(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password_sync(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        # Malformed stored hash, or a password longer than bcrypt accepts.
        return False


async def hash_password(password: str) -> str:
    """bcrypt is CPU-bound (~250 ms at cost 12), so keep it off the event loop."""
    return await asyncio.to_thread(_hash_password_sync, password)


async def verify_password(password: str, password_hash: str | None) -> bool:
    """Always performs a bcrypt comparison, even when there is no stored hash."""
    if not password_hash:
        await asyncio.to_thread(_verify_password_sync, password, _DUMMY_HASH)
        return False
    return await asyncio.to_thread(_verify_password_sync, password, password_hash)


# --- Opaque tokens (refresh, email verification, password reset) ------------------------

def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(raw_token: str) -> str:
    """Only this digest is stored; the raw token exists in the user's hands and the email."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# --- Access tokens ----------------------------------------------------------------------

def create_access_token(user_id: uuid.UUID, now: datetime | None = None) -> tuple[str, int]:
    """Returns (jwt, lifetime in seconds)."""
    issued_at = now or utc_now()
    lifetime = timedelta(minutes=settings.access_token_ttl_minutes)
    claims = {
        "sub": str(user_id),
        "iss": settings.auth_jwt_issuer,
        "type": ACCESS_TOKEN_TYPE,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + lifetime).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(claims, settings.auth_jwt_secret, algorithm=JWT_ALGORITHM), int(lifetime.total_seconds())


def decode_access_token(token: str) -> dict:
    """Verifies signature, expiry, issuer and token type. Raises InvalidAccessTokenError."""
    try:
        claims = jwt.decode(
            token,
            settings.auth_jwt_secret,
            algorithms=[JWT_ALGORITHM],
            issuer=settings.auth_jwt_issuer,
            options={"verify_aud": False},
        )
    except JWTError:
        raise InvalidAccessTokenError("Could not validate credentials")

    if claims.get("type") != ACCESS_TOKEN_TYPE or not claims.get("sub"):
        raise InvalidAccessTokenError("Could not validate credentials")
    return claims
