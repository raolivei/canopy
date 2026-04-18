"""Reset all Canopy data while preserving schema.

Usage::

    # From the repo root, with DATABASE_URL set:
    python -m backend.scripts.reset_data

    # Or against Docker Compose:
    docker-compose exec api python -m backend.scripts.reset_data

The script prints per-table row counts before and after deleting, then
commits. Requires the operator to type ``RESET ALL DATA`` to confirm.
"""

from __future__ import annotations

import sys

from backend.db.session import SessionLocal
from backend.services.admin import reset_all_data


def _print_counts(db, heading: str) -> None:
    from backend.api.admin import _COUNT_MODELS

    print(heading)
    for label, model in _COUNT_MODELS:
        count = db.query(model).count()
        print(f"  {label:<30} {count}")


def main() -> int:
    confirm = None
    for arg in sys.argv[1:]:
        if arg.startswith("--confirm="):
            confirm = arg.split("=", 1)[1]

    if confirm is None:
        try:
            confirm = input(
                "This will DELETE every row from every data table. Type "
                "'RESET ALL DATA' to proceed: "
            )
        except EOFError:
            confirm = ""

    if confirm != "RESET ALL DATA":
        print("Aborted.")
        return 1

    db = SessionLocal()
    try:
        _print_counts(db, "Before:")
        report = reset_all_data(db)
        db.commit()
        _print_counts(db, "\nAfter:")
        print(f"\nDeleted {report.total} rows across {len(report.deleted)} tables.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
