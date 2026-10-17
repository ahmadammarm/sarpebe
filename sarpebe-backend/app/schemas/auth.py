from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import MAX_PASSWORD_BYTES

MIN_PASSWORD_LENGTH = 8


def _validate_new_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes.")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(min_length=2, max_length=100)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _validate_new_password(value)

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    # No strength rules here: imported accounts may have shorter legacy passwords.
    password: str = Field(min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=512)


class LogoutRequest(RefreshRequest):
    pass


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class EmailRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _validate_new_password(value)


class MessageResponse(BaseModel):
    message: str


class AuthUser(BaseModel):
    id: UUID
    email: str | None
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token lifetime in seconds
    user: AuthUser
