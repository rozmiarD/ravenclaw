# Public Validation Surface Index v0.1

The Public Validation Surface Index is a reader-facing, public-safe contract for the local validation commands Ravenclaw exposes.

It answers three questions for each surface:

1. What command should a public reader run?
2. What does that command validate?
3. What does that command explicitly **not** claim?

## Artifact identity

- `artifact_type`: `public_validation_surface_index`
- `schema_version`: `v0.1`
- `schema_ref`: `schemas/public_validation_surface_index.v0.1.schema.json`
- producer: `scripts/list_public_validation_surfaces.py --format json --check`

## Boundaries

Every indexed surface is constrained as:

- `public_safe: true`
- `dry_run_or_local_only: true`
- `live_target_execution: false`
- `protocol_adapter_work: false`

The index is a navigation and release-prep aid. It does **not** authorize publication, live target testing, protocol adapter work, or production deployment claims.

## Required surface fields

Each surface contains:

- `id` — stable check identifier.
- `title` — reader-facing name.
- `command` — command string to run from the repository root unless stated otherwise.
- `paths` — files or directories the surface depends on.
- `claim` — what passing or inspecting this surface supports.
- `non_claim` — what it deliberately does not prove.
- `boundaries` — public-safety limits.
- `missing_paths` — paths absent from the current tree; `--check` fails when any are present.

## Why this is schema-backed

The index is intentionally schema-backed so the public validation map cannot silently drift into an unbounded marketing list. Adding or changing a surface must preserve explicit claims, non-claims, public-safety boundaries, and path existence checks.
