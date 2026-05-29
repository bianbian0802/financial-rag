"""Central router for all v1 API endpoints."""

from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(health_router, tags=["health"])
