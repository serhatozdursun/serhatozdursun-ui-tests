#!/usr/bin/env bash
# Start the resume site on PORT (default 3000). Matches ui_local_pytest.yml CI flow.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESUME_DIR="${RESUME_DIR:-$ROOT/resume}"
PORT="${PORT:-3000}"

if [ ! -d "$RESUME_DIR/.next" ]; then
  echo "[resume] No build found — run: bash scripts/resume_env_setup.sh"
  exit 1
fi

cd "$RESUME_DIR"
export PORT

if curl -sf "http://localhost:${PORT}/" >/dev/null 2>&1; then
  echo "[resume] Already running on http://localhost:${PORT}/"
  exit 0
fi

echo "[resume] Starting on http://localhost:${PORT}/ (background)"
nohup yarn start > /tmp/resume-server.log 2>&1 &
PID=$!

for i in $(seq 1 30); do
  if curl -sf "http://localhost:${PORT}/" >/dev/null; then
    echo "[resume] Ready (pid $PID)"
    exit 0
  fi
  sleep 2
done

echo "[resume] Failed to start — see /tmp/resume-server.log"
exit 1
