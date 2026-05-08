#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3.11+ to run the backend."
  exit 1
fi

VENV_DIR="$ROOT_DIR/backend/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Backend venv not found at $VENV_DIR. Create it first (python3 -m venv backend/.venv)."
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt"

export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Install Node.js 18+ to run the frontend."
  exit 1
fi

if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
  (cd "$ROOT_DIR/frontend" && npm install)
fi

echo "Starting backend on http://localhost:8000"
(cd "$ROOT_DIR/backend" && uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

echo "Starting frontend on http://localhost:3000"
(cd "$ROOT_DIR/frontend" && npm run dev -- --host 0.0.0.0 --port 3000) &
FRONTEND_PID=$!

cleanup() {
  echo "Stopping services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM

wait -n "$BACKEND_PID" "$FRONTEND_PID"
cleanup
wait || true
