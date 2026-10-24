from typing import Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.auth import _validate_new_password

# The tiers an administrator can assign. Only "free" is limited (see quota_service).
SubscriptionTier = Literal["free", "premium"]
UserRole = Literal["user", "admin"]

class ProfileResponse(BaseModel):
    id: UUID
    email: str | None = None
    full_name: str
    school_name: str | None
    subscription_tier: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProfileUpdate(BaseModel):
    """Partial update of the signed-in user's own details."""
    full_name: str | None = Field(default=None, max_length=100)
    school_name: str | None = Field(default=None, max_length=150)

    @field_validator("full_name")
    @classmethod
    def check_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return value

    @field_validator("school_name")
    @classmethod
    def strip_school(cls, value: str | None) -> str | None:
        # An empty school name clears the field.
        return (value.strip() or None) if value is not None else None

    @model_validator(mode="after")
    def require_a_change(self) -> "ProfileUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _validate_new_password(value)

class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)

class AdminUserResponse(ProfileResponse):
    email_verified_at: datetime | None = None
    disabled_at: datetime | None = None

class UserAdminUpdate(BaseModel):
    """Partial update of another account by an administrator."""
    role: UserRole | None = None
    subscription_tier: SubscriptionTier | None = None
    disabled: bool | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> "UserAdminUpdate":
        if self.role is None and self.subscription_tier is None and self.disabled is None:
            raise ValueError("at least one field is required")
        return self

class QuotaResponse(BaseModel):
    # None for `limit` and `remaining` when the user is not limited.
    limit: int | None
    used: int
    remaining: int | None
    unlimited: bool
    # When the oldest counted plan leaves the 24-hour window and a slot frees up; None if none is counted.
    resets_at: datetime | None

class CostSummaryResponse(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_cost: float

class UserCostSummaryResponse(CostSummaryResponse):
    user_id: UUID
