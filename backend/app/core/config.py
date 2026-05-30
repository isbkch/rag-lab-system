"""
Core configuration module for the RAG platform.
"""

import sys
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Application
    APP_NAME: str = "Enterprise RAG Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # JWT Authentication
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    DEFAULT_ADMIN_PASSWORD: Optional[str] = None

    # Error Tracking
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600  # 1 hour

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Vector Database
    VECTOR_DB_PROVIDER: str = "chroma"
    VECTOR_DB_COLLECTION: str = "documents"

    # Pinecone
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: Optional[str] = None

    # Weaviate
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_API_KEY: Optional[str] = None

    # Chroma
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Embeddings
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSIONS: int = 1536
    CACHE_EMBEDDINGS: bool = True
    EMBEDDING_BATCH_SIZE: int = 100

    # Document Processing
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    CHUNKING_STRATEGY: str = "recursive"

    # Search
    MAX_SEARCH_RESULTS: int = 10
    SIMILARITY_THRESHOLD: float = 0.7

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
    )

    def __init__(self, **kwargs):
        """Initialize settings and set defaults."""
        super().__init__(**kwargs)
        # Use SECRET_KEY for JWT if JWT_SECRET_KEY not provided
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = self.SECRET_KEY

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        if "pytest" in sys.modules:
            return (
                init_settings,
                dotenv_settings,
                file_secret_settings,
            )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    if "pytest" in sys.modules:
        return Settings(_env_file=".env.test")
    return Settings()


settings = get_settings()
