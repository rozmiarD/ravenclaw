# Public Snapshot Manifest Wave — 2026-05-01

## Scope

Bounded local/public-safe continuation after the `be8c4c0` public push and green GitHub Actions run.

Goal: make the assembled public snapshot more auditable by mapping public validation surfaces to the concrete files present in a snapshot tree.

## Changes

- Added `scripts/build_public_snapshot_manifest.py`.
- Added `schemas/public_snapshot_manifest.v0.1.schema.json`.
- Added `references/public-snapshot-manifest-v0.1.md`.
- Added the manifest script to public snapshot assembly.
- Added `public_snapshot_manifest` to the public validation surface index.
- Added `snapshot_manifest` to the consolidated Security Contract validation runner.
- Added focused regression coverage for manifest generation, schema validation, missing-path failure, unsafe-boundary rejection, and snapshot inclusion.
- Updated `VALIDATION.md`, `PUBLISHING.md`, `SECURITY_CONTRACT_LAYER.md`, and `CHANGELOG.md`.

## Validation

Passed:

```text
python -m pytest -q tests/test_public_snapshot_manifest.py tests/test_public_validation_surface_index.py tests/test_security_contract_validation_runner.py tests/test_public_snapshot_security_contract_fixtures.py tests/test_public_snapshot_residue_audit.py
SNAP=$(mktemp -d /tmp/ravenclaw-manifest-snapshot.XXXXXX); scripts/assemble_public_snapshot.sh "$SNAP" >/dev/null; cd "$SNAP"; PYTHONDONTWRITEBYTECODE=1 python scripts/build_public_snapshot_manifest.py . --check
python scripts/run_security_contract_validation.py --include-pytest
git diff --check
```

Consolidated validation returned `status=passed`, `summary={failed: 0, passed: 10, total: 10}`.

The standalone assembled snapshot manifest returned `artifact_type=public_snapshot_manifest`, `surface_count=10`, `path_count=25`, `missing_path_count=0`.

## Review

This is a public-readiness/auditability improvement, not a runtime feature. It makes validation claims easier to verify inside an assembled snapshot and catches missing files before publication or review.

## Remaining work

- Run full GitHub Actions parity receipt before any push.
- If green, push only with explicit operator approval.
- Next feature wave candidate: public snapshot manifest markdown artifact generation or lightweight reviewer guide linking manifest sections to `VALIDATION.md` and `QUALITY_SIGNALS.md`.
