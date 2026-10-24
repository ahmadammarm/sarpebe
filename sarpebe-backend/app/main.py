from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.config import settings
from app.core.exceptions import (
    AccountDisabledError,
    AppError,
    DocumentNotFoundError,
    EmailNotVerifiedError,
    ForbiddenError,
    InvalidAccessTokenError,
    InvalidContentError,
    InvalidCredentialsError,
    InvalidEmailTokenError,
    InvalidPasswordError,
    InvalidRefreshTokenError,
    InvalidStateError,
    InvalidUploadError,
    LastAdminError,
    LessonPlanNotFoundError,
    NotOwnerError,
    QuotaExceededError,
    SelfActionError,
    TooManyAttemptsError,
    UserNotFoundError,
)
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    yield
    # Shutdown actions
    await engine.dispose()

app = FastAPI(
    title="SARPEBE Backend",
    description="Backend API for SARPEBE Lesson Plan Generator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ERROR_STATUS_CODES: dict[type[AppError], int] = {
    DocumentNotFoundError: 404,
    LessonPlanNotFoundError: 404,
    NotOwnerError: 403,
    ForbiddenError: 403,
    InvalidStateError: 409,
    InvalidUploadError: 400,
    InvalidEmailTokenError: 400,
    InvalidContentError: 422,
    InvalidCredentialsError: 401,
    InvalidAccessTokenError: 401,
    InvalidRefreshTokenError: 401,
    EmailNotVerifiedError: 403,
    TooManyAttemptsError: 429,
    QuotaExceededError: 429,
    InvalidPasswordError: 400,  # not 401: the client would take that for an expired session
    AccountDisabledError: 403,
    UserNotFoundError: 404,
    LastAdminError: 409,
    SelfActionError: 409,
}


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = ERROR_STATUS_CODES.get(type(exc), 400)
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "code": exc.code},
        headers=headers,
    )


# Register all API routes
app.include_router(api_router)
