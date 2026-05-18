"""FastAPI application entrypoint for the Financial RAG project."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_application()
