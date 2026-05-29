"""Schemas used by document upload endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Normalized response returned after a document upload succeeds."""

    document_id: str = Field(..., description="Stable identifier assigned to the uploaded document.")
    original_filename: str = Field(..., description="Original filename received from the client.")
    stored_filename: str = Field(..., description="Filename used when persisting the upload on disk.")
    file_extension: str = Field(..., description="Normalized lowercase file extension, including the leading dot.")
    content_type: str = Field(..., description="Content type reported by the client upload request.")
    size_bytes: int = Field(..., ge=0, description="Actual file size persisted on disk in bytes.")
    storage_path: str = Field(..., description="Relative local storage path used for the uploaded document.")
    status: str = Field(..., description="Current document ingestion status.")
    uploaded_at: datetime = Field(..., description="UTC timestamp recorded when the upload completed.")
