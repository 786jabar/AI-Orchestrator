#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/services/orchestrator:${PYTHONPATH:-}"
mkdir -p data/projects data/sandboxes
exec python3 -m uvicorn app.main:app --app-dir "$ROOT/services/orchestrator" --host 0.0.0.0 --port 8000 --reload --reload-dir "$ROOT/services/orchestrator"
