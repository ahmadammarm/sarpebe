import time
import pytest
from fastapi import HTTPException
from jose import jwt, jwk
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from app.config import settings
from app.core import security

def _claims(**overrides):
    claims = {"sub": "user-1", "aud": "authenticated", "exp": int(time.time()) + 3600}
    claims.update(overrides)
    return claims

def _ec_keypair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem

@pytest.fixture(autouse=True)
def reset_jwks_cache():
    security._jwks_cache.update({"keys": [], "fetched_at": 0.0})
    yield
    security._jwks_cache.update({"keys": [], "fetched_at": 0.0})

def test_valid_hs256_token_is_accepted():
    token = jwt.encode(_claims(), settings.supabase_jwt_secret, algorithm="HS256")
    assert security.verify_supabase_token(token)["sub"] == "user-1"

def test_hs256_with_wrong_secret_is_rejected():
    token = jwt.encode(_claims(), "not-the-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        security.verify_supabase_token(token)
    assert exc.value.status_code == 401

def test_expired_token_is_rejected():
    token = jwt.encode(_claims(exp=int(time.time()) - 10), settings.supabase_jwt_secret, algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        security.verify_supabase_token(token)
    assert exc.value.status_code == 401

def test_wrong_audience_is_rejected():
    token = jwt.encode(_claims(aud="anon"), settings.supabase_jwt_secret, algorithm="HS256")
    with pytest.raises(HTTPException):
        security.verify_supabase_token(token)

def test_unsigned_alg_none_token_is_rejected():
    import base64, json
    def b64(data: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()
    token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64(_claims())}."
    with pytest.raises(HTTPException) as exc:
        security.verify_supabase_token(token)
    assert exc.value.status_code == 401

def test_forged_es256_token_is_rejected(mocker):
    """Regression: signatures on ES256/RS256 tokens used to be skipped entirely."""
    _, trusted_public = _ec_keypair()
    attacker_private, _ = _ec_keypair()
    trusted_jwk = jwk.construct(trusted_public, "ES256").to_dict() | {"kid": "k1"}
    mocker.patch.object(security, "_fetch_jwks", return_value=[trusted_jwk])

    forged = jwt.encode(_claims(sub="admin"), attacker_private, algorithm="ES256", headers={"kid": "k1"})
    with pytest.raises(HTTPException) as exc:
        security.verify_supabase_token(forged)
    assert exc.value.status_code == 401

def test_valid_es256_token_is_accepted_via_jwks(mocker):
    private_pem, public_pem = _ec_keypair()
    public_jwk = jwk.construct(public_pem, "ES256").to_dict() | {"kid": "k1"}
    mocker.patch.object(security, "_fetch_jwks", return_value=[public_jwk])

    token = jwt.encode(_claims(), private_pem, algorithm="ES256", headers={"kid": "k1"})
    assert security.verify_supabase_token(token)["sub"] == "user-1"

def test_unknown_kid_is_rejected(mocker):
    private_pem, public_pem = _ec_keypair()
    public_jwk = jwk.construct(public_pem, "ES256").to_dict() | {"kid": "other"}
    mocker.patch.object(security, "_fetch_jwks", return_value=[public_jwk])

    token = jwt.encode(_claims(), private_pem, algorithm="ES256", headers={"kid": "k1"})
    with pytest.raises(HTTPException):
        security.verify_supabase_token(token)
