# Reviewer Validation Guide Wave — 2026-05-01

## Scope

Bounded local/public-safe continuation after the Public Snapshot Manifest push and green GitHub Actions run.

Goal: give public reviewers a short validation path that links `VALIDATION.md`, `QUALITY_SIGNALS.md`, the Public Snapshot Manifest, and Security Contract receipt/non-claims.

## Changes

- Added `REVIEWER_VALIDATION_GUIDE.md`.
- Included the guide in assembled public snapshots.
- Added guide coverage to focused validation through `tests/test_reviewer_validation_guide.py` and `scripts/run_security_contract_validation.py`.
- Updated `DOCS_MAP.md`, `VALIDATION.md`, `QUALITY_SIGNALS.md`, and `CHANGELOG.md`.
- Extended snapshot inclusion tests to require the guide.

## Validation

Passed:

```text
python -m pytest -q tests/test_reviewer_validation_guide.py tests/test_security_contract_validation_runner.py tests/test_public_snapshot_security_contract_fixtures.py
SNAP=$(mktemp -d /tmp/ravenclaw-reviewer-guide.XXXXXX); scripts/assemble_public_snapshot.sh "$SNAP" >/dev/null; test -f "$SNAP/REVIEWER_VALIDATION_GUIDE.md"; cd "$SNAP"; PYTHONDONTWRITEBYTECODE=1 python scripts/build_public_snapshot_manifest.py . --check
python scripts/run_security_contract_validation.py --include-pytest
git diff --check
```

Consolidated validation returned `status=passed`, `summary={failed: 0, passed: 10, total: 10}`.

The assembled snapshot manifest remained clean with `surface_count=10`, `path_count=25`, `missing_path_count=0`.

## Review

This is a reviewer-experience and public-readiness improvement, not a runtime feature. It reduces reviewer friction by making the validation path explicit and preserving non-claims in one short guide.

## Remaining work

- Run full parity receipt before any public push.
- Push only with explicit operator approval.
- Next roadmap candidate after publish: add a small generated markdown mode for the manifest or keep moving toward proof-of-value/benchmark framing once validation discoverability is stable.
