# Reviewer Validation Guide

This guide gives a public reviewer the shortest useful path for validating Ravenclaw without assuming access to a live operator environment.

It is intentionally local/public-safe. It does **not** authorize live target execution, protocol adapter work, publication, or production-readiness claims.

## 1. Start with repo truth

Read these first:

1. `PUBLIC_STATUS.md` — maturity and current public truth.
2. `QUALITY_SIGNALS.md` — what the repo's trust signals support and do not support.
3. `VALIDATION.md` — runnable validation commands.
4. `references/public-safe-proof-walkthrough.md` — the shortest proof-trace walkthrough.
5. `SECURITY_CONTRACT_LAYER.md` — contract-layer proof direction and artifact map.
6. `PROOF_OF_VALUE.md` — value framing without live exploit claims.

## 2. Run the broad validation surface

From the repository root after the dev/test install path in `INSTALL.md`:

```bash
python scripts/validate_public_install.py --dev
pytest -q
```

For CI-parity slices:

```bash
python scripts/run_pytest_slice.py --list
for slice in contracts_policy auto_campaign runtime_core runtime_runner logdash misc_public; do
  PYTHONDONTWRITEBYTECODE=1 python scripts/run_pytest_slice.py "$slice"
done
```

What this supports:
- broad regression confidence across public runtime, policy, Logdash, and proof surfaces;
- package-chain readiness for `sclite-core` and `govengine`;
- visibility into the GovEngine public surface registry and Ravenclaw's security-profile compatibility seam.

What it does not prove:
- live deployment readiness, exhaustive security assurance, complete architecture stability, or readiness of a future GovEngine release candidate.

## 3. Inspect validation surfaces and snapshot files

List the public-safe validation surfaces:

```bash
python scripts/list_public_validation_surfaces.py --format json --check
```

For an assembled public snapshot, use the Public Snapshot Manifest to map those surfaces to concrete files:

```bash
python scripts/build_public_snapshot_manifest.py . --check
python scripts/build_public_snapshot_manifest.py . --format reviewer-report --check
```

Expected manifest/reviewer-report result:
- `artifact_type: public_snapshot_manifest`
- `schema_version: v0.1`
- `summary.missing_path_count: 0`

Use this to answer: "Do the validation surfaces documented by the repo actually exist in this snapshot?"

## 4. Validate the Security Contract proof path

Run the consolidated local/public-safe receipt:

```bash
python scripts/validate_public_install.py --dev
python scripts/run_security_contract_validation.py --include-pytest
```

Before any public push, use the parity form:

```bash
python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix
```

Expected receipt result:
- `artifact_type: security_contract_validation_receipt`
- `schema_version: v0.1`
- `status: passed`

This validates the public-safe proof trace:

`scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence summary`

## 5. Read the evidence trail

Primary proof/evidence files:

- `references/public-safe-proof-walkthrough.md`
- `examples/security-contract-proof/`
- `examples/contract-lifecycle-v0.2/`
- `examples/replayable-truth-runtime/`
- `examples/scope-fidelity-report/`
- `schemas/*.v0.1.schema.json`
- `references/*v0.1.md`
- `references/public-validation-surface-index-v0.1.md`
- `references/public-snapshot-manifest-v0.1.md`

These are dry-run/local/example artifacts. They are meant to show governance, schema, and evidence structure — not live vulnerability findings.


Proof-of-value scorecard:

Committed fixture validation:

```bash
python scripts/validate_proof_of_value_scorecard.py examples/proof-of-value-scorecard/scorecard.json
```


```bash
python scripts/build_proof_of_value_scorecard.py . --check
python scripts/build_proof_of_value_scorecard.py . --format markdown --check
```

## 6. Non-claims to preserve

Passing the above checks does **not** mean:

- Ravenclaw is production-ready for every deployment.
- Live target testing is authorized.
- The public snapshot contains private operator state.
- Protocol adapters such as OpenClaw, MCP, or A2A are complete.
- Demo evidence is live vulnerability evidence.

If a future change weakens these non-claims, treat it as a publication-safety regression.
