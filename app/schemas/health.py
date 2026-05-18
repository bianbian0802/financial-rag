"""Response schemas for health-related endpoints."""

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Response body returned by the health check endpoint."""

    status: str = Field(..., description="Current service status.")
    service: str = Field(..., description="Logical service name.")
