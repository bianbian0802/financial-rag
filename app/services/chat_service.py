"""Service layer responsible for calling an OpenAI-compatible chat API."""

import logging

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

    # 检查配置是否齐全
    # 拼出模型请求 payload
    # 发 HTTP 请求给模型服务
    # 处理网络/超时/供应商错误
    # 把模型返回解析成你的统一响应结构
    async def generate_reply(self, request: ChatRequest) -> ChatResponse:
        """Send the user message to the configured model and return a normalized reply."""
        self._validate_settings()

        payload = {
            "model": self.settings.llm_chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": request.system_prompt or self.settings.llm_system_prompt,
                },
                {"role": "user", "content": request.message},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        logger.info("Sending chat completion request using model %s.", self.settings.llm_chat_model)

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
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

    def _validate_settings(self) -> None:
        """Ensure the minimum model configuration is present before sending requests."""
        if not self.settings.llm_api_key:
            raise AppException(
                message="LLM API key is missing. Please configure llm_api_key in your environment.",
                status_code=500,
                error_code="LLM_API_KEY_MISSING",
            )

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
