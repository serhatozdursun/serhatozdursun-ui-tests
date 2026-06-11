#!/usr/bin/env bash
# Pre-commit hook: same checks as .github/workflows/lint.yml
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

poetry run ruff check .
poetry run ruff format --check .
poetry run black --check .
