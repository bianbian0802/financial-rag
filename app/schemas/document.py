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


class DocumentChunk(BaseModel):
    """Single chunk derived from a parsed document for downstream retrieval work."""

    chunk_id: str = Field(..., description="Stable chunk identifier unique within the document.")
    chunk_index: int = Field(..., ge=0, description="Zero-based position of the chunk within the document.")
    text: str = Field(..., description="Plain-text content contained in this chunk.")
    char_count: int = Field(..., ge=0, description="Character length of the chunk text.")
    start_char_index: int = Field(..., ge=0, description="Inclusive start offset in the cleaned document text.")
    end_char_index: int = Field(..., ge=0, description="Exclusive end offset in the cleaned document text.")
    preview_text: str = Field(..., description="Short preview string for UI or debugging output.")


class DocumentChunkResponse(BaseModel):
    """Response returned after a parsed document is segmented into retrieval chunks."""

    document_id: str = Field(..., description="Stable identifier assigned to the uploaded document.")
    source_parsed_output_path: str = Field(..., description="Parsed JSON file consumed as the source for chunking.")
    chunk_count: int = Field(..., ge=0, description="Number of chunks generated from the parsed document.")
    chunk_size: int = Field(..., ge=1, description="Target maximum character count used for chunking.")
    chunk_overlap: int = Field(..., ge=0, description="Configured overlap size carried between adjacent chunks.")
    cleaned_char_count: int = Field(..., ge=0, description="Character length of the cleaned text after normalization.")
    chunks_output_path: str = Field(..., description="Local path of the persisted chunk JSON output.")
    status: str = Field(..., description="Current chunking status.")
    chunked_at: datetime = Field(..., description="UTC timestamp recorded when chunking completed.")
    chunks: list[DocumentChunk] = Field(..., description="Ordered chunk list generated from the source document.")


class EmbeddingUsage(BaseModel):
    """Token usage metadata reported by an embedding provider, when available."""

    prompt_tokens: int = Field(..., ge=0, description="Token count consumed by the embedding request input.")
    total_tokens: int = Field(..., ge=0, description="Total token count reported for the embedding request.")


class EmbeddedDocumentChunk(DocumentChunk):
    """Chunk payload extended with the generated embedding vector."""

    embedding: list[float] = Field(..., description="Dense vector generated for the chunk text.")
    embedding_dimensions: int = Field(..., ge=0, description="Length of the embedding vector.")


class DocumentEmbeddingResponse(BaseModel):
    """Response returned after a chunked document is converted into dense vectors."""

    document_id: str = Field(..., description="Stable identifier assigned to the uploaded document.")
    source_chunks_output_path: str = Field(..., description="Chunk JSON file consumed as the source for embedding generation.")
    embedding_model: str = Field(..., description="Embedding model used for vector generation.")
    provider: str = Field(..., description="Embedding provider type used for this document.")
    chunk_count: int = Field(..., ge=0, description="Number of embedded chunks produced for the document.")
    embedding_dimensions: int = Field(..., ge=0, description="Dimension count shared by the generated chunk vectors.")
    embeddings_output_path: str = Field(..., description="Local path of the persisted embedding JSON output.")
    status: str = Field(..., description="Current embedding status.")
    usage: EmbeddingUsage | None = Field(
        default=None,
        description="Optional provider token usage aggregated across embedding batches.",
    )
    embedded_at: datetime = Field(..., description="UTC timestamp recorded when embedding generation completed.")
    embedded_chunks: list[EmbeddedDocumentChunk] = Field(
        ...,
        description="Ordered list of chunk records paired with their generated embeddings.",
    )
