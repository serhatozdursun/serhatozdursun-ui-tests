#!/usr/bin/env bash
# Clone and build serhatozdursun/resume for local UI tests on http://localhost:3000/
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESUME_DIR="${RESUME_DIR:-$ROOT/resume}"
RESUME_REPO="${RESUME_REPO:-https://github.com/serhatozdursun/resume.git}"

cd "$ROOT"

if ! command -v yarn >/dev/null 2>&1; then
  echo "[resume] ERROR: yarn not found (Node.js required)"
  exit 1
fi

if [ ! -d "$RESUME_DIR/.git" ]; then
  echo "[resume] Cloning $RESUME_REPO into $RESUME_DIR"
  git clone "$RESUME_REPO" "$RESUME_DIR"
else
  echo "[resume] Updating existing clone at $RESUME_DIR"
  git -C "$RESUME_DIR" fetch origin main
  git -C "$RESUME_DIR" checkout main
  git -C "$RESUME_DIR" pull --ff-only origin main || true
fi

echo "[resume] Installing dependencies..."
(cd "$RESUME_DIR" && yarn install --frozen-lockfile)

echo "[resume] Building production bundle..."
(cd "$RESUME_DIR" && yarn build)

echo "[resume] Ready. Start with: bash scripts/resume_start.sh"
