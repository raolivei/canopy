#!/usr/bin/env bash
# Prove Alembic migrations on a real PostgreSQL database (#48).
#
# 1. Two upgrades to head start at the same time on an empty database; the
#    advisory lock in alembic/env.py must serialise them and both must succeed.
# 2. The database ends at the single head revision.
# 3. A third upgrade is a no-op.
# 4. The migrated schema matches the models (alembic check).
#
# Needs DATABASE_URL pointing at a disposable database. Run from anywhere.
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must point at a disposable PostgreSQL database}"
case "$DATABASE_URL" in
  postgresql*) ;;
  *) echo "DATABASE_URL must be a PostgreSQL URL" >&2; exit 2 ;;
esac

backend_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$(dirname "$backend_dir")${PYTHONPATH:+:$PYTHONPATH}"
cd "$backend_dir"

echo "== concurrent upgrades on an empty database"
alembic upgrade head > /tmp/canopy-migrate-a.log 2>&1 &
pid_a=$!
alembic upgrade head > /tmp/canopy-migrate-b.log 2>&1 &
pid_b=$!
status=0
wait "$pid_a" || status=1
wait "$pid_b" || status=1
cat /tmp/canopy-migrate-a.log /tmp/canopy-migrate-b.log
if [ "$status" -ne 0 ]; then
  echo "a concurrent upgrade failed" >&2
  exit 1
fi

echo "== database is at the single head"
heads="$(alembic heads | awk '{print $1}')"
current="$(alembic current | awk '{print $1}')"
if [ "$(echo "$heads" | wc -l | tr -d ' ')" -ne 1 ]; then
  echo "expected one head, got: $heads" >&2
  exit 1
fi
if [ "$current" != "$heads" ]; then
  echo "current revision '$current' is not head '$heads'" >&2
  exit 1
fi

echo "== repeat upgrade is a no-op"
alembic upgrade head

echo "== schema matches the models"
alembic check

echo "PostgreSQL migrations OK at $current"
