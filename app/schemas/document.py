"""Schemas used by document upload and parsing endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class StoredDocumentMetadata(BaseModel):
    """Metadata persisted for each uploaded source document."""

    document_id: str = Field(..., description="Stable identifier assigned to the uploaded document.")
    original_filename: str = Field(..., description="Original filename received from the client.")
    stored_filename: str = Field(..., description="Filename used when persisting the upload on disk.")
    file_extension: str = Field(..., description="Normalized lowercase file extension, including the leading dot.")
    content_type: str = Field(..., description="Content type reported by the client upload request.")
    size_bytes: int = Field(..., ge=0, description="Actual file size persisted on disk in bytes.")
    storage_path: str = Field(..., description="Relative local storage path used for the uploaded document.")
    status: str = Field(..., description="Current document ingestion status.")
    uploaded_at: datetime = Field(..., description="UTC timestamp recorded when the upload completed.")


class DocumentUploadResponse(StoredDocumentMetadata):
    """Normalized response returned after a document upload succeeds."""


class DocumentParseResponse(BaseModel):
    """Response returned after a stored document is parsed into plain text."""

    document_id: str = Field(..., description="Stable identifier assigned to the uploaded document.")
    original_filename: str = Field(..., description="Original filename captured for the source document.")
    stored_filename: str = Field(..., description="Filename used when persisting the upload on disk.")
    file_extension: str = Field(..., description="Normalized lowercase file extension, including the leading dot.")
    source_storage_path: str = Field(..., description="Local storage path pointing to the uploaded source file.")
    parser_name: str = Field(..., description="Parser implementation used to extract plain text.")
    status: str = Field(..., description="Current document parsing status.")
    extracted_char_count: int = Field(..., ge=0, description="Number of plain-text characters extracted from the source document.")
    preview_text: str = Field(..., description="Short preview of the parsed plain-text output.")
    parsed_output_path: str = Field(..., description="Local path of the persisted parsed document JSON.")
    parsed_at: datetime = Field(..., description="UTC timestamp recorded when parsing completed.")


class ParsedDocumentRecord(DocumentParseResponse):
    """Persisted representation of a parsed document, including the full extracted text."""

    extracted_text: str = Field(..., description="Full plain-text content extracted from the source document.")
