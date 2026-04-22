#!/usr/bin/env sh
# Run Alembic migrations (same as: cd backend && alembic upgrade head).
# Docker Compose: docker compose exec api sh /app/backend/scripts/migrate.sh
# Kubernetes:    kubectl -n canopy exec deploy/canopy-api -- sh /app/backend/scripts/migrate.sh
set -euo pipefail
cd "$(dirname "$0")/.."
exec alembic upgrade head
