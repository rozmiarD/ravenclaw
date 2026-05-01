# Proof-of-Value Scorecard v0.1

The Proof-of-Value Scorecard is a public-safe, machine-readable benchmark checklist for Ravenclaw's current proof-of-value layer.

It turns the dimensions described in `PROOF_OF_VALUE.md` into checks over concrete public evidence paths.

## Artifact identity

- `artifact_type`: `proof_of_value_scorecard`
- `schema_version`: `v0.1`
- `schema_ref`: `schemas/proof_of_value_scorecard.v0.1.schema.json`
- producer: `scripts/build_proof_of_value_scorecard.py`

## Usage

From the repository root or an assembled public snapshot:

```bash
python scripts/build_proof_of_value_scorecard.py . --check
python scripts/build_proof_of_value_scorecard.py . --format markdown --check
```

Expected result: `summary.status: passed` with all dimensions backed by present public evidence paths.

## Dimensions

- Scope fidelity
- Policy decision clarity
- Execution spec accountability
- Dry-run/evidence separation
- Replayability
- Snapshot completeness
- Non-claim preservation

## Boundaries

The scorecard is local/public-safe only. It does **not** claim:

- live target execution;
- live vulnerability evidence;
- production readiness;
- protocol adapter completeness;
- superiority of real-world outcomes by itself.
