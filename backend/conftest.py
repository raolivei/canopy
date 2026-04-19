"""Project-level pytest bootstrap for Canopy backend.

This file is intentionally tiny and runs *before* any test module or the
in-test ``backend/tests/conftest.py`` is imported. Its only job is to make
`pytest` work out-of-the-box from a fresh direnv shell:

* point the app at an in-memory SQLite DB so ``backend.db.base`` can create
  its engine at import time without requiring a running Postgres;
* make sure the repo root (the parent of ``backend/``) is on ``sys.path`` so
  absolute imports like ``from backend.db.base import Base`` resolve even when
  pytest is invoked directly from the ``backend/`` directory.

Postgres-specific column types (``ARRAY``, ``JSONB``) are still mapped to
SQLite-compatible equivalents in ``backend/tests/conftest.py``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
