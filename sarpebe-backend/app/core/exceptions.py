class AppError(Exception):
    """Base class for all domain-level application exceptions."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class QuotaExceededError(AppError):
    """Raised when a user has exceeded their lesson plan generation quota."""
    pass

class DocumentNotFoundError(AppError):
    """Raised when a requested curriculum document cannot be found."""
    pass

class LessonPlanNotFoundError(AppError):
    """Raised when a requested lesson plan cannot be found."""
    pass

class NotOwnerError(AppError):
    """Raised when a user attempts to access a resource they do not own."""
    pass
