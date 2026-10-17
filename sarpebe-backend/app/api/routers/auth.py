from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.services import email_service
from app.core.services.auth_service import auth_service
from app.schemas.auth import (
    EmailRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# These endpoints answer identically whether or not the email exists, so they cannot be used
# to find out who is registered.
REGISTER_MESSAGE = "If the email can be registered, a verification link has been sent."
VERIFICATION_RESENT_MESSAGE = "If the account exists and is unverified, a new verification link has been sent."
RESET_SENT_MESSAGE = "If the account exists, a password reset link has been sent."


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.register(db, payload.email, payload.password, payload.full_name)
    if result:
        user, token = result
        if token:
            background_tasks.add_task(email_service.send_verification_email, user.email, user.full_name, token)
    return MessageResponse(message=REGISTER_MESSAGE)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh(db, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.logout(db, payload.refresh_token)
    return None


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.verify_email(db, payload.token)
    return MessageResponse(message="Email verified.")


@router.post("/resend-verification", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    payload: EmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.resend_verification(db, payload.email)
    if result:
        user, token = result
        background_tasks.add_task(email_service.send_verification_email, user.email, user.full_name, token)
    return MessageResponse(message=VERIFICATION_RESENT_MESSAGE)


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: EmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.forgot_password(db, payload.email)
    if result:
        user, token = result
        background_tasks.add_task(email_service.send_password_reset_email, user.email, user.full_name, token)
    return MessageResponse(message=RESET_SENT_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(db, payload.token, payload.password)
    return MessageResponse(message="Password updated. Please sign in with your new password.")
