"""Service layer responsible for calling an OpenAI-compatible chat API."""

import json
import logging
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx

from app.core.config import Settings
from app.core.exceptions import AppException
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class ChatService:
    """Encapsulate chat completion requests to an OpenAI-compatible provider."""

    def __init__(self, settings: Settings) -> None:
        """Store runtime settings required to call the model API."""
        self.settings = settings

    def validate_configuration(self) -> None:
        """Validate the current model configuration before handling a request."""
        self._validate_settings()

    async def generate_reply(self, request: ChatRequest) -> ChatResponse:
        """Send the user message to the configured model and return a normalized reply."""
        self._validate_settings()

        logger.info("Sending chat completion request using model %s.", self.settings.llm_chat_model)

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.llm_timeout_seconds,
                headers=self._build_headers(),
            ) as client:
                response = await client.post(
                    self._build_chat_completion_url(),
                    json=self._build_payload(request, stream=False),
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AppException(
                message="Model request timed out.",
                status_code=504,
                error_code="MODEL_TIMEOUT",
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("Model provider returned error: %s", exc.response.text)
            raise AppException(
                message="Model provider returned an error.",
                status_code=502,
                error_code="MODEL_PROVIDER_ERROR",
                details={"status_code": exc.response.status_code},
            ) from exc
        except httpx.HTTPError as exc:
            raise AppException(
                message="Failed to connect to the model provider.",
                status_code=502,
                error_code="MODEL_CONNECTION_ERROR",
            ) from exc

        response_data = response.json()
        reply = self._extract_reply(response_data)
        logger.info("Chat completion request completed successfully.")
        return ChatResponse(
            reply=reply,
            model=self.settings.llm_chat_model,
            provider="openai-compatible",
        )

    async def stream_reply(self, request: ChatRequest) -> AsyncIterator[str]:
        """Stream OpenAI-compatible SSE chunks from the configured model provider."""
        try:
            self._validate_settings()

            logger.info(
                "Sending streaming chat completion request using model %s.",
                self.settings.llm_chat_model,
            )

            async with httpx.AsyncClient(
                timeout=self.settings.llm_timeout_seconds,
                headers=self._build_headers(),
            ) as client:
                async with client.stream(
                    "POST",
                    self._build_chat_completion_url(),
                    json=self._build_payload(request, stream=True),
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        normalized_line = self._normalize_stream_line(line)
                        if normalized_line is not None:
                            yield normalized_line
        except httpx.TimeoutException as exc:
            yield self._build_stream_error_event(
                AppException(
                    message="Model request timed out.",
                    status_code=504,
                    error_code="MODEL_TIMEOUT",
                )
            )
            logger.warning("Streaming model request timed out: %s", exc)
            return
        except httpx.HTTPStatusError as exc:
            logger.warning("Model provider returned streaming error: %s", exc.response.text)
            yield self._build_stream_error_event(
                AppException(
                    message="Model provider returned an error.",
                    status_code=502,
                    error_code="MODEL_PROVIDER_ERROR",
                    details={"status_code": exc.response.status_code},
                )
            )
            return
        except httpx.HTTPError as exc:
            yield self._build_stream_error_event(
                AppException(
                    message="Failed to connect to the model provider.",
                    status_code=502,
                    error_code="MODEL_CONNECTION_ERROR",
                )
            )
            logger.warning("Failed to connect to model provider for streaming: %s", exc)
            return
        except AppException as exc:
            yield self._build_stream_error_event(exc)
            logger.warning("Streaming request stopped due to app exception: %s", exc.message)
            return

    def _validate_settings(self) -> None:
        """Ensure the minimum model configuration is present before sending requests."""
        if not self.settings.llm_base_url:
            raise AppException(
                message="LLM base URL is missing. Please configure llm_base_url in your environment.",
                status_code=500,
                error_code="LLM_BASE_URL_MISSING",
            )
        if not self.settings.llm_chat_model:
            raise AppException(
                message="LLM chat model is missing. Please configure llm_chat_model in your environment.",
                status_code=500,
                error_code="LLM_CHAT_MODEL_MISSING",
            )
        if not self.settings.llm_api_key and not self._is_local_base_url():
            raise AppException(
                message="LLM API key is missing. Please configure llm_api_key in your environment.",
                status_code=500,
                error_code="LLM_API_KEY_MISSING",
            )

    def _build_payload(self, request: ChatRequest, *, stream: bool) -> dict:
        """Build the OpenAI-compatible chat completion payload."""
        conversation_messages = [
            history_message.model_dump()
            for history_message in request.history
        ]
        return {
            "model": self.settings.llm_chat_model,
            "stream": stream,
            "messages": [
                {
                    "role": "system",
                    "content": request.system_prompt or self.settings.llm_system_prompt,
                },
                *conversation_messages,
                {"role": "user", "content": request.message},
            ],
        }

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for the model provider request."""
        headers = {"Content-Type": "application/json"}
        if self.settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"
        return headers

    def _build_chat_completion_url(self) -> str:
        """Return the full chat completion endpoint URL."""
        return f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"

    def _is_local_base_url(self) -> bool:
        """Check whether the configured provider points to a local development host."""
        hostname = urlparse(self.settings.llm_base_url).hostname
        return hostname in {"127.0.0.1", "localhost"}

    def _normalize_stream_line(self, line: str) -> str | None:
        """Normalize a provider SSE line into a clean downstream SSE frame."""
        if not line:
            return None
        if not line.startswith("data:"):
            return None

        payload = line.removeprefix("data:").strip()
        if payload == "[DONE]":
            return "data: [DONE]\n\n"

        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise AppException(
                message="Model stream response format is invalid.",
                status_code=502,
                error_code="MODEL_STREAM_RESPONSE_INVALID",
            ) from exc

        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    def _build_stream_error_event(self, exc: AppException) -> str:
        """Build a terminal SSE error event for downstream streaming clients."""
        payload = {
            "error": {
                "message": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
            }
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\ndata: [DONE]\n\n"

    @staticmethod
    def _extract_reply(response_data: dict) -> str:
        """Extract the assistant text from an OpenAI-compatible response payload."""
        try:
            return response_data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError, TypeError) as exc:
            raise AppException(
                message="Model response format is invalid.",
                status_code=502,
                error_code="MODEL_RESPONSE_INVALID",
            ) from exc
