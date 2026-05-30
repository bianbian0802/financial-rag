"""Tests for the Day11 document chunking API."""

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.v1.documents import get_document_service
from app.core.config import Settings
from app.main import app
from app.services.document_service import DocumentService


class DocumentChunkingApiTests(unittest.TestCase):
    """Verify parsed documents can be segmented into retrieval-friendly chunks."""

    def setUp(self) -> None:
        """Create isolated document storage and a fresh API client for each test."""
        self.temp_directory = tempfile.TemporaryDirectory()
        self.client = TestClient(app)
        self._override_document_service()

    def tearDown(self) -> None:
        """Remove dependency overrides and temporary files after each test."""
        app.dependency_overrides.clear()
        self.temp_directory.cleanup()

    def test_chunk_document_succeeds_and_persists_output(self) -> None:
        """Ensure a parsed document can be split into multiple overlapping chunks."""
        source_text = (
            "第一段介绍金融 RAG 项目的背景和目标。\n\n"
            "第二段补充系统设计、日志能力和解析流程。" * 8
        )
        upload_response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.md", source_text.encode("utf-8"), "text/markdown")},
        )
        document_id = upload_response.json()["document_id"]
        self.client.post(f"/api/v1/documents/{document_id}/parse")

        chunk_response = self.client.post(f"/api/v1/documents/{document_id}/chunk")

        self.assertEqual(chunk_response.status_code, 200)
        payload = chunk_response.json()
        self.assertEqual(payload["document_id"], document_id)
        self.assertEqual(payload["status"], "chunked")
        self.assertGreater(payload["chunk_count"], 1)
        self.assertEqual(payload["chunk_count"], len(payload["chunks"]))
        self.assertEqual(payload["chunks"][0]["chunk_index"], 0)
        self.assertGreater(payload["chunks"][0]["char_count"], 0)
        self.assertGreaterEqual(
            payload["chunks"][1]["start_char_index"],
            payload["chunks"][0]["end_char_index"] - payload["chunk_overlap"],
        )

        chunks_output_path = Path(payload["chunks_output_path"])
        self.assertTrue(chunks_output_path.exists())
        stored_payload = json.loads(chunks_output_path.read_text(encoding="utf-8"))
        self.assertEqual(stored_payload["chunk_count"], payload["chunk_count"])

    def test_chunk_document_requires_existing_parse_output(self) -> None:
        """Ensure chunking fails cleanly when the parse step has not run yet."""
        upload_response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": ("guide.md", b"# chunk later", "text/markdown")},
        )
        document_id = upload_response.json()["document_id"]

        chunk_response = self.client.post(f"/api/v1/documents/{document_id}/chunk")

        self.assertEqual(chunk_response.status_code, 404)
        payload = chunk_response.json()
        self.assertEqual(payload["error_code"], "DOCUMENT_PARSED_NOT_FOUND")

    def test_chunk_document_rejects_invalid_chunk_settings(self) -> None:
        """Ensure invalid chunk settings are reported as stable configuration errors."""
        self._override_document_service(chunk_size=100, chunk_overlap=100)
        upload_response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": ("guide.md", b"# config test", "text/markdown")},
        )
        document_id = upload_response.json()["document_id"]
        self.client.post(f"/api/v1/documents/{document_id}/parse")

        chunk_response = self.client.post(f"/api/v1/documents/{document_id}/chunk")

        self.assertEqual(chunk_response.status_code, 500)
        payload = chunk_response.json()
        self.assertEqual(payload["error_code"], "DOCUMENT_CHUNK_CONFIG_INVALID")

    def _override_document_service(
        self,
        *,
        chunk_size: int = 120,
        chunk_overlap: int = 20,
    ) -> None:
        """Override the document service dependency with isolated chunking settings."""
        settings = Settings(
            documents_storage_dir=self.temp_directory.name,
            documents_max_upload_size_mb=25,
            documents_chunk_size_bytes=1024 * 1024,
            document_chunk_size=chunk_size,
            document_chunk_overlap=chunk_overlap,
            document_chunk_preview_limit=80,
        )
        app.dependency_overrides[get_document_service] = lambda: DocumentService(settings)


if __name__ == "__main__":
    unittest.main()
