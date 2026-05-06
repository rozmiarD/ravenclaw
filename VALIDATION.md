# VALIDATION.md

This file tells a public reader how to validate the current Ravenclaw repository without assuming a full live operator environment. For a shorter reviewer-oriented path, see `REVIEWER_VALIDATION_GUIDE.md`.

## Fast public validation path

After following `INSTALL.md`, run:

```bash
pytest -q
```

This is the primary repo-wide validation command exposed publicly today.

## Public validation surface index

To list the public-safe validation entry points and what each one does and does not prove, run:

```bash
python scripts/list_public_validation_surfaces.py
python scripts/list_public_validation_surfaces.py --format json --check
```

This emits a schema-backed `public_validation_surface_index` artifact (`schemas/public_validation_surface_index.v0.1.schema.json`; see `references/public-validation-surface-index-v0.1.md`). It is a navigation aid for readers and release prep. It does not run live targets and does not replace the actual validation commands listed below.

For an assembled public snapshot, map those validation surfaces to concrete snapshot files with:

```bash
python scripts/build_public_snapshot_manifest.py . --check
python scripts/build_public_snapshot_manifest.py . --format reviewer-report --check
```

This emits a schema-backed `public_snapshot_manifest` artifact (`schemas/public_snapshot_manifest.v0.1.schema.json`; see `references/public-snapshot-manifest-v0.1.md`) and fails if any validation-surface path is missing from the snapshot. The `reviewer-report` format renders the same checks as a ready-to-read markdown review artifact.

## Stable sliced validation path

For CI or lower-wall-time local validation, use the slice runner:

```bash
python scripts/run_pytest_slice.py --list
python scripts/run_pytest_slice.py contracts_policy
python scripts/run_pytest_slice.py runtime_runner
```

The slices are coverage-preserving partitions of the current suite, intended to keep broad validation reproducible even when one giant batch is more fragile than the underlying tests.

## What this validates

Running the suite exercises public-visible correctness signals across areas such as:
- planner and runtime contracts
- policy and approval behavior
- execution contract shaping
- Logdash control and state projection behavior
- runtime recovery truth
- evaluation and replay semantics

## Focused validation reads

If you want to inspect representative trust anchors before or after running tests, start here:
- `.github/workflows/pytest.yml`
- `scripts/run_pytest_slice.py`
- `tests/test_logdash_smoke.py`
- `tests/test_logdash_operator_truth_contracts.py`
- `engine/tests/test_execution_contracts.py`
- `engine/tests/test_runtime_plan_service_contracts.py`
- `references/runtime-task-contract-v2.md`
- `references/logdash-operator-truth-contracts.md`

## Demo plus validation

A useful public review path is:
1. follow `DEMO.md`
2. run `pytest -q`
3. inspect `QUALITY_SIGNALS.md`

That gives a reader:
- a safe demo path
- a repo-wide automated validation path
- a short explanation of what the proof surfaces do and do not mean

## Security Contract proof fixture validation

To validate the committed public-safe Security Contract proof fixture directly, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_security_contract_fixtures.py examples/security-contract-proof
```

Expected result:

```text
security_contract_fixtures_ok:...
```

This checks the schema-backed proof trace, public-safety invariants, and fixture sanitization using the pinned SCLite dependency. The fixture is dry-run/local/example-only evidence; it does not claim live vulnerability evidence.

For the generated public demo bundle path, run:

```bash
bin/demo-bundle --print-summary
```

For the repeatable local/public-safe Security Contract validation receipt, run:

```bash
python scripts/run_security_contract_validation.py --include-pytest
```

Expected result: JSON with `artifact_type: security_contract_validation_receipt`, `schema_version: v0.1`, and `status: passed`. This runner validates the public validation surface index, validates the public snapshot manifest, validates the committed fixtures, generates the demo bundle from a disposable public snapshot, assembles a temporary public snapshot, validates copied fixtures inside that snapshot, audits snapshot residue, validates the public-safe Replayable Truth Runtime fixture and Scope Fidelity fixtures, and optionally runs the focused Security Contract/public snapshot pytest slice. The receipt is produced through SCLite validation helpers, schema-backed by `schemas/security_contract_validation_receipt.v0.1.schema.json`, and described in `references/security-contract-validation-receipt-v0.1.md`.

## What not to assume

Passing tests does **not** mean:
- every live deployment path is public-ready
- every subsystem is frozen
- the repo already has polished packaging or production ergonomics

Validation should be read together with `PUBLIC_STATUS.md`, not as a substitute for it.

## Current truth

Ravenclaw is already testable and inspectable in public form.
The remaining gap is less about whether verification exists, and more about making those verification surfaces easier for public readers to discover and interpret.