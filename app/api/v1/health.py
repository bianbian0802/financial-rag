"""Health check endpoints used to verify the service is running."""

from fastapi import APIRouter

from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, summary="Health check")
def health_check() -> HealthCheckResponse:
    """Return the current service status for local development checks."""
    return HealthCheckResponse(status="ok", service="financial-rag")
