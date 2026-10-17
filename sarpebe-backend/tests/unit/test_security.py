import base64
import json
import time
import uuid
import pytest
from jose import jwt

from app.config import settings
from app.core import security
from app.core.exceptions import InvalidAccessTokenError

def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

def _claims(**overrides):
    claims = {
        "sub": str(uuid.uuid4()),
        "iss": settings.auth_jwt_issuer,
        "type": "access",
        "exp": int(time.time()) + 600,
    }
    claims.update(overrides)
    return claims

def _encode(claims, secret=None, algorithm="HS256"):
    return jwt.encode(claims, secret or settings.auth_jwt_secret, algorithm=algorithm)

def test_access_token_round_trip():
    user_id = uuid.uuid4()
    token, lifetime = security.create_access_token(user_id)
    claims = security.decode_access_token(token)
    assert claims["sub"] == str(user_id)
    assert lifetime == settings.access_token_ttl_minutes * 60

def test_wrong_secret_is_rejected():
    with pytest.raises(InvalidAccessTokenError):
        security.decode_access_token(_encode(_claims(), secret="x" * 40))

def test_expired_token_is_rejected():
    with pytest.raises(InvalidAccessTokenError):
        security.decode_access_token(_encode(_claims(exp=int(time.time()) - 10)))

def test_wrong_issuer_is_rejected():
    with pytest.raises(InvalidAccessTokenError):
        security.decode_access_token(_encode(_claims(iss="someone-else")))

def test_non_access_token_type_is_rejected():
    with pytest.raises(InvalidAccessTokenError):
        security.decode_access_token(_encode(_claims(type="refresh")))

def test_missing_subject_is_rejected():
    claims = _claims()
    del claims["sub"]
    with pytest.raises(InvalidAccessTokenError):
        security.decode_access_token(_encode(claims))

def test_unsigned_alg_none_token_is_rejected():
    token = f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64(_claims())}."
    with pytest.raises(InvalidAccessTokenError):
        security.decode_access_token(token)

def test_token_signed_with_other_algorithm_is_rejected():
    with pytest.raises(InvalidAccessTokenError):
        security.decode_access_token(_encode(_claims(), algorithm="HS512"))

def test_garbage_is_rejected():
    with pytest.raises(InvalidAccessTokenError):
        security.decode_access_token("not-a-jwt")

def test_hash_token_is_deterministic_and_not_the_raw_value():
    raw = security.generate_opaque_token()
    assert security.hash_token(raw) == security.hash_token(raw)
    assert raw not in security.hash_token(raw)
    assert security.generate_opaque_token() != raw

def test_normalize_email():
    assert security.normalize_email("  Guru@Example.COM ") == "guru@example.com"

@pytest.mark.asyncio(loop_scope="session")
async def test_password_hash_and_verify(monkeypatch):
    monkeypatch.setattr(security, "BCRYPT_ROUNDS", 4)
    hashed = await security.hash_password("correct horse")
    assert hashed != "correct horse"
    assert await security.verify_password("correct horse", hashed)
    assert not await security.verify_password("wrong", hashed)

@pytest.mark.asyncio(loop_scope="session")
async def test_verify_password_without_stored_hash_is_false():
    assert not await security.verify_password("anything", None)

@pytest.mark.asyncio(loop_scope="session")
async def test_supabase_style_2a_hash_is_accepted():
    """Accounts imported from Supabase Auth carry $2a$ bcrypt hashes."""
    import bcrypt
    legacy = bcrypt.hashpw(b"legacy-password", bcrypt.gensalt(rounds=4)).decode().replace("$2b$", "$2a$", 1)
    assert legacy.startswith("$2a$")
    assert await security.verify_password("legacy-password", legacy)
    assert not await security.verify_password("nope", legacy)

@pytest.mark.asyncio(loop_scope="session")
async def test_malformed_stored_hash_is_false_not_an_error():
    assert not await security.verify_password("pw", "not-a-bcrypt-hash")
