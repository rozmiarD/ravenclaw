# GovEngine Stage 2F Runner Dry-Run Seam Report — 2026-05-07

Status: implemented locally on `ravenclaw/govengine-plan-refresh`; no push performed.
Base before this wave: `12f70af feat: add GovEngine scope port`.
Persistent worktree: `/home/probo/.openclaw/worktrees/ravenclaw-govengine-plan`.

## Implemented scope

- Added `govengine.execution.runner` for non-executing runner result helpers:
  - `approved_spec_compiled_action(...)`
  - `dry_run_result(...)`
  - `approved_spec_dry_run_result(...)`
  - `legacy_action_spec_dry_run_result(...)`
- Updated `engine/executor.py` to delegate dry-run result assembly for:
  - approved execution specs;
  - legacy direct action specs.
- Kept all command execution in Ravenclaw executor.
- Added focused tests proving runner dry-run helpers match current executor result shapes.

## Explicit non-goals held

- No subprocess execution moved.
- No live command runner moved.
- No artifact writing moved.
- No Logdash move.
- No external GovEngine repo.
- No public push.

## Validation

Focused gate:

```bash
/tmp/ravenclaw-docs-venv/bin/python -m pytest -q \
  engine/tests/test_govengine_runner_seam.py \
  engine/tests/test_executor_v2.py
```

Result: passed.

Full gate:

```bash
/tmp/ravenclaw-docs-venv/bin/python scripts/run_security_contract_validation.py --include-pytest --format markdown
for slice in contracts_policy auto_campaign runtime_core runtime_runner logdash misc_public; do
  PYTHONDONTWRITEBYTECODE=1 /tmp/ravenclaw-docs-venv/bin/python scripts/run_pytest_slice.py "$slice"
done
/tmp/ravenclaw-docs-venv/bin/sclite verify-lifecycle examples/contract-lifecycle-v0.2/artifact_chain_manifest.json
```

Result:

- Security Contract validation receipt: passed.
- Pytest slice matrix: passed for all requested slices.
- SCLite lifecycle verification: `lifecycle_ok:6:ddb006900727142b8095e918a93f3dba484d3820b66fff813c169c3b16c6b295`.

## Recommended next wave

Stage 2G should either:

1. introduce an execution backend protocol/result object for subprocess-backed execution while keeping Ravenclaw's concrete subprocess runner; or
2. pause and run a publication-readiness review of the accumulated GovEngine branch before moving live execution mechanics.

Recommendation: pause for review before moving subprocess execution.
