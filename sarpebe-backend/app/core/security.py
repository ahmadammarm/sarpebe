from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.config import settings

def verify_supabase_token(token: str) -> dict:
    """
    Verifies the Supabase JWT using the HS256 secret.
    Raises a 401 HTTPException if invalid.
    """
    try:
        # Supabase signs JWTs with HS256 and the JWT_SECRET
        payload = jwt.decode(
            token, 
            settings.supabase_jwt_secret, 
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
