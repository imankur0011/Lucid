"""
Configuration module for the Major Project backend.
Loads environment variables and provides typed settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # --- LLM ---
    gemini_api_key: Optional[str] = None
    llm_provider: str = "gemini"  # gemini | ollama
    llm_model: str = "gemini-2.5-flash"
    ollama_base_url: str = "http://localhost:11434"

    # --- Neo4j ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "majorproject"
    postgres_user: str = "postgres"
    postgres_password: str = "password"

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # --- API Keys ---
    fred_api_key: Optional[str] = None
    news_api_key: Optional[str] = None

    # --- Application ---
    app_env: str = "development"
    app_port: int = 8000
    app_secret_key: str = "change-me-in-production"
    jwt_secret_key: str = "change-me-in-production-jwt-key-32-chars-minimum"
    cors_origins: str = "http://localhost:3000"

    # --- Data Paths ---
    data_raw_dir: str = "../data/raw"
    data_processed_dir: str = "../data/processed"
    faiss_index_dir: str = "../data/faiss_index"

    @property
    def postgres_url(self) -> str:
        if self.postgres_password:
            return (
                f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return (
            f"postgresql+psycopg2://{self.postgres_user}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            ".env",
            "../.env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Singleton settings instance
settings = Settings()
