"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings model for the Financial RAG service."""

    app_name: str = "Financial RAG API"
    app_version: str = "0.1.0"
    app_description: str = "A starter FastAPI service for a finance-focused RAG project."
    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object to avoid repeated parsing."""
    return Settings()
