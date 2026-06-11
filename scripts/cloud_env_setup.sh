#!/usr/bin/env bash
# Cursor Cloud Agent — environment update script (paste into dashboard Environment tab).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "[env] Python: $(python3 --version)"
echo "[env] Node: $(node --version 2>/dev/null || echo 'not installed')"

if ! command -v poetry >/dev/null 2>&1; then
  echo "[env] Installing Poetry..."
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="${HOME}/.local/bin:${PATH}"
fi

poetry env use python3
poetry install --no-interaction

if ! command -v gh >/dev/null 2>&1; then
  echo "[env] WARNING: gh CLI not found — PR create/merge will fail until installed"
fi

if ! command -v google-chrome >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1; then
  echo "[env] WARNING: Chrome/Chromium not found — install for headless Selenium"
fi

mkdir -p reports/html reports/screenshots reports/healer reports/discoverer

echo "[env] Running lint checks..."
poetry run pre-commit install
poetry run pre-commit run --all-files

echo "[env] Smoke pytest (production, chrome, quiet)..."
poetry run pytest -q --browser=chrome -m "not in_progress" --base_url=https://www.serhatozdursun.com

echo "[env] Ready for UI Test Healer and UI Test Discoverer agents."
