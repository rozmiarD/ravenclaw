# GovEngine Stage 2D Command-Shape Seam Report — 2026-05-07

Status: implemented locally on `ravenclaw/govengine-plan-refresh`; no push performed.
Base before this wave: `bff98dc feat: extract GovEngine execution gate helpers`.
Persistent worktree: `/home/probo/.openclaw/worktrees/ravenclaw-govengine-plan`.

## Implemented scope

- Added `govengine.execution.command_shape` for pure command-shape helpers:
  - `normalize_argv(...)`
  - `extract_hosts_from_text(...)`
  - `arg_target_observations(...)`
  - `enforce_target_semantics(...)`
  - `enforce_scope(...)`
- Updated `engine/executor.py` to delegate its argv normalization, target observation, target-kind checks, and scope enforcement helpers to the GovEngine seam.
- Kept host-specific policy sources injected from Ravenclaw:
  - allowed tools provider remains Ravenclaw/GovEngine policy layer call site;
  - restricted-pattern checker supplied by policy layer;
  - `extract_host_from_url` and `host_in_scope` supplied by Ravenclaw campaign utilities;
  - tool catalog supplied by Ravenclaw/GovEngine registry.
- Added focused equivalence tests for engine wrappers vs GovEngine command-shape helpers.

## Explicit non-goals held

- No subprocess execution moved.
- No artifact writing moved.
- No runtime command runner moved.
- No Logdash move.
- No external GovEngine repo.
- No public push.

## Validation

Focused gate:

```bash
/tmp/ravenclaw-docs-venv/bin/python -m pytest -q \
  engine/tests/test_govengine_command_shape_seam.py \
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

Stage 2E can now introduce a `govengine.execution.runner` interface and move only dry-run planning/result assembly first, or continue reducing utility coupling by extracting `campaign_utils` host/scope helpers behind a GovEngine scope port. Recommendation: add the scope port before moving subprocess execution.
