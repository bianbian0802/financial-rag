"""Chat endpoints used to test the first model integration."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, StreamingResponse

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


def get_chat_service(settings: Settings = Depends(get_settings)) -> ChatService:
    """Create a chat service instance for the current request."""
    return ChatService(settings)


def get_chat_playground_path() -> Path:
    """Return the local HTML file path for the chat playground page."""
    return Path(__file__).resolve().parents[2] / "static" / "chat-playground.html"


@router.get(
    "/chat/playground",
    response_class=FileResponse,
    summary="Open the local chat playground page",
)
async def chat_playground() -> FileResponse:
    """Serve a minimal browser page for testing JSON and streaming chat modes."""
    return FileResponse(get_chat_playground_path(), media_type="text/html")


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with the configured model",
)
async def chat(
    request: ChatRequest, service: ChatService = Depends(get_chat_service)
) -> Any:
    """Send a user message to the configured model provider and return JSON or SSE."""
    if request.stream:
        service.validate_configuration()
        return StreamingResponse(
            service.stream_reply(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await service.generate_reply(request)
