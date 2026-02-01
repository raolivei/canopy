"""SQLAlchemy Base and engine setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from backend.app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Create engine using settings
settings = get_settings()
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)
