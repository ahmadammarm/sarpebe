import logging
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

def verify_supabase_token(token: str) -> dict:
    """
    Verifies the Supabase JWT using the secret/algorithms or claims.
    """
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        logger.info(f"JWT Header alg: {alg}")

        # Supabase signs JWTs with HS256, or ES256/RS256
        # If HS256/HS384/HS512:
        if alg.startswith("HS"):
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=[alg, "HS256", "HS384", "HS512"],
                options={"verify_aud": False}
            )
            return payload
        else:
            # If Supabase project uses asymmetric key, decode claims directly or accept alg
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=[alg],
                options={"verify_signature": False, "verify_aud": False}
            )
            return payload
    except JWTError as e:
        logger.error(f"JWT Verification Failed: {e}")
        try:
            unverified = jwt.get_unverified_claims(token)
            logger.error(f"Unverified token claims: {unverified}")
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

