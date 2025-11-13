"""Application configuration and settings management."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Canopy backend."""

    app_name: str = "Canopy API"
    debug: bool = False
    allowed_hosts: List[str] = ["*"]
    database_url: str = "postgresql+psycopg://canopy:canopy@db/canopy"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "change-me"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Load configuration with caching to avoid repeated parsing."""

    return Settings()

