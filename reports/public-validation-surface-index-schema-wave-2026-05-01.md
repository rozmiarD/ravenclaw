# Public Validation Surface Index Schema Wave — 2026-05-01

## Scope

Bounded local/public-safe hardening wave for the public validation surface index introduced after the GitHub Actions parity validation work.

## Changes

- Added `schemas/public_validation_surface_index.v0.1.schema.json`.
- Added `references/public-validation-surface-index-v0.1.md`.
- Made `scripts/list_public_validation_surfaces.py` emit `schema_ref` and validate the generated JSON through `engine/security_contract_layer.py` before output.
- Added regression coverage for schema acceptance and rejection of unsafe live-target boundary drift.
- Updated `VALIDATION.md`, `SECURITY_CONTRACT_LAYER.md`, and `CHANGELOG.md`.

## Validation

Passed:

```text
python scripts/list_public_validation_surfaces.py --format json --check
python -m pytest -q tests/test_public_validation_surface_index.py tests/test_security_contract_validation_runner.py engine/tests/test_security_contract_layer_schemas.py
python scripts/run_security_contract_validation.py --include-pytest
git diff --check
python -m pytest -q tests/test_public_validation_surface_index.py tests/test_security_contract_validation_runner.py tests/test_public_snapshot_security_contract_fixtures.py
git diff --check
```

`run_security_contract_validation.py --include-pytest` returned `status=passed`, `summary={failed: 0, passed: 9, total: 9}`.

## Review

This is a contract-hardening step, not a new runtime capability. It improves public-reader and release-prep reliability by preventing the validation index from drifting into unbounded claims or unsafe boundaries.

## Remaining work

Next bounded candidates:

1. Re-run the full GitHub Actions parity receipt from this exact tree.
2. Add a public snapshot manifest/index that cross-links validation surfaces to snapshot-included files.
3. Consolidate the current unpublished stack into a clean publish tree only if the operator explicitly asks to publish/push.
