"""Shared error response schemas used by exception handlers."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response body for API failures."""

    message: str = Field(..., description="Human-readable error message.")
    error_code: str = Field(..., description="Stable application error code.")
    details: Any | None = Field(
        default=None,
        description="Optional structured details for debugging or validation feedback.",
    )
