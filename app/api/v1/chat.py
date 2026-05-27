"""Chat endpoints used to test the first model integration."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


def get_chat_service(settings: Settings = Depends(get_settings)) -> ChatService:
    """Create a chat service instance for the current request."""
    return ChatService(settings)


@router.post("/chat", response_model=ChatResponse, summary="Chat with the configured model")
async def chat(
    request: ChatRequest, service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """Send a user message to the configured model provider and return the reply."""
    return await service.generate_reply(request)
