"""Health check endpoints used to verify the service is running."""

import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthCheckResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthCheckResponse, summary="Health check")
def health_check() -> HealthCheckResponse:
    """Return the current service status for local development checks."""
    settings = get_settings()
    logger.info("Health check requested for service %s.", settings.app_name)
    return HealthCheckResponse(status="ok", service="financial-rag")
