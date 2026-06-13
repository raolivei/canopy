#!/bin/bash
set -e

TAG="${1:-monarch-dev}"
REPO="ghcr.io/raolivei"

echo "🔍 Watching for changes and auto-deploying to tag: $TAG"
echo "📦 Images: $REPO/canopy-api:$TAG, $REPO/canopy-frontend:$TAG"
echo ""

# Check if fswatch is installed
if ! command -v fswatch &> /dev/null; then
  echo "❌ fswatch not found. Install with: brew install fswatch"
  exit 1
fi

# Function to build and deploy
build_and_deploy() {
  local component=$1
  echo ""
  echo "🔨 Building $component..."

  if [ "$component" = "backend" ]; then
    docker build -t $REPO/canopy-api:$TAG ./backend
    docker push $REPO/canopy-api:$TAG
    echo "✅ Backend image pushed"

    # Restart deployment
    kubectl rollout restart deployment/canopy-monarch-api -n canopy-monarch
    echo "🔄 API deployment restarted"

  elif [ "$component" = "frontend" ]; then
    docker build -t $REPO/canopy-frontend:$TAG ./frontend
    docker push $REPO/canopy-frontend:$TAG
    echo "✅ Frontend image pushed"

    # Restart deployment
    kubectl rollout restart deployment/canopy-monarch-frontend -n canopy-monarch
    echo "🔄 Frontend deployment restarted"
  fi

  echo "⏳ Waiting for rollout to complete..."
  sleep 5
  echo "✨ Changes should be live at https://monarch.eldertree.local"
}

# Watch backend
fswatch -o backend/ | while read; do
  build_and_deploy "backend"
done &

# Watch frontend
fswatch -o frontend/ | while read; do
  build_and_deploy "frontend"
done &

echo "👀 Watching backend/ and frontend/ for changes..."
echo "🌐 Open https://monarch.eldertree.local to see live updates"
echo "⏱️  Changes typically deploy in 30-60 seconds"
echo ""
echo "Press Ctrl+C to stop watching"

# Wait for both background processes
wait
