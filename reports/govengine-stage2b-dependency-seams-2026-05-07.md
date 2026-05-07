# GovEngine Stage 2B Dependency Seam Report — 2026-05-07

Status: implemented locally on `ravenclaw/govengine-plan-refresh`; no push performed.
Base before this wave: `921b2ea feat: expose GovEngine policy and SCLite seams`.

## Implemented scope

- Added `govengine.tool_registry` seam.
- Added `govengine.policy.gateway` seam.
- Added `govengine.contracts.execution` seam.
- Converted these Ravenclaw modules to compatibility module aliases:
  - `engine/tool_registry.py`
  - `engine/policy_gateway.py`
  - `engine/execution_contracts.py`
- Tightened existing seams:
  - `govengine.policy.core` imports `govengine.tool_registry` instead of engine `tool_registry`.
  - `govengine.sclite_adapter` imports `govengine.policy.gateway` and `govengine.contracts.execution` instead of engine wrappers.
- Added compatibility/equivalence tests covering old module names and new GovEngine modules.
- Preserved monkeypatch compatibility for module-level globals by aliasing compatibility modules through `sys.modules[__name__]` instead of plain star re-export wrappers.

## Boundary notes

This reduces the direct dependencies identified after Stage 2A:

- `tool_registry` moved behind `govengine.tool_registry`.
- `policy_gateway.normalize_policy_decision_v0` moved behind `govengine.policy.gateway`.
- `execution_contracts.redact_prepared_execution_spec_for_auditor` moved behind `govengine.contracts.execution`.

Remaining Ravenclaw-engine bootstrap dependencies are still explicit in these GovEngine seams because adjacent modules are not yet extracted:

- `json_state_io`
- `campaign_utils`
- `action_compiler`
- `action_validators`
- `action_schema`
- `paths`-style runtime conventions are mostly reduced for registry paths but still present indirectly through helper modules.

No executor move, no Logdash move, no external GovEngine repo, and no protocol adapter work.

## Validation

Focused gate:

```bash
/tmp/ravenclaw-docs-venv/bin/python -m pytest -q \
  engine/tests/test_govengine_stage2b_seams.py \
  engine/tests/test_tool_registry.py \
  engine/tests/test_policy_gateway_semantic_actions.py \
  engine/tests/test_execution_contracts.py \
  engine/tests/test_govengine_policy_seam.py
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

Stage 2C should choose one of two routes:

1. **Contracts/support route**: extract the remaining non-executor helper dependencies used by policy/contracts (`campaign_utils`, `action_schema`, validators, compiler helpers) into GovEngine seams, preserving wrappers.
2. **Executor prep route**: introduce `govengine.execution` package and move only pure ticket-gate/spec-validation helpers first, leaving command execution in `engine/executor.py` until the next review.

Recommendation: take route 2 only if the goal is to prepare executor movement now; otherwise route 1 reduces coupling more cleanly.
