"""Tests for the Day12 document embedding API."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.v1.documents import get_document_service
from app.core.config import Settings
from app.main import app
from app.schemas.document import EmbeddingUsage
from app.services.document_service import DocumentService


class DocumentEmbeddingApiTests(unittest.TestCase):
    """Verify chunked documents can be embedded and persisted as vectors."""

    def setUp(self) -> None:
        """Create isolated document storage and a fresh API client for each test."""
        self.temp_directory = tempfile.TemporaryDirectory()
        self.client = TestClient(app)
        self._override_document_service()

    def tearDown(self) -> None:
        """Remove dependency overrides and temporary files after each test."""
        app.dependency_overrides.clear()
        self.temp_directory.cleanup()

    def test_embed_document_succeeds_and_persists_vectors(self) -> None:
        """Ensure a chunked document can be converted into embeddings."""
        source_text = (
            "第一段介绍 embedding 的意义和检索背景。\n\n"
            "第二段解释 chunk 如何进入向量空间。\n\n"
        ) * 20
        upload_response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.md", source_text.encode("utf-8"), "text/markdown")},
        )
        document_id = upload_response.json()["document_id"]
        self.client.post(f"/api/v1/documents/{document_id}/parse")
        self.client.post(f"/api/v1/documents/{document_id}/chunk")

        async def fake_request_embeddings(texts: list[str]) -> tuple[list[list[float]], EmbeddingUsage]:
            """Return deterministic vectors so the route can be tested without a real model."""
            vectors = [
                [float(len(text)), float(index), 1.0]
                for index, text in enumerate(texts)
            ]
            return vectors, EmbeddingUsage(prompt_tokens=len(texts) * 10, total_tokens=len(texts) * 11)

        with patch.object(
            DocumentService,
            "_request_embeddings",
            new=AsyncMock(side_effect=fake_request_embeddings),
        ) as request_embeddings_mock:
            response = self.client.post(f"/api/v1/documents/{document_id}/embed")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["document_id"], document_id)
        self.assertEqual(payload["status"], "embedded")
        self.assertGreater(payload["chunk_count"], 1)
        self.assertEqual(payload["chunk_count"], len(payload["embedded_chunks"]))
        self.assertEqual(payload["embedding_dimensions"], 3)
        self.assertEqual(payload["usage"]["prompt_tokens"], payload["chunk_count"] * 10)
        self.assertTrue(request_embeddings_mock.await_count >= 1)

        embeddings_output_path = Path(payload["embeddings_output_path"])
        self.assertTrue(embeddings_output_path.exists())
        stored_payload = json.loads(embeddings_output_path.read_text(encoding="utf-8"))
        self.assertEqual(stored_payload["embedding_model"], "qwen2.5:3b")
        self.assertEqual(stored_payload["embedded_chunks"][0]["embedding_dimensions"], 3)

    def test_embed_document_requires_chunk_output(self) -> None:
        """Ensure embedding an unknown document ID returns a stable not-found response."""
        response = self.client.post("/api/v1/documents/not-real/embed")

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["error_code"], "DOCUMENT_CHUNKED_NOT_FOUND")

    def test_embed_document_rejects_invalid_batch_size(self) -> None:
        """Ensure invalid batch size settings are surfaced before provider calls."""
        self._override_document_service(embedding_batch_size=0)
        upload_response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": ("guide.md", b"# embedding config", "text/markdown")},
        )
        document_id = upload_response.json()["document_id"]
        self.client.post(f"/api/v1/documents/{document_id}/parse")
        self.client.post(f"/api/v1/documents/{document_id}/chunk")

        response = self.client.post(f"/api/v1/documents/{document_id}/embed")

        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertEqual(payload["error_code"], "EMBEDDING_BATCH_SIZE_INVALID")

    def _override_document_service(self, *, embedding_batch_size: int = 2) -> None:
        """Override the document service dependency with isolated embedding settings."""
        settings = Settings(
            documents_storage_dir=self.temp_directory.name,
            documents_max_upload_size_mb=25,
            documents_chunk_size_bytes=1024 * 1024,
            document_chunk_size=120,
            document_chunk_overlap=20,
            document_chunk_preview_limit=80,
            embedding_base_url="http://127.0.0.1:11434/v1",
            embedding_api_key="ollama",
            embedding_model="qwen2.5:3b",
            embedding_batch_size=embedding_batch_size,
            embedding_timeout_seconds=60,
            llm_base_url="http://127.0.0.1:11434/v1",
            llm_api_key="ollama",
            llm_chat_model="qwen2.5:3b",
        )
        app.dependency_overrides[get_document_service] = lambda: DocumentService(settings)


if __name__ == "__main__":
    unittest.main()
