# Reviewer Validation Guide

This guide gives a public reviewer the shortest useful path for validating Ravenclaw without assuming access to a live operator environment.

It is intentionally local/public-safe. It does **not** authorize live target execution, protocol adapter work, publication, or production-readiness claims.

## Fastest useful path

If you only have a few minutes after installing dev dependencies:

```bash
./scripts/bootstrap_public_demo.sh scenario
python scripts/validate_public_install.py --dev
python scripts/validate_package_runtime_boundary.py
python scripts/validate_openclaw_fixture_presenter.py
python scripts/list_public_validation_surfaces.py --format json --check
```

This gives you a generated Ravenclaw/GovEngine/SCLite scenario, confirms the active package chain, checks the package/runtime boundary, validates the OpenClaw fixture-presenter example, and lists the public validation surfaces without requiring live targets. For broader confidence, continue with the full guide below.

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
- visibility into the GovEngine public surface registry, security-profile facade, and Ravenclaw boundary-profile check.

What it does not prove:
- live deployment readiness, exhaustive security assurance, complete architecture stability, or readiness of a future package release.

Package/runtime boundary checkpoint:

```bash
python scripts/validate_package_runtime_boundary.py
```

Expected result:

```text
package_runtime_boundary_ok:ravenclaw-security==0.18.0:packages=ravenclaw
```

OpenClaw fixture-presenter checkpoint:

```bash
python scripts/validate_openclaw_fixture_presenter.py
```

Expected result:

```text
openclaw_fixture_presenter_ok:adapter_status=not_implemented:fixture_mode=presenter_only
```

These checks preserve the current package/runtime boundary and fixture-review
posture: the PyPI helper package is narrow, the full runtime remains
source/reference-owned, and the OpenClaw-shaped fixture is not an adapter.

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

This validates the current lifecycle/review-bundle proof path:

`runtime projection -> policy decision -> execution contract -> scoped execution ticket -> execution receipt -> evidence contract -> review bundle`

## 5. Run the reviewer demo scenario

For a compact package-chain scenario that generates artifacts and validates the SCLite lifecycle chain:

```bash
./scripts/bootstrap_public_demo.sh scenario
```

Expected scenario summary files:

- `demo-output/demo-scenario/demo_scenario_summary.json`
- `demo-output/demo-scenario/demo_scenario_summary.md`

The summary records:

- Ravenclaw demo runtime mode and dry-run/mock execution adapter;
- active `govengine` and `sclite-core` package versions;
- GovEngine `security_profile_helpers` groups;
- demo execution-ticket signing/trust metadata bound to the execution-contract digest, when inspecting generated lifecycle artifacts;
- SCLite lifecycle files checked by the scenario;
- reviewer commands for independently checking the generated artifact-chain manifest.

This scenario is still local/demo-safe. It does not authorize live target testing or adapter implementation.
The demo signing/trust metadata is not PKI, production identity proof, or key-management support.

## 6. Read the evidence trail

Primary proof/evidence files:

- `references/public-safe-proof-walkthrough.md`
- generated `demo-output/review_bundle/`
- `engine/public_demo_bundle.py`
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

## 7. Non-claims to preserve

Passing the above checks does **not** mean:

- Ravenclaw is ready for every production deployment.
- Live target testing is authorized.
- The public snapshot contains private operator state.
- Protocol adapters such as OpenClaw, MCP, or A2A are complete.
- The OpenClaw fixture presenter is a real OpenClaw Skill/plugin.
- Demo evidence is live vulnerability evidence.
- Demo signing/trust metadata is PKI, production identity proof, or key-management support.

If a future change weakens these non-claims, treat it as a public-safety regression.
