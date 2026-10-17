import logging
import time
import threading

import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)

SYMMETRIC_ALGORITHMS = {"HS256"}
ASYMMETRIC_ALGORITHMS = {"ES256", "RS256"}
EXPECTED_AUDIENCE = "authenticated"
JWKS_TTL_SECONDS = 600

_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}
_jwks_lock = threading.Lock()


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _fetch_jwks() -> list[dict]:
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json().get("keys", [])


def _get_signing_key(kid: str | None, force_refresh: bool = False) -> dict | None:
    with _jwks_lock:
        expired = time.monotonic() - _jwks_cache["fetched_at"] > JWKS_TTL_SECONDS
        if force_refresh or expired or not _jwks_cache["keys"]:
            _jwks_cache["keys"] = _fetch_jwks()
            _jwks_cache["fetched_at"] = time.monotonic()
        keys = _jwks_cache["keys"]

    for key in keys:
        if kid is None or key.get("kid") == kid:
            return key
    return None


def verify_supabase_token(token: str) -> dict:
    """
    Verifies a Supabase JWT: signature, expiry and audience.
    HS256 tokens use the project JWT secret; ES256/RS256 tokens use the project JWKS.
    Any other algorithm (including "none") is rejected.
    """
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")

        if alg in SYMMETRIC_ALGORITHMS:
            key = settings.supabase_jwt_secret
        elif alg in ASYMMETRIC_ALGORITHMS:
            kid = header.get("kid")
            key = _get_signing_key(kid)
            if key is None:
                key = _get_signing_key(kid, force_refresh=True)
            if key is None:
                raise JWTError("Unknown signing key")
        else:
            raise JWTError("Unsupported signing algorithm")

        return jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience=EXPECTED_AUDIENCE,
        )
    except (JWTError, httpx.HTTPError) as e:
        logger.warning("JWT verification failed: %s", e)
        raise _unauthorized()
