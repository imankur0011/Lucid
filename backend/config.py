"""
Configuration module for the Major Project backend.
Loads environment variables and provides typed settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # --- LLM & AI ---
    gemini_api_key: Optional[str] = None
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3.8-flash"

    # --- PostgreSQL 16 (Authoritative Relational Database) ---
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    postgres_db: str = "portfolio_dev"
    postgres_user: str = "postgres"
    postgres_password: str = "password"

    # --- External Financial APIs ---
    fred_api_key: Optional[str] = None
    news_api_key: Optional[str] = None

    # --- Application & Financial Constants ---
    app_env: str = "development"
    app_port: int = 8000
    app_secret_key: str = "change-me-in-production"
    jwt_secret_key: str = "change-me-in-production-jwt-key-32-chars-minimum"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
    risk_free_rate_pct: float = 7.0  # Configurable benchmark yield (India 10Y G-Sec)

    # --- Database URL (Overrides component settings if provided) ---
    database_url: Optional[str] = None

    # --- Data Paths ---
    data_raw_dir: str = "../data/raw"
    data_processed_dir: str = "../data/processed"

    @property
    def postgres_url(self) -> str:
        # Canonical Precedence: Explicit database_url or DATABASE_URL overrides component settings
        raw_url = self.database_url or os.environ.get("DATABASE_URL")
        if raw_url:
            if raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+psycopg2://"):
                return raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return raw_url

        if self.postgres_password:
            return (
                f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return (
            f"postgresql+psycopg2://{self.postgres_user}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def validate_security_keys(self) -> None:
        """Fails closed in staging/production if default or insecure secrets are configured."""
        if self.app_env.lower() in ("staging", "production"):
            if not self.jwt_secret_key or "change-me" in self.jwt_secret_key or len(self.jwt_secret_key) < 32:
                raise ValueError(
                    f"CRITICAL SECURITY CONFIGURATION ERROR: Environment '{self.app_env}' strictly requires "
                    f"a non-default JWT_SECRET_KEY of at least 32 characters (RFC 7518 Section 3.2)."
                )
            if not self.app_secret_key or "change-me" in self.app_secret_key:
                raise ValueError(
                    f"CRITICAL SECURITY CONFIGURATION ERROR: Environment '{self.app_env}' strictly requires "
                    f"a non-default APP_SECRET_KEY."
                )


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
