"""Exception handlers that convert errors into consistent API responses."""

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


def _build_error_response(
    *,
    message: str,
    error_code: str,
    details: object | None,
    status_code: int,
) -> JSONResponse:
    """Build a JSON error response with the shared error schema."""
    payload = ErrorResponse(
        message=message,
        error_code=error_code,
        details=details,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    """Handle known application exceptions in a predictable format."""
    logger.warning("App exception raised: %s", exc.message)
    return _build_error_response(
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        status_code=exc.status_code,
    )


async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI validation errors with a business-friendly structure."""
    logger.warning("Validation error raised: %s", exc.errors())
    return _build_error_response(
        message="Request validation failed.",
        error_code="VALIDATION_ERROR",
        details=exc.errors(),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions without leaking internal details."""
    logger.exception("Unexpected server error: %s", exc)
    return _build_error_response(
        message="Internal server error.",
        error_code="INTERNAL_SERVER_ERROR",
        details=None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
