#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/public-snapshot}"

rm -rf "$OUT"
mkdir -p "$OUT"

copy_path() {
  local rel="$1"
  if [ -e "$ROOT/$rel" ]; then
    mkdir -p "$OUT/$(dirname "$rel")"
    cp -R "$ROOT/$rel" "$OUT/$rel"
  fi
}

prune_snapshot_noise() {
  find "$OUT" -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' -o -name 'tmp' \) -prune -print0 | xargs -0r rm -rf
  find "$OUT" -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.pyd' -o -name '*.log' -o -name 'logs.db' -o -name 'logdash.out' \) -delete
  rm -rf "$OUT/engine/tmp"
  rm -f "$OUT/engine/public_targets_plan.json"
  rm -f "$OUT/engine/context_summary.json"
  rm -f "$OUT/engine/pipeline_config.json"
  rm -rf "$OUT/engine/system_memory"
  rm -rf "$OUT/logdash/.venv"
  rm -f "$OUT/logdash/agents_config.json"
  rm -f "$OUT/out.json"
  rm -rf "$OUT/logs"
  rm -rf "$OUT/reports"
  rm -rf "$OUT/memory"
  rm -rf "$OUT/pending"
  rm -rf "$OUT/tmp"
  rm -rf "$OUT/state"
  rm -rf "$OUT/workspace-brain"
}

# Core code
copy_path engine
copy_path govengine
copy_path logdash
copy_path tests
copy_path references
copy_path schemas
copy_path .devcontainer
copy_path .github

# Core docs / metadata
for f in \
  README.md \
  INSTALL.md \
  ENVIRONMENT_SUPPORT.md \
  DEMO.md \
  VALIDATION.md \
  REVIEWER_VALIDATION_GUIDE.md \
  PROOF_OF_VALUE.md \
  QUALITY_SIGNALS.md \
  PUBLIC_STATUS.md \
  AUDIENCE.md \
  DOCS_MAP.md \
  PUBLISHING.md \
  ARCHITECTURE_OVERVIEW.md \
  WHY_RAVENCLAW.md \
  ARCHITECTURE.md \
  STATE_FILES.md \
  VERSION_ROADMAP.md \
  OPEN_SOURCE_1_0_PLAN.md \
  SECURITY_CONTRACT_LAYER.md \
  REPLAYABLE_TRUTH_RUNTIME.md \
  SECURITY.md \
  CONTRIBUTING.md \
  LICENSE \
  CODE_OF_CONDUCT.md \
  pyproject.toml \
  policy.yaml \
  whitelist.yaml \
  proxy.yaml \
  budgets.yaml \
  campaign.md \
  CHANGELOG.md \
  compose.demo.yaml
 do
  copy_path "$f"
 done

# Public snapshot scaffolding
mkdir -p "$OUT/examples/campaign_registry"
mkdir -p "$OUT/examples/runtime_state"
mkdir -p "$OUT/scripts"
copy_path bin/demo
copy_path bin/demo-bundle
copy_path scripts/assemble_public_snapshot.sh
copy_path scripts/bootstrap_public_demo.sh
cp "$ROOT/scripts/prepare_public_examples.md" "$OUT/scripts/prepare_public_examples.md"
copy_path scripts/audit_public_snapshot_residue.py
copy_path scripts/validate_security_contract_fixtures.py
copy_path scripts/run_security_contract_validation.py
copy_path scripts/validate_replayable_truth_fixture.py
copy_path scripts/validate_scope_fidelity_fixtures.py
copy_path scripts/build_scope_fidelity_report.py
copy_path scripts/run_pytest_slice.py
copy_path scripts/list_public_validation_surfaces.py
copy_path scripts/build_public_snapshot_manifest.py
copy_path scripts/build_proof_of_value_scorecard.py
copy_path scripts/validate_proof_of_value_scorecard.py
copy_path examples/security-contract-proof
copy_path examples/contract-lifecycle-v0.2
copy_path examples/replayable-truth-runtime
copy_path examples/scope-fidelity-report
copy_path examples/proof-of-value-scorecard

cat > "$OUT/examples/campaign_registry/example-registry-entry.md" <<'EOF'
# Example campaign registry entry

This placeholder stands in for a future sanitized campaign-registry example.
Do not replace it with a live registry export without review/redaction.
EOF

cat > "$OUT/examples/runtime_state/example-runtime-snapshot.json" <<'EOF'
{
  "ok": true,
  "source": "example_redacted",
  "campaign": {
    "campaign_key": "example-campaign",
    "state": "idle"
  },
  "notes": [
    "This is a redacted example artifact for public documentation.",
    "Do not publish live runtime/control-plane state files."
  ]
}
EOF

prune_snapshot_noise

cat > "$OUT/PUBLIC_SNAPSHOT_NOTICE.md" <<'EOF'
This directory is an assembled public snapshot scaffold.

It intentionally excludes mixed local/internal areas such as:
- reports/ (except prepared examples added later)
- memory/
- logs/
- pending/
- tmp/
- state/
- workspace/operator-specific bootstrap files

It also prunes obvious snapshot noise such as:
- engine/tmp/
- legacy generated engine JSON mirrors like `engine/public_targets_plan.json` and `engine/context_summary.json`
- internal runtime role guidance under `engine/system_memory/`
- embedded virtualenvs like `logdash/.venv`
- internal model wiring like `logdash/agents_config.json`
- __pycache__/
- test/tool caches
- *.log, `logdash.out`, and `logs.db` artifacts

`auth-harness/` is not included by default in this scaffold and should only be considered for publication after separate secret-flow review.

Before publishing, review the assembled snapshot and populate examples/ with intentionally prepared redacted samples.
EOF

echo "Assembled public snapshot scaffold at: $OUT"
echo "Next: review scaffold contents and curated examples before any public push."
