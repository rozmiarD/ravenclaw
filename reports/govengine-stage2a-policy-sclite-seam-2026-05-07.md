# GovEngine Stage 2A Policy/SCLite Seam Report — 2026-05-07

Status: implemented locally on `ravenclaw/govengine-plan-refresh`; no push performed.
Base before this wave: `072e5c8 feat: add GovEngine context seam`.

## Implemented scope

- Added `govengine.policy` API seam:
  - `govengine/policy/__init__.py`
  - `govengine/policy/core.py`
- Converted `engine/policy_core.py` into a compatibility wrapper re-exporting `govengine.policy.core`.
- Added `govengine/sclite_adapter.py` as the SCLite/Ravenclaw lifecycle adapter seam.
- Converted `engine/scl_ravenclaw_adapter.py` into a compatibility wrapper re-exporting `govengine.sclite_adapter`.
- Updated `pyproject.toml` packages to include `govengine.policy`.
- Added equivalence tests for old `engine/*` imports and new `govengine.*` imports.

## Boundary notes

This is still package-in-place extraction. Some code in the new GovEngine seams intentionally bootstraps the Ravenclaw `engine/` path because adjacent dependencies (`tool_registry`, `policy_gateway`, `execution_contracts`) have not yet been moved. That coupling is explicit and should be reduced in later Stage 2 waves.

No wholesale executor move, no Logdash move, no external GovEngine repo, and no protocol adapter work.

## Validation

Focused gate:

```bash
/tmp/ravenclaw-docs-venv/bin/python -m pytest -q \
  engine/tests/test_govengine_policy_seam.py \
  engine/tests/test_security_contract_layer_wrapper.py \
  engine/tests/test_policy_core_runtime_tool_policy.py \
  engine/tests/test_policy_core_approved_spec.py \
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

Stage 2B should reduce the remaining policy/SCLite seam coupling by moving or wrapping the immediate dependencies that currently keep `govengine.policy.core` and `govengine.sclite_adapter` tied to Ravenclaw engine path bootstrap:

1. tool registry provider seam;
2. policy gateway normalization seam;
3. execution contract redaction seam;
4. then reconsider executor movement as a separate bounded wave.
