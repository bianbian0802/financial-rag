"""Tests for the Day9 document upload API."""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.v1.documents import get_document_service
from app.core.config import Settings
from app.main import app
from app.services.document_service import DocumentService


class DocumentsApiTests(unittest.TestCase):
    """Verify document uploads are validated and stored as expected."""

    def setUp(self) -> None:
        """Create an isolated storage directory and test client for each test."""
        self.temp_directory = tempfile.TemporaryDirectory()
        self.client = TestClient(app)
        self._override_document_service()

    def tearDown(self) -> None:
        """Clear dependency overrides and remove temporary test files."""
        app.dependency_overrides.clear()
        self.temp_directory.cleanup()

    def test_upload_markdown_document_succeeds(self) -> None:
        """Ensure a supported markdown file is stored and returns metadata."""
        response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": ("guide.md", b"# upload ok", "text/markdown")},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["original_filename"], "guide.md")
        self.assertEqual(payload["file_extension"], ".md")
        self.assertEqual(payload["status"], "uploaded")
        self.assertEqual(payload["size_bytes"], len(b"# upload ok"))
        stored_file = Path(payload["storage_path"])
        self.assertTrue(stored_file.exists())
        self.assertEqual(stored_file.read_bytes(), b"# upload ok")

    def test_upload_large_docx_document_succeeds_with_chunked_write(self) -> None:
        """Ensure multi-megabyte Word uploads succeed within the configured size limit."""
        word_bytes = b"x" * ((2 * 1024 * 1024) + 321)
        response = self.client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "proposal.docx",
                    word_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["file_extension"], ".docx")
        self.assertEqual(payload["size_bytes"], len(word_bytes))
        self.assertTrue(Path(payload["storage_path"]).exists())

    def test_upload_rejects_unsupported_extension(self) -> None:
        """Ensure files outside the supported extension list are rejected."""
        response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": ("payload.exe", b"oops", "application/octet-stream")},
        )

        self.assertEqual(response.status_code, 415)
        payload = response.json()
        self.assertEqual(payload["error_code"], "DOCUMENT_TYPE_UNSUPPORTED")

    def test_upload_rejects_oversized_file_and_cleans_partial_output(self) -> None:
        """Ensure oversized uploads stop early and do not keep partial files on disk."""
        self._override_document_service(max_upload_size_mb=1)
        too_large_bytes = b"x" * ((1 * 1024 * 1024) + 1)

        response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": ("large.doc", too_large_bytes, "application/msword")},
        )

        self.assertEqual(response.status_code, 413)
        payload = response.json()
        self.assertEqual(payload["error_code"], "DOCUMENT_TOO_LARGE")
        stored_files = list(Path(self.temp_directory.name).iterdir())
        self.assertEqual(stored_files, [])

    def _override_document_service(self, *, max_upload_size_mb: int = 25) -> None:
        """Override the document service dependency with isolated test storage settings."""
        settings = Settings(
            documents_storage_dir=self.temp_directory.name,
            documents_max_upload_size_mb=max_upload_size_mb,
            documents_chunk_size_bytes=1024 * 1024,
        )
        app.dependency_overrides[get_document_service] = lambda: DocumentService(settings)


if __name__ == "__main__":
    unittest.main()
