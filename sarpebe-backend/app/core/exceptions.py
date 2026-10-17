class AppError(Exception):
    """Base class for all domain-level application exceptions."""
    # Stable machine-readable identifier returned to clients alongside the message.
    code: str = "error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class DocumentNotFoundError(AppError):
    """Raised when a requested curriculum document cannot be found."""
    code = "document_not_found"

class LessonPlanNotFoundError(AppError):
    """Raised when a requested lesson plan cannot be found."""
    code = "lesson_plan_not_found"

class NotOwnerError(AppError):
    """Raised when a user attempts to access a resource they do not own."""
    code = "not_owner"

class InvalidStateError(AppError):
    """Raised when an operation is not allowed in the resource's current state."""
    code = "invalid_state"

class InvalidUploadError(AppError):
    """Raised when an uploaded file fails validation."""
    code = "invalid_upload"

class InvalidCredentialsError(AppError):
    """Raised when an email/password pair does not match an account."""
    code = "invalid_credentials"

class EmailNotVerifiedError(AppError):
    """Raised when logging in to an account whose email has not been verified."""
    code = "email_not_verified"

class TooManyAttemptsError(AppError):
    """Raised when an account or action is temporarily rate limited."""
    code = "too_many_attempts"

class InvalidAccessTokenError(AppError):
    """Raised when an access token is missing, malformed, expired or forged."""
    code = "invalid_token"

class InvalidRefreshTokenError(AppError):
    """Raised when a refresh token is unknown, expired, revoked or replayed."""
    code = "invalid_refresh_token"

class InvalidEmailTokenError(AppError):
    """Raised when an email verification or password reset token is unusable."""
    code = "invalid_email_token"
