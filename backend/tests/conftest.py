"""Pytest conftest: make postgres-only column types compile on SQLite.

Several models use ``ARRAY(String)`` and ``JSONB`` which are postgres-specific.
For unit tests we swap in plain ``TEXT``/``JSON`` fallbacks so an in-memory
SQLite engine can create the schema and exercise the ORM end-to-end.
"""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(ARRAY, "sqlite")
def _compile_array_sqlite(_element, _compiler, **_kw):  # pragma: no cover
    return "TEXT"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_element, _compiler, **_kw):  # pragma: no cover
    return "JSON"
