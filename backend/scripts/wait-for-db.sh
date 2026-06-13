#!/bin/bash
# Wait for PostgreSQL to be ready before running migrations
# Usage: ./wait-for-db.sh <host> <port> <user> <password> <database>

set -e

HOST="${1:-localhost}"
PORT="${2:-5432}"
USER="${3:-postgres}"
PASSWORD="${4:-postgres}"
DB="${5:-canopy}"

RETRY_LIMIT=30
RETRY_COUNT=0

echo "Waiting for PostgreSQL at $HOST:$PORT to be ready..."

until pg_isready -h "$HOST" -p "$PORT" -U "$USER" > /dev/null 2>&1; do
  RETRY_COUNT=$((RETRY_COUNT + 1))

  if [ "$RETRY_COUNT" -ge "$RETRY_LIMIT" ]; then
    echo "ERROR: PostgreSQL at $HOST:$PORT did not become ready after $RETRY_LIMIT attempts"
    exit 1
  fi

  echo "PostgreSQL not ready yet. Attempt $RETRY_COUNT/$RETRY_LIMIT..."
  sleep 1
done

echo "PostgreSQL is ready at $HOST:$PORT"

# Verify we can connect to the specific database
export PGPASSWORD="$PASSWORD"
if psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -c "SELECT 1" > /dev/null 2>&1; then
  echo "Successfully connected to database: $DB"
  exit 0
else
  echo "ERROR: Could not connect to database $DB"
  exit 1
fi
