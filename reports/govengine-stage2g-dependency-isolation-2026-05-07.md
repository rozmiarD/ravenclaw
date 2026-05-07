# GovEngine Stage 2G Dependency Isolation Report — 2026-05-07

Status: implemented locally on `ravenclaw/govengine-plan-refresh`; no push performed.
Base before this wave: `96cdf43 docs: add GovEngine branch readiness review`.
Persistent worktree: `/home/probo/.openclaw/worktrees/ravenclaw-govengine-plan`.

## Implemented scope

- Moved action/compiler support into GovEngine package-in-place modules:
  - `govengine.action_schema`
  - `govengine.action_validators`
  - `govengine.action_compiler`
  - `govengine.capability_recipes`
  - `govengine.semantic_loss_policy`
- Added package-local GovEngine data files:
  - `govengine/capability_recipes.yaml`
  - `govengine/tool_registry.yaml`
- Converted Ravenclaw `engine/action_*`, `engine/capability_recipes.py`, and `engine/semantic_loss_policy.py` to compatibility aliases.
- Extended `govengine.state_store` with neutral JSON state helpers, replacing `json_state_io` dependency in GovEngine tool registry.
- Extended `govengine.scope` with neutral host extraction, scope-domain loading, and in-scope checks, replacing `campaign_utils` imports in GovEngine modules.
- Updated `govengine.policy.gateway`, `govengine.contracts.execution`, and `govengine.tool_registry` to use GovEngine-local dependencies.
- Added package-data metadata for GovEngine YAML files.
- Added standalone copy/import tests proving GovEngine public surface imports without Ravenclaw `engine/`.

## Dependency blockers addressed

Previous standalone import blockers:

- `json_state_io` — addressed by `govengine.state_store` helpers.
- `campaign_utils` — addressed by `govengine.scope` helpers/port.
- `action_schema` — moved to `govengine.action_schema`.
- `action_validators` — moved to `govengine.action_validators`.
- `action_compiler` — moved to `govengine.action_compiler`.
- Transitive `capability_recipes` / `semantic_loss_policy` — moved to GovEngine package modules.

A direct grep for the prior Ravenclaw helper imports in `govengine/**/*.py` returned no hits.

## Standalone import proof

Focused test copies only `govengine/` into a temporary directory and imports:

- `govengine`
- `govengine.context`
- `govengine.scope`
- `govengine.state_store`
- `govengine.action_schema`
- `govengine.action_validators`
- `govengine.semantic_loss_policy`
- `govengine.capability_recipes`
- `govengine.action_compiler`
- `govengine.tool_registry`
- `govengine.contracts.execution`
- `govengine.policy.core`
- `govengine.policy.gateway`
- `govengine.execution.approved_spec`
- `govengine.execution.command_shape`
- `govengine.execution.runner`
- `govengine.execution.ticket_gate`

Result: `standalone_imports_ok:17`.

## Explicit non-goals held

- No subprocess execution moved.
- No artifact writing moved.
- No Logdash move.
- No external repo created or pushed.
- No live target testing.

## Validation

Focused gate:

```bash
/tmp/ravenclaw-docs-venv/bin/python -m pytest -q \
  engine/tests/test_govengine_dependency_isolation.py \
  engine/tests/test_govengine_stage2b_seams.py \
  engine/tests/test_govengine_policy_seam.py \
  engine/tests/test_govengine_command_shape_seam.py \
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

Proceed to Stage 2H repo scaffold rehearsal:

1. create a temp standalone GovEngine repo scaffold;
2. copy `govengine/`, minimal package metadata, license, and focused tests;
3. install editable in a clean venv;
4. run standalone imports and focused tests;
5. report blockers without pushing.
