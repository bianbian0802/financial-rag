"""Service layer responsible for validating and storing uploaded documents."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import AppException
from app.schemas.document import DocumentUploadResponse

logger = logging.getLogger(__name__)


class DocumentService:
    """Validate supported uploads and persist them to local storage in chunks."""

    supported_extensions = {".pdf", ".md", ".txt", ".doc", ".docx"}

    def __init__(self, settings: Settings) -> None:
        """Store document-related settings used by the upload workflow."""
        self.settings = settings

    async def save_upload(self, upload_file: UploadFile) -> DocumentUploadResponse:
        """Persist a supported uploaded file to disk using bounded memory."""
        self._validate_filename(upload_file.filename)

        original_filename = Path(upload_file.filename or "").name
        file_extension = Path(original_filename).suffix.lower()
        document_id = uuid4().hex
        stored_filename = f"{document_id}{file_extension}"
        storage_directory = Path(self.settings.documents_storage_dir)
        storage_directory.mkdir(parents=True, exist_ok=True)
        storage_path = storage_directory / stored_filename

        logger.info("Saving uploaded document %s as %s.", original_filename, stored_filename)

        max_size_bytes = self.settings.documents_max_upload_size_mb * 1024 * 1024
        chunk_size_bytes = self.settings.documents_chunk_size_bytes
        written_size_bytes = 0

        try:
            with storage_path.open("wb") as output_file:
                while True:
                    chunk = await upload_file.read(chunk_size_bytes)
                    if not chunk:
                        break

                    written_size_bytes += len(chunk)
                    if written_size_bytes > max_size_bytes:
                        raise AppException(
                            message=(
                                f"Uploaded file is too large. Maximum allowed size is "
                                f"{self.settings.documents_max_upload_size_mb} MB."
                            ),
                            status_code=413,
                            error_code="DOCUMENT_TOO_LARGE",
                            details={"max_size_mb": self.settings.documents_max_upload_size_mb},
                        )

                    output_file.write(chunk)
        except AppException:
            self._remove_partial_file(storage_path)
            raise
        except OSError as exc:
            self._remove_partial_file(storage_path)
            raise AppException(
                message="Failed to store the uploaded document.",
                status_code=500,
                error_code="DOCUMENT_STORE_FAILED",
            ) from exc
        finally:
            await upload_file.close()

        logger.info(
            "Document upload completed for %s with %s bytes written.",
            original_filename,
            written_size_bytes,
        )

        return DocumentUploadResponse(
            document_id=document_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_extension=file_extension,
            content_type=upload_file.content_type or "application/octet-stream",
            size_bytes=written_size_bytes,
            storage_path=str(storage_path.as_posix()),
            status="uploaded",
            uploaded_at=datetime.now(UTC),
        )

    def _validate_filename(self, filename: str | None) -> None:
        """Ensure the client provided a supported filename before reading any content."""
        if not filename:
            raise AppException(
                message="Uploaded file must include a filename.",
                status_code=400,
                error_code="DOCUMENT_FILENAME_MISSING",
            )

        normalized_extension = Path(filename).suffix.lower()
        if normalized_extension not in self.supported_extensions:
            raise AppException(
                message=(
                    "Unsupported document type. Supported extensions are: "
                    ".pdf, .md, .txt, .doc, .docx."
                ),
                status_code=415,
                error_code="DOCUMENT_TYPE_UNSUPPORTED",
                details={"supported_extensions": sorted(self.supported_extensions)},
            )

    @staticmethod
    def _remove_partial_file(storage_path: Path) -> None:
        """Delete a partially written file if the upload fails midway."""
        if storage_path.exists():
            storage_path.unlink()
