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

class TransientLLMError(AppError):
    """Raised when the model API stays unavailable (429, 5xx, timeout) after the allowed attempts."""
    code = "llm_unavailable"

class LLMOutputError(AppError):
    """Raised when the model's output is unusable even after one repair attempt."""
    code = "llm_output_invalid"

class ContentBlockedError(AppError):
    """Raised when the model refuses or the response is blocked (safety, recitation)."""
    code = "content_blocked"

class InsufficientContextError(AppError):
    """Raised when the indexed documents do not cover the requested topic well enough."""
    code = "insufficient_context"

class InvalidContentError(AppError):
    """Raised when edited lesson plan content does not match its schema."""
    code = "invalid_content"

class InvalidPasswordError(AppError):
    """Raised when the current password given for a sensitive action is wrong."""
    code = "invalid_password"

class AccountDisabledError(AppError):
    """Raised when an administrator has disabled the account that tries to sign in or act."""
    code = "account_disabled"

class UserNotFoundError(AppError):
    """Raised when an administrator names a user that does not exist."""
    code = "user_not_found"

class LastAdminError(AppError):
    """Raised when an action would leave the system without an active administrator."""
    code = "last_admin"

class SelfActionError(AppError):
    """Raised when an administrator tries to change their own role or status, or delete themselves."""
    code = "self_action_forbidden"

class QuotaExceededError(AppError):
    """Raised when a user has used up the lesson plans they may start in the current window."""
    code = "quota_exceeded"

class ForbiddenError(AppError):
    """Raised when an authenticated user lacks the role an endpoint requires."""
    code = "forbidden"
