"""Custom exception types used across the application."""

from typing import Any


class AppException(Exception):
    """Application-level exception with a stable response structure."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_code: str = "APP_ERROR",
        details: Any | None = None,
    ) -> None:
        """Initialize a structured application exception."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
