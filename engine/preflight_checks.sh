#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${RAVENCLAW_WORKSPACE:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[preflight] checking feature flag consistency..."
"$PYTHON_BIN" "$ROOT/engine/verify_feature_flags.py"

echo "[preflight] checking changelog freshness..."
"$PYTHON_BIN" "$ROOT/engine/changelog_guard.py"

echo "[preflight] checking python syntax (core files)..."
"$PYTHON_BIN" -m py_compile \
  "$ROOT/engine/feature_flags.py" \
  "$ROOT/engine/run_pipeline.py" \
  "$ROOT/engine/auto_campaign.py" \
  "$ROOT/logdash/app.py"

echo "[preflight] all checks passed"
