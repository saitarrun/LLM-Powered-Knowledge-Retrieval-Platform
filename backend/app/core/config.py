from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve .env from the project root (one level above this backend/ directory)
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge Retrieval Platform"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").upper()

    # Database (SQLite)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rag.db")

    # Vector Store
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./faiss_index")
    BM25_INDEX_PATH: str = os.getenv("BM25_INDEX_PATH", "./bm25_index")

    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Models
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    RERANKING_MODEL: str = os.getenv("RERANKING_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")

    # Retrieval Limits
    DEFAULT_TOP_K: int = 5
    MAX_TOKENS: int = 2000
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    class Config:
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
