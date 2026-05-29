"""Document upload endpoints for the Day9 ingestion entrypoint."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import Settings, get_settings
from app.schemas.document import DocumentUploadResponse
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
