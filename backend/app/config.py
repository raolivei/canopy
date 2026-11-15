"""Application configuration and settings management."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Canopy backend.

    Note: Default values are for local development only.
    In production, all secrets are retrieved from Vault via External Secrets Operator
    and provided as environment variables (DATABASE_URL, SECRET_KEY, etc.).
    """

    app_name: str = "Canopy API"
    debug: bool = False
    allowed_hosts: list[str] = ["*"]
    database_url: str = (
        "postgresql+psycopg://canopy:canopy@db/canopy"  # Overridden by DATABASE_URL env var in production
    )
    redis_url: str = "redis://redis:6379/0"  # Overridden by REDIS_URL env var in production
    secret_key: str = "change-me"  # Overridden by SECRET_KEY env var from Vault in production
    environment: str = "development"
    questrade_refresh_token: str | None = None  # For Celery background sync; use Vault in production

    # Optional integration tokens (can be set via env / Vault + ESO; UI can also send per request)
    wise_api_token: str | None = None  # WISE_API_TOKEN
    questrade_refresh_token: str | None = None  # QUESTRADE_REFRESH_TOKEN

    # AI Assistant configuration
    assistant_provider: str = "ollama"  # "ollama" or "openclaw"
    openclaw_url: str | None = None  # e.g., "http://openclaw.eldertree.local:8080/v1"
    openclaw_model: str = "llama3.1:70b"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars
    )


@lru_cache
def get_settings() -> Settings:
    """Load configuration with caching to avoid repeated parsing."""

    return Settings()
