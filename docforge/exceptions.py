"""DocForge exceptions and error handling."""


class DocForgeException(Exception):
    """Base exception for all DocForge errors."""

    def __init__(self, message: str, error_code: str = "UNKNOWN"):
        self.message = message
        self.error_code = error_code
        super().__init__(f"[{error_code}] {message}")


class ConfigurationError(DocForgeException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str):
        super().__init__(message, error_code="CONFIG")


class PromptError(DocForgeException):
    """Raised when prompt processing fails."""

    def __init__(self, message: str):
        super().__init__(message, error_code="PROMPT")


class PipelineError(DocForgeException):
    """Raised when pipeline execution fails."""

    def __init__(self, message: str):
        super().__init__(message, error_code="PIPELINE")


class LLMError(DocForgeException):
    """Raised when LLM API call fails."""

    def __init__(self, message: str):
        super().__init__(message, error_code="LLM")


class StorageError(DocForgeException):
    """Raised when storage operation fails."""

    def __init__(self, message: str):
        super().__init__(message, error_code="STORAGE")


class ValidationError(DocForgeException):
    """Raised when validation fails."""

    def __init__(self, message: str):
        super().__init__(message, error_code="VALIDATION")


class MissingContextError(DocForgeException):
    """Raised when required context is missing."""

    def __init__(self, message: str):
        super().__init__(message, error_code="MISSING_CONTEXT")