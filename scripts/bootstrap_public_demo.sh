#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-install}"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
LOGDASH_PORT="${LOGDASH_PORT:-9091}"
DEMO_OUTPUT_DIR="${DEMO_OUTPUT_DIR:-demo-output}"
INSTALL_STAMP="$VENV_DIR/.ravenclaw-public-demo-install-key"

ensure_venv() {
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
}

install_key() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import hashlib
root = Path.cwd()
parts = []
for rel in ['pyproject.toml', 'logdash/requirements.txt']:
    p = root / rel
    parts.append(rel)
    parts.append(p.read_text(encoding='utf-8') if p.exists() else '')
print(hashlib.sha256('\n'.join(parts).encode('utf-8')).hexdigest())
PY
}

install_deps() {
  ensure_venv
  local key current_key
  current_key="$(install_key)"
  if [[ -f "$INSTALL_STAMP" ]] && [[ "$(cat "$INSTALL_STAMP")" == "$current_key" ]]; then
    return 0
  fi
  python -m pip install --upgrade pip
  python -m pip install -e '.[dev]'
  printf '%s' "$current_key" > "$INSTALL_STAMP"
}

run_demo() {
  ensure_venv
  "$ROOT_DIR/bin/demo" "$@"
}

run_logdash() {
  ensure_venv
  cd "$ROOT_DIR/logdash"
  python app.py --port "$LOGDASH_PORT"
}

run_bundle() {
  ensure_venv
  "$ROOT_DIR/bin/demo-bundle" --output-dir "$DEMO_OUTPUT_DIR" "$@"
}

run_doctor() {
  ensure_venv
  local install_status="missing"
  local key="$(install_key)"
  if [[ -f "$INSTALL_STAMP" ]] && [[ "$(cat "$INSTALL_STAMP")" == "$key" ]]; then
    install_status="ready"
  fi
  local install_validation
  install_validation="$(python "$ROOT_DIR/scripts/validate_public_install.py" --dev --json)"
  INSTALL_VALIDATION="$install_validation" python - <<PY
import json
import os
from pathlib import Path
print(json.dumps({
  'mode': 'doctor',
  'repo_root': str(Path(r'''$ROOT_DIR''')),
  'venv_dir': str(Path(r'''$VENV_DIR''')),
  'logdash_port': int(r'''$LOGDASH_PORT'''),
  'demo_output_dir': str(Path(r'''$ROOT_DIR''') / r'''$DEMO_OUTPUT_DIR'''),
  'install_status': r'''$install_status''',
  'install_validation': json.loads(os.environ['INSTALL_VALIDATION']),
  'runtime_mode': 'demo'
}, ensure_ascii=False, indent=2))
PY
}

run_smoke() {
  ensure_venv
  "$ROOT_DIR/bin/demo" --print-only
  "$ROOT_DIR/bin/demo-bundle" --output-dir "$DEMO_OUTPUT_DIR" --print-summary >/tmp/ravenclaw-public-demo-bundle-summary.json
  python - <<'PY'
import json
from pathlib import Path
obj = json.loads(Path('/tmp/ravenclaw-public-demo-bundle-summary.json').read_text())
assert obj['runtime_mode'] == 'demo'
assert obj['integration_adapters']['execution']['mode'] == 'mock'
assert obj['engine_status'] == 'dry-run'
print('public_demo_smoke_ok')
PY
}

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap_public_demo.sh <mode>

Modes:
  install      Create/update venv and install public demo dependencies when needed
  doctor       Print compact readiness info for the public demo path
  demo         Run the official public-safe demo entrypoint
  demo-print   Print the official demo commands without executing them
  bundle       Generate reusable demo artifacts into DEMO_OUTPUT_DIR (default: demo-output)
  logdash      Start Logdash on LOGDASH_PORT (default: 9091)
  smoke        Run a bounded public demo smoke check
EOF
}

case "$MODE" in
  install)
    install_deps
    ;;
  doctor)
    install_deps >&2
    run_doctor
    ;;
  demo)
    install_deps
    run_demo
    ;;
  demo-print)
    install_deps
    run_demo --print-only
    ;;
  bundle)
    install_deps
    run_bundle
    ;;
  logdash)
    install_deps
    run_logdash
    ;;
  smoke)
    install_deps
    run_smoke
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "unknown mode: $MODE" >&2
    usage >&2
    exit 2
    ;;
esac
