"""Application configuration and settings management."""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Canopy backend.
    
    Note: Default values are for local development only.
    In production, all secrets are retrieved from Vault via External Secrets Operator
    and provided as environment variables (DATABASE_URL, SECRET_KEY, etc.).
    """

    app_name: str = "Canopy API"
    debug: bool = False
    allowed_hosts: List[str] = ["*"]
    database_url: str = "postgresql+psycopg://canopy:canopy@db/canopy"  # Overridden by DATABASE_URL env var in production
    redis_url: str = "redis://redis:6379/0"  # Overridden by REDIS_URL env var in production
    secret_key: str = "change-me"  # Overridden by SECRET_KEY env var from Vault in production
    environment: str = "development"
    questrade_refresh_token: Optional[str] = None  # For Celery background sync; use Vault in production

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra env vars
    )


@lru_cache
def get_settings() -> Settings:
    """Load configuration with caching to avoid repeated parsing."""

    return Settings()

