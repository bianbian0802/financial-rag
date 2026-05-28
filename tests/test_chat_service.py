"""Tests for chat service payload composition."""

import unittest

from app.core.config import Settings
from app.schemas.chat import ChatHistoryMessage, ChatRequest
from app.services.chat_service import ChatService


class ChatServiceTests(unittest.TestCase):
    """Verify service helpers build the expected upstream payload."""

    def test_build_payload_includes_history_before_latest_user_message(self) -> None:
        """Ensure historical messages are forwarded in order for multi-turn chat."""
        service = ChatService(
            Settings(
                llm_base_url="http://127.0.0.1:11434/v1",
                llm_api_key="ollama",
                llm_chat_model="qwen2.5:3b",
                llm_system_prompt="system prompt",
            )
        )
        request = ChatRequest(
            message="最新问题",
            history=[
                ChatHistoryMessage(role="user", content="第一轮用户问题"),
                ChatHistoryMessage(role="assistant", content="第一轮助手回答"),
            ],
        )

        payload = service._build_payload(request, stream=True)

        self.assertEqual(payload["model"], "qwen2.5:3b")
        self.assertTrue(payload["stream"])
        self.assertEqual(
            payload["messages"],
            [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "第一轮用户问题"},
                {"role": "assistant", "content": "第一轮助手回答"},
                {"role": "user", "content": "最新问题"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
