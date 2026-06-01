"""Document upload endpoints for the Day9 ingestion entrypoint."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import Settings, get_settings
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentEmbeddingResponse,
    DocumentParseResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter()


def get_document_service(settings: Settings = Depends(get_settings)) -> DocumentService:
    """Create a document service instance for the current request."""
    return DocumentService(settings)


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    summary="Upload a source document for later RAG ingestion",
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """Validate and store a supported source document for downstream processing."""
    return await service.save_upload(file)


@router.post(
    "/documents/{document_id}/parse",
    response_model=DocumentParseResponse,
    summary="Parse an uploaded document into plain text",
)
def parse_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentParseResponse:
    """Load a previously uploaded document and extract plain text for later RAG stages."""
    return service.parse_document(document_id)


@router.post(
    "/documents/{document_id}/chunk",
    response_model=DocumentChunkResponse,
    summary="Chunk a parsed document into retrieval-ready segments",
)
def chunk_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentChunkResponse:
    """Load a parsed document and split its text into reusable chunks for downstream RAG work."""
    return service.chunk_document(document_id)


@router.post(
    "/documents/{document_id}/embed",
    response_model=DocumentEmbeddingResponse,
    summary="Generate embeddings for a chunked document",
)
async def embed_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentEmbeddingResponse:
    """Load a chunked document and generate dense vectors for each chunk."""
    return await service.embed_document(document_id)
