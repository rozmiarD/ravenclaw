# Public Snapshot Manifest v0.1

The Public Snapshot Manifest maps Ravenclaw's public validation surfaces to the files present in an assembled public snapshot.

It is intended for reviewer navigation and release-prep sanity checks: if documentation says a public-safe validation surface exists, the manifest shows the concrete snapshot paths that support it and whether any are missing.

## Artifact identity

- `artifact_type`: `public_snapshot_manifest`
- `schema_version`: `v0.1`
- `schema_ref`: `schemas/public_snapshot_manifest.v0.1.schema.json`
- producer: `scripts/build_public_snapshot_manifest.py`

## Boundaries

The manifest inherits validation-surface boundaries:

- `public_safe: true`
- `dry_run_or_local_only: true`
- `live_target_execution: false`
- `protocol_adapter_work: false`

It does **not** authorize publication, live target testing, protocol adapter work, or production-readiness claims.

## Required checks

Run against an assembled public snapshot:

```bash
python scripts/build_public_snapshot_manifest.py . --check
python scripts/build_public_snapshot_manifest.py . --format reviewer-report --check
```

Expected result: JSON with `artifact_type: public_snapshot_manifest`, `schema_version: v0.1`, and `summary.missing_path_count: 0`.

## Relationship to the validation surface index

The manifest is derived from `scripts/list_public_validation_surfaces.py`. The index describes the validation surfaces; the manifest confirms their referenced paths are present in a specific snapshot tree.

## Reviewer report format

Use `--format reviewer-report` to render the manifest as a markdown review artifact with a summary, surface/path table, and explicit non-authorization boundaries.
