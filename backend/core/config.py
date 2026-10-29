import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    Designed to be beginner-friendly with robust defaults and explicit validations.
    """
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/mm_chatbot"

    # AI Providers
    DEFAULT_AI_PROVIDER: str = "gemini"  # "gemini" or "openai"
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Embeddings & Vector Search
    EMBEDDING_PROVIDER: str = "gemini"  # "gemini" or "openai"
    EMBEDDING_DIMENSION: int = 768      # 768 for gemini, 1536 for openai

    # Web Search
    WEB_SEARCH_PROVIDER: str = "duckduckgo"
    TAVILY_API_KEY: Optional[str] = None

    # Storage & File Constraints
    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 10

    # API & Network
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    BACKEND_API_URL: str = "http://127.0.0.1:8000"
    CORS_ORIGINS: str = "http://localhost:8501,http://127.0.0.1:8501"

    @property
    def cors_origins_list(self) -> List[str]:
        """Returns parsed list of allowed CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Returns max upload size converted to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Returns cached application settings instance."""
    return Settings()
