"""Service layer responsible for validating and storing uploaded documents."""

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from docx import Document as WordDocument
from fastapi import UploadFile
from pydantic import ValidationError
from pypdf import PdfReader

from app.core.config import Settings
from app.core.exceptions import AppException
from app.schemas.document import (
    DocumentParseResponse,
    DocumentUploadResponse,
    ParsedDocumentRecord,
    StoredDocumentMetadata,
)

logger = logging.getLogger(__name__)


class DocumentService:
    """Validate supported uploads and persist them to local storage in chunks."""

    supported_extensions = {".pdf", ".md", ".txt", ".doc", ".docx"}
    metadata_directory_name = "metadata"
    parsed_directory_name = "parsed"
    preview_text_limit = 240

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

        upload_response = DocumentUploadResponse(
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
        self._write_document_metadata(upload_response)
        return upload_response

    def parse_document(self, document_id: str) -> DocumentParseResponse:
        """Load an uploaded document by ID, extract plain text, and persist the parse result."""
        metadata = self._load_document_metadata(document_id)
        storage_path = Path(metadata.storage_path)
        if not storage_path.exists():
            raise AppException(
                message="The uploaded document file could not be found on disk.",
                status_code=404,
                error_code="DOCUMENT_FILE_MISSING",
                details={"document_id": document_id},
            )

        parser_name, extracted_text = self._extract_text(storage_path, metadata.file_extension)
        normalized_text = self._normalize_extracted_text(extracted_text)
        if not normalized_text:
            raise AppException(
                message="The document was parsed, but no extractable text was found.",
                status_code=422,
                error_code="DOCUMENT_TEXT_EMPTY",
                details={"document_id": document_id, "file_extension": metadata.file_extension},
            )

        parsed_directory = self._get_parsed_directory()
        parsed_directory.mkdir(parents=True, exist_ok=True)
        parsed_output_path = parsed_directory / f"{document_id}.json"
        parsed_at = datetime.now(UTC)

        parsed_record = ParsedDocumentRecord(
            document_id=metadata.document_id,
            original_filename=metadata.original_filename,
            stored_filename=metadata.stored_filename,
            file_extension=metadata.file_extension,
            source_storage_path=metadata.storage_path,
            parser_name=parser_name,
            status="parsed",
            extracted_char_count=len(normalized_text),
            preview_text=self._build_preview_text(normalized_text),
            parsed_output_path=str(parsed_output_path.as_posix()),
            parsed_at=parsed_at,
            extracted_text=normalized_text,
        )
        self._write_json_file(parsed_output_path, parsed_record.model_dump(mode="json"))

        logger.info(
            "Document %s parsed successfully using %s with %s extracted characters.",
            document_id,
            parser_name,
            parsed_record.extracted_char_count,
        )

        return DocumentParseResponse.model_validate(parsed_record.model_dump())

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

    def _write_document_metadata(self, metadata: StoredDocumentMetadata) -> None:
        """Persist upload metadata so later steps can resolve documents by document ID."""
        metadata_directory = self._get_metadata_directory()
        metadata_directory.mkdir(parents=True, exist_ok=True)
        metadata_path = metadata_directory / f"{metadata.document_id}.json"
        self._write_json_file(metadata_path, metadata.model_dump(mode="json"))

    def _load_document_metadata(self, document_id: str) -> StoredDocumentMetadata:
        """Load persisted upload metadata, reconstructing it for older uploads when needed."""
        if not document_id:
            raise AppException(
                message="Document ID must not be empty.",
                status_code=400,
                error_code="DOCUMENT_ID_MISSING",
            )

        metadata_path = self._get_metadata_directory() / f"{document_id}.json"
        if metadata_path.exists():
            try:
                metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                return StoredDocumentMetadata.model_validate(metadata_payload)
            except (OSError, json.JSONDecodeError, ValidationError) as exc:
                raise AppException(
                    message="Stored document metadata is corrupted or unreadable.",
                    status_code=500,
                    error_code="DOCUMENT_METADATA_INVALID",
                    details={"document_id": document_id},
                ) from exc

        return self._reconstruct_metadata(document_id)

    def _reconstruct_metadata(self, document_id: str) -> StoredDocumentMetadata:
        """Rebuild minimal metadata for files uploaded before metadata persistence existed."""
        storage_directory = Path(self.settings.documents_storage_dir)
        matching_files = [
            candidate
            for candidate in storage_directory.glob(f"{document_id}.*")
            if candidate.is_file() and candidate.suffix.lower() in self.supported_extensions
        ]
        if not matching_files:
            raise AppException(
                message="No uploaded document was found for the provided document ID.",
                status_code=404,
                error_code="DOCUMENT_NOT_FOUND",
                details={"document_id": document_id},
            )

        source_file = matching_files[0]
        source_file_stat = source_file.stat()
        reconstructed_metadata = StoredDocumentMetadata(
            document_id=document_id,
            original_filename=source_file.name,
            stored_filename=source_file.name,
            file_extension=source_file.suffix.lower(),
            content_type="application/octet-stream",
            size_bytes=source_file_stat.st_size,
            storage_path=str(source_file.as_posix()),
            status="uploaded",
            uploaded_at=datetime.fromtimestamp(source_file_stat.st_mtime, tz=UTC),
        )
        logger.warning(
            "Reconstructed document metadata for %s because no metadata file existed.",
            document_id,
        )
        self._write_document_metadata(reconstructed_metadata)
        return reconstructed_metadata

    def _extract_text(self, storage_path: Path, file_extension: str) -> tuple[str, str]:
        """Dispatch to the appropriate parser based on the stored file extension."""
        if file_extension in {".md", ".txt"}:
            return "plain_text", self._read_text_document(storage_path)
        if file_extension == ".pdf":
            return "pypdf", self._extract_pdf_text(storage_path)
        if file_extension == ".docx":
            return "python-docx", self._extract_docx_text(storage_path)
        if file_extension == ".doc":
            raise AppException(
                message="Legacy .doc parsing is not supported yet. Please convert the file to .docx.",
                status_code=422,
                error_code="DOCUMENT_PARSE_UNSUPPORTED",
                details={"file_extension": ".doc"},
            )

        raise AppException(
            message="Unsupported document type for parsing.",
            status_code=415,
            error_code="DOCUMENT_PARSE_TYPE_UNSUPPORTED",
            details={"file_extension": file_extension},
        )

    @staticmethod
    def _read_text_document(storage_path: Path) -> str:
        """Read plain-text documents using a small set of practical encodings."""
        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                return storage_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
            except OSError as exc:
                raise AppException(
                    message="Failed to read the uploaded text document.",
                    status_code=500,
                    error_code="DOCUMENT_READ_FAILED",
                ) from exc

        raise AppException(
            message="Failed to decode the uploaded text document with the supported encodings.",
            status_code=422,
            error_code="DOCUMENT_DECODE_FAILED",
            details={"supported_encodings": ["utf-8", "utf-8-sig", "gb18030"]},
        )

    @staticmethod
    def _extract_pdf_text(storage_path: Path) -> str:
        """Extract text from each PDF page and merge the results into one string."""
        try:
            reader = PdfReader(str(storage_path))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise AppException(
                message="Failed to extract text from the uploaded PDF document.",
                status_code=422,
                error_code="DOCUMENT_PARSE_FAILED",
                details={"file_extension": ".pdf"},
            ) from exc

    @staticmethod
    def _extract_docx_text(storage_path: Path) -> str:
        """Extract paragraph and table cell text from a DOCX document."""
        try:
            document = WordDocument(str(storage_path))
        except Exception as exc:
            raise AppException(
                message="Failed to open the uploaded DOCX document.",
                status_code=422,
                error_code="DOCUMENT_PARSE_FAILED",
                details={"file_extension": ".docx"},
            ) from exc

        fragments = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        for table in document.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    fragments.append(" | ".join(row_cells))
        return "\n".join(fragments)

    @staticmethod
    def _normalize_extracted_text(extracted_text: str) -> str:
        """Normalize line endings and collapse noisy blank lines in parsed output."""
        normalized_text = extracted_text.replace("\r\n", "\n").replace("\r", "\n")
        normalized_text = "\n".join(line.rstrip() for line in normalized_text.split("\n"))
        normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text)
        return normalized_text.strip()

    def _build_preview_text(self, extracted_text: str) -> str:
        """Create a short preview for API responses without returning the full parsed text."""
        if len(extracted_text) <= self.preview_text_limit:
            return extracted_text
        return f"{extracted_text[: self.preview_text_limit].rstrip()}..."

    def _write_json_file(self, output_path: Path, payload: dict[str, object]) -> None:
        """Write structured JSON to disk using UTF-8 so later pipeline steps can reuse it."""
        try:
            output_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise AppException(
                message="Failed to persist document metadata or parsed output.",
                status_code=500,
                error_code="DOCUMENT_PERSIST_FAILED",
                details={"output_path": str(output_path)},
            ) from exc

    def _get_metadata_directory(self) -> Path:
        """Return the directory used for upload metadata sidecar files."""
        return Path(self.settings.documents_storage_dir) / self.metadata_directory_name

    def _get_parsed_directory(self) -> Path:
        """Return the directory used for parsed text output files."""
        return Path(self.settings.documents_storage_dir) / self.parsed_directory_name

    @staticmethod
    def _remove_partial_file(storage_path: Path) -> None:
        """Delete a partially written file if the upload fails midway."""
        if storage_path.exists():
            storage_path.unlink()
