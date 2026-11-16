"""Pytest conftest: make postgres-only column types compile on SQLite.

Several models use ``ARRAY(String)`` and ``JSONB`` which are postgres-specific.
For unit tests we swap in plain ``TEXT``/``JSON`` fallbacks so an in-memory
SQLite engine can create the schema and exercise the ORM end-to-end.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Numeric, create_engine, event
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.server import create_app
from backend.db.base import Base
from backend.db.session import get_db


@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(_element, _compiler, **_kw):  # pragma: no cover
    return "TEXT"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_element, _compiler, **_kw):  # pragma: no cover
    return "JSON"


@compiles(Numeric, "sqlite")
def _compile_numeric_sqlite(element, _compiler, **_kw):  # pragma: no cover
    return "REAL"


@pytest.fixture(scope="function")
def db():
    """Provide an in-memory SQLite database for testing."""
    # One shared connection for every thread: the FastAPI TestClient runs
    # endpoints on a worker thread, and each :memory: connection would
    # otherwise be a separate, empty database.
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    """FastAPI test client whose ``get_db`` dependency yields the in-memory session."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def query_counter(db):
    """Count SQL statements issued through the test session's engine."""
    counts = {"statements": 0}
    engine = db.get_bind()

    def _count(*_args, **_kwargs):
        counts["statements"] += 1

    event.listen(engine, "before_cursor_execute", _count)
    yield counts
    event.remove(engine, "before_cursor_execute", _count)
