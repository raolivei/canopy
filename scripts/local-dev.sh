#!/usr/bin/env bash
# Canopy local dev — brings the full stack up with hot reload and waits
# until both services are ready, then prints the URLs you can point
# Cursor's Simple Browser at.
#
# Mirrors the SwimTO `make dev` flow. Ctrl-C tails logs until you quit.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Load workspace-config port assignments if present
PORTS_FILE="../workspace-config/ports/.env.ports"
if [[ -f "$PORTS_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$PORTS_FILE"
fi

FRONTEND_PORT="${CANOPY_FRONTEND_PORT:-3001}"
API_PORT="${CANOPY_API_PORT:-8001}"
POSTGRES_PORT="${CANOPY_POSTGRES_PORT:-5433}"
REDIS_PORT="${CANOPY_REDIS_PORT:-6380}"

echo "🌳 Canopy — local dev"
echo "====================="
echo ""
echo "Ports:"
echo "  Frontend : http://localhost:$FRONTEND_PORT"
echo "  API docs : http://localhost:$API_PORT/docs"
echo "  Postgres : localhost:$POSTGRES_PORT"
echo "  Redis    : localhost:$REDIS_PORT"
echo ""

# ---------------------------------------------------------------------------
# Docker sanity check
# ---------------------------------------------------------------------------
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker daemon not reachable."
  echo ""
  echo "  Rancher Desktop: open -a 'Rancher Desktop'"
  echo "  Then wait ~30s for the VM to boot and re-run: make dev"
  exit 1
fi

# ---------------------------------------------------------------------------
# Bring up the stack detached, then tail logs
# ---------------------------------------------------------------------------
echo "Starting containers..."
docker-compose up -d

echo ""
echo "Waiting for API to become healthy..."
for _ in $(seq 1 60); do
  if curl -fsS "http://localhost:$API_PORT/v1/health" >/dev/null 2>&1 \
     || curl -fsS "http://localhost:$API_PORT/docs" >/dev/null 2>&1; then
    echo "  ✅ API ready"
    break
  fi
  sleep 1
done

echo "Waiting for frontend (this takes ~60s on first run while npm install runs)..."
for _ in $(seq 1 180); do
  if curl -fsS "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
    echo "  ✅ Frontend ready"
    break
  fi
  sleep 1
done

cat <<EOF

✅ Canopy is running.

   Frontend : http://localhost:$FRONTEND_PORT
   API docs : http://localhost:$API_PORT/docs

Hot reload is active for both services:
  - Edit any file under backend/  → uvicorn reloads automatically
  - Edit any file under frontend/ → Next.js HMR refreshes the browser

In Cursor, open the Simple Browser (Cmd+Shift+P → "Simple Browser: Show")
and paste http://localhost:$FRONTEND_PORT — every save you see me make
will show up there within a second or two.

Tailing logs (Ctrl-C to stop tailing; containers keep running):
EOF
echo ""

trap 'echo; echo "(containers still running — stop with: make down)"; exit 0' INT

docker-compose logs -f --tail=50
