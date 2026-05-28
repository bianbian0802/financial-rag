"""Tests for the chat API endpoint."""

import unittest
from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.api.v1.chat import get_chat_service
from app.main import app
from app.schemas.chat import ChatRequest, ChatResponse


class FakeChatService:
    """Minimal fake chat service used to test route behavior."""

    def validate_configuration(self) -> None:
        """Pretend the current model configuration is valid."""

    async def generate_reply(self, request: ChatRequest) -> ChatResponse:
        """Return a deterministic non-streaming response for tests."""
        return ChatResponse(
            reply=f"echo:{request.message}",
            model="fake-model",
            provider="fake-provider",
        )

    async def stream_reply(self, _: ChatRequest) -> AsyncIterator[str]:
        """Yield a small deterministic SSE sequence for tests."""
        yield 'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
        yield 'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
        yield "data: [DONE]\n\n"


class ChatApiTests(unittest.TestCase):
    """Verify the chat endpoint supports both JSON and streaming responses."""

    def setUp(self) -> None:
        """Create a fresh test client with dependency overrides."""
        app.dependency_overrides[get_chat_service] = lambda: FakeChatService()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        """Clear dependency overrides after each test case."""
        app.dependency_overrides.clear()

    def test_chat_returns_json_response_by_default(self) -> None:
        """Ensure the chat endpoint keeps the Day6 JSON contract by default."""
        response = self.client.post(
            "/api/v1/chat",
            json={"message": "hi"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "reply": "echo:hi",
                "model": "fake-model",
                "provider": "fake-provider",
            },
        )

    def test_chat_playground_returns_html_page(self) -> None:
        """Ensure the chat playground page is available for manual local testing."""
        response = self.client.get("/api/v1/chat/playground")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Financial RAG Chat Playground", response.text)
        self.assertIn("/api/v1/chat", response.text)

    def test_chat_returns_sse_when_stream_enabled(self) -> None:
        """Ensure the chat endpoint returns SSE frames when stream is enabled."""
        with self.client.stream(
            "POST",
            "/api/v1/chat",
            json={"message": "hi", "stream": True},
        ) as response:
            body = "".join(response.iter_text())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/event-stream; charset=utf-8")
        self.assertIn('data: {"choices":[{"delta":{"content":"hello"}}]}', body)
        self.assertIn('data: {"choices":[{"delta":{"content":" world"}}]}', body)
        self.assertIn("data: [DONE]", body)


if __name__ == "__main__":
    unittest.main()
