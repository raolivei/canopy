#!/bin/bash
# Start Canopy locally with assigned ports
# This script ensures no port conflicts with other projects

set -e

# Load port assignments
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$WORKSPACE_ROOT/.env.ports" 2>/dev/null || true

# Use assigned ports or defaults
CANOPY_FRONTEND_PORT=${CANOPY_FRONTEND_PORT:-3001}
CANOPY_API_PORT=${CANOPY_API_PORT:-8001}
CANOPY_POSTGRES_PORT=${CANOPY_POSTGRES_PORT:-5433}
CANOPY_REDIS_PORT=${CANOPY_REDIS_PORT:-6380}

echo "🌳 Starting Canopy with assigned ports..."
echo "   Frontend: $CANOPY_FRONTEND_PORT"
echo "   API: $CANOPY_API_PORT"
echo "   PostgreSQL: $CANOPY_POSTGRES_PORT"
echo "   Redis: $CANOPY_REDIS_PORT"
echo ""

# Check for port conflicts
check_port() {
    local port=$1
    local service=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo "❌ Port $port ($service) is already in use!"
        echo "   Run './scripts/check-ports.sh' to see conflicts"
        exit 1
    fi
}

check_port $CANOPY_FRONTEND_PORT "canopy-frontend"
check_port $CANOPY_API_PORT "canopy-api"
check_port $CANOPY_POSTGRES_PORT "canopy-postgres"
check_port $CANOPY_REDIS_PORT "canopy-redis"

# Start services
cd "$SCRIPT_DIR/.."

# Start PostgreSQL and Redis with assigned ports
if command -v docker-compose &> /dev/null; then
    echo "Starting PostgreSQL and Redis..."
    POSTGRES_PORT=$CANOPY_POSTGRES_PORT REDIS_PORT=$CANOPY_REDIS_PORT \
        docker-compose up -d postgres redis 2>/dev/null || \
        echo "⚠️  docker-compose not available, skipping database startup"
fi

# Start backend
echo "Starting backend API on port $CANOPY_API_PORT..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null || true

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:$CANOPY_POSTGRES_PORT/canopy
REDIS_URL=redis://localhost:$CANOPY_REDIS_PORT/0
SECRET_KEY=dev-secret-key-change-me
DEBUG=True
ENVIRONMENT=development
ALLOWED_HOSTS=localhost,127.0.0.1
API_V1_PREFIX=/v1
EOF
fi

# Update .env with correct ports
sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:postgres@localhost:$CANOPY_POSTGRES_PORT/canopy|" .env
sed -i.bak "s|REDIS_URL=.*|REDIS_URL=redis://localhost:$CANOPY_REDIS_PORT/0|" .env

nohup python3 -m uvicorn app.server:app --reload --host 0.0.0.0 --port $CANOPY_API_PORT > /tmp/canopy-api.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Start frontend
echo "Starting frontend on port $CANOPY_FRONTEND_PORT..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    cat > .env.local << EOF
PORT=$CANOPY_FRONTEND_PORT
NEXT_PUBLIC_API_URL=http://localhost:$CANOPY_API_PORT
EOF
fi

# Update .env.local with correct ports
sed -i.bak "s|PORT=.*|PORT=$CANOPY_FRONTEND_PORT|" .env.local 2>/dev/null || echo "PORT=$CANOPY_FRONTEND_PORT" >> .env.local
sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://localhost:$CANOPY_API_PORT|" .env.local 2>/dev/null || echo "NEXT_PUBLIC_API_URL=http://localhost:$CANOPY_API_PORT" >> .env.local

PORT=$CANOPY_FRONTEND_PORT nohup npm run dev > /tmp/canopy-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ Canopy is starting!"
echo ""
echo "Access points:"
echo "   Frontend: http://localhost:$CANOPY_FRONTEND_PORT"
echo "   API: http://localhost:$CANOPY_API_PORT"
echo "   API Docs: http://localhost:$CANOPY_API_PORT/docs"
echo ""
echo "Logs:"
echo "   Backend: tail -f /tmp/canopy-api.log"
echo "   Frontend: tail -f /tmp/canopy-frontend.log"
echo ""
echo "To stop: pkill -f 'uvicorn.*canopy' && pkill -f 'next.*canopy'"

