#!/usr/bin/env bash
# Simple RAVEN-CLAW monitoring daemon
# Logs basic system health (uptime, disk, memory) plus current task context
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_WORKSPACE="$(cd -- "$SCRIPT_DIR/.." && pwd)"
WORKSPACE="${RAVENCLAW_WORKSPACE:-${WORKSPACE:-$DEFAULT_WORKSPACE}}"
LOG_DIR="$WORKSPACE/logs"
CONTEXT_FILE="${RAVENCLAW_CONTEXT_SUMMARY_PATH:-$WORKSPACE/reports/cache/context_summary.json}"
LEGACY_CONTEXT_FILE="$WORKSPACE/engine/context_summary.json"
OPERATOR="${RAVENCLAW_OPERATOR:-operatorX}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/monitor.log"
while true; do
  echo "--- $(date '+%Y-%m-%d %H:%M:%S') ---" >> "$LOG_FILE"
  echo "Operator: $OPERATOR" >> "$LOG_FILE"
  if [ ! -f "$CONTEXT_FILE" ] && [ -f "$LEGACY_CONTEXT_FILE" ]; then
    CONTEXT_FILE="$LEGACY_CONTEXT_FILE"
  fi
  if [ -f "$CONTEXT_FILE" ]; then
    CURRENT_TASK=$(WORKSPACE="$WORKSPACE" RAVENCLAW_CONTEXT_SUMMARY_PATH="$CONTEXT_FILE" python3 - <<'PY'
import json, pathlib, os
workspace = pathlib.Path(os.environ.get("WORKSPACE") or os.getcwd())
preferred = pathlib.Path(os.environ.get("RAVENCLAW_CONTEXT_SUMMARY_PATH", str(workspace / "reports" / "cache" / "context_summary.json")))
legacy = workspace / "engine" / "context_summary.json"
path = preferred if preferred.exists() else legacy
try:
    data = json.loads(path.read_text())
    if data:
        last = data[-1]
        objective = last.get("objective") or "n/a"
        target = last.get("target") or "n/a"
        owner_override = last.get("owner_override")
        status = last.get("status") or last.get("returncode")
        print(f"Current task: {objective} @ {target} | status={status} | owner_override={owner_override}")
    else:
        print("Current task: none")
except Exception as e:
    print(f"Current task: unavailable ({e})")
PY
)
    echo "$CURRENT_TASK" >> "$LOG_FILE"
  else
    echo "Current task: none" >> "$LOG_FILE"
  fi
  echo "Uptime:" >> "$LOG_FILE"
  uptime >> "$LOG_FILE"
  echo "Disk usage:" >> "$LOG_FILE"
  df -h >> "$LOG_FILE"
  echo "Memory usage:" >> "$LOG_FILE"
  free -h >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
  sleep 300  # 5 minutes
 done
