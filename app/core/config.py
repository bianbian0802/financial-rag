"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings model for the Financial RAG service."""

    app_name: str = "Financial RAG API"
    app_version: str = "0.1.0"
    app_description: str = "A starter FastAPI service for a finance-focused RAG project."
    api_v1_prefix: str = "/api/v1"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    log_level: str = "INFO"
    documents_storage_dir: str = "data/documents"
    documents_max_upload_size_mb: int = 25
    documents_chunk_size_bytes: int = 1048576
    document_chunk_size: int = 800
    document_chunk_overlap: int = 120
    document_chunk_preview_limit: int = 180
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_chat_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30.0
    llm_system_prompt: str = (
        "You are a helpful finance-focused AI assistant. "
        "Answer clearly and avoid fabricating facts."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object to avoid repeated parsing."""
    return Settings()
