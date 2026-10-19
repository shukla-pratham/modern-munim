#!/usr/bin/env bash
# Development only: start backend and frontend for FF Marketplace.
# Backend: http://127.0.0.1:8000  |  Frontend: http://localhost:3000
# For production use: docker compose up -d --build (see docs/deployment/DEPLOY.md).

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

kill_port() {
  local port=$1
  local pid
  pid=$(lsof -ti ":$port" 2>/dev/null) || true
  if [ -n "$pid" ]; then
    echo "Stopping process on port $port (PID $pid)..."
    kill -9 $pid 2>/dev/null || true
    sleep 1
  fi
}
kill_port 8000
kill_port 3000

cleanup() {
  echo ""
  echo "Stopping servers..."
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

# Start backend
cd "$ROOT/backend"
if [ -d "venv" ]; then
  source venv/bin/activate
fi
echo "Starting backend on http://127.0.0.1:8000 ..."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be up
sleep 2

# Start frontend (final-frontend = executive-command-center integrated with backend)
cd "$ROOT/final-frontend"
echo "Starting frontend on http://localhost:3000 ..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both."
echo ""

wait
