#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data/sandboxes
exec python3 -m uvicorn app.main:app --app-dir "$ROOT/services/sandbox" --host 0.0.0.0 --port 8001 --reload --reload-dir "$ROOT/services/sandbox"
