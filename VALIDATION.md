# VALIDATION.md

This file tells a public reader how to validate the current Ravenclaw repository without assuming a full live operator environment. For a shorter reviewer-oriented path, see `REVIEWER_VALIDATION_GUIDE.md`.

## Fast public validation path

After following the dev/test path in `INSTALL.md`, run:

```bash
python scripts/validate_public_install.py --dev
pytest -q
```

`validate_public_install.py` confirms that the public dependency chain resolves
from the active Python environment before tests run. For release readiness,
run it inside a clean virtual environment; a broad system interpreter can fail
`pip check` because unrelated installed tools are dependency-inconsistent.
`pytest -q` remains the primary repo-wide validation command exposed publicly
today.

For a repeatable clean-env validation from this checkout, use:

```bash
python scripts/validate_clean_public_install.py \
  --venv /tmp/ravenclaw-clean-public-install \
  --dev
```

For coordinated source-chain validation before a cross-repo push, install the
local SCLite and GovEngine trees into the clean venv before Ravenclaw:

```bash
python scripts/validate_clean_public_install.py \
  --venv /tmp/ravenclaw-clean-source-chain \
  --dev \
  --sclite-source /path/to/SCLite \
  --govengine-source /path/to/GovEngine
```

Persisted runtime state truth is checked separately with:

```bash
python scripts/validate_runtime_state_truth.py
python scripts/validate_govengine_helper_boundary.py
python scripts/validate_package_runtime_boundary.py
python scripts/validate_openclaw_fixture_presenter.py
```

The runtime-state validator compares the state manifest, canonical path
helpers, `STATE_FILES.md`, and the GovEngine state/control projection map. The
GovEngine helper-boundary validator obtains the optional helper module set from
GovEngine's public `security_profile_helpers` registry and rejects direct
runtime/Logdash imports outside `engine/govengine_security_helpers.py`, so the
host-owned narrowing point cannot silently omit part of the upstream-declared
surface. It also rejects reintroducing `govengine.policy.gateway` into that
seam: the active policy/scope decision now belongs to
`engine/security_policy_gateway.py` and uses Ravenclaw-owned scope state. The
package/runtime boundary validator checks that the published
`ravenclaw-security` wheel remains a narrow public helper package while the
full runtime, `engine/`, Logdash, demo, and validation workflows remain
source/reference-owned. The OpenClaw fixture-presenter validator checks the
committed public-safe fixture packet under
`examples/openclaw-fixture-presenter/` without registering a carrier adapter.
None of these validators reads live targets, mutates state, sends carrier
messages, or starts Logdash.

## Install validation

Runtime-only install check:

```bash
python scripts/validate_public_install.py
```

Dev/test install check, required before `pytest` and `--include-pytest` validation receipts:

```bash
python scripts/validate_public_install.py --dev
```

When validating from a clean package/downstream environment, keep generated runtime state outside the publish tree:

```bash
RAVENCLAW_REPORTS_DIR=/tmp/ravenclaw-reports \
RAVENCLAW_TMP_DIR=/tmp/ravenclaw-tmp \
RAVENCLAW_LOGDASH_DB=/tmp/ravenclaw-logdash.db \
RAVENCLAW_PIPELINE_CONFIG=/tmp/ravenclaw-pipeline_config.json \
python -m pytest -q
```

Expected result:

```text
ravenclaw_public_install_validation:runtime:passed
```

or, for dev/test installs:

```text
ravenclaw_public_install_validation:dev:passed
```

This checks Python version, importability/version visibility for `PyYAML`, `govengine`, `sclite-core`, and — with `--dev` — `pytest` and `Flask`; verifies the GovEngine public surface registry expected by Ravenclaw (`artifact_governance_core`, `planning_contracts_core`, `admission_policy_core`, `evidence_review_core`, `domain_profile_sdk`, `runtime_contract_proofs`, `controlled_execution_core`, `security_profile_helpers`); validates the published `govengine.security_profile` facade directly; validates Ravenclaw's own security-profile manifest and OpenClaw readiness-packet boundary; then runs `python -m pip check`. The focused GovEngine seam tests cover the same package-boundary path. These checks do not prove production deployment readiness or validate private operator overlays.

`scripts/validate_clean_public_install.py` is a wrapper around the same
validation surface. It creates a new virtual environment, installs the chosen
package/source chain, and then runs `validate_public_install.py`, so `pip check`
is scoped to the install under validation rather than the operator machine's
global Python environment.

With the current GovEngine `0.11.0-alpha` source/package line, Ravenclaw's source dependency baseline is `govengine>=0.11.0a0,<0.12` and `sclite-core>=0.8.0a0,<0.9`. Public install validation also requires Ravenclaw's boundary-profile readiness through `engine/govengine_boundary_profile.py`. That check validates `govengine.kernel_boundary_report`, the Ravenclaw profile contract, the public surface index, and the expected non-claims around live execution and carrier-adapter ownership. Ravenclaw's focused state/control projection tests validate the GovEngine runtime-shell surface for host control actions, queue snapshots, and runtime snapshots; focused planning projection tests validate the GovEngine planning-contract surface for redacted planner/runtime task handoffs; focused admission projection tests validate the GovEngine admission-policy surface for redacted go/no-go, policy, approval, and audit records; focused runner-supervision projection tests validate approved-spec runner requests, supervision plans, leases, and receipts; focused review projection tests validate receipt-bounded evidence claims and review results; focused security-profile tests validate that Ravenclaw is documented as a security runtime/profile over GovEngine + SCLite while OpenClaw remains at readiness-packet status; focused OpenClaw readiness tests validate redaction/output, approval-UX, command-authority, and rollback/stop boundaries before any carrier implementation.

## Package/runtime boundary and fixture presenter

The current PyPI package line is intentionally narrow:
`ravenclaw-security==0.18.0` packages the public helper/profile/readiness API
under `ravenclaw/`. It is not the full source/runtime package. To mechanically
check that package/runtime boundary, run:

```bash
python scripts/validate_package_runtime_boundary.py
```

Expected result:

```text
package_runtime_boundary_ok:ravenclaw-security==0.18.0:packages=ravenclaw
```

For the OpenClaw fixture-presenter review harness, run:

```bash
python scripts/validate_openclaw_fixture_presenter.py
```

Expected result:

```text
openclaw_fixture_presenter_ok:adapter_status=not_implemented:fixture_mode=presenter_only
```

This validates `examples/openclaw-fixture-presenter/carrier_input.json`
against `examples/openclaw-fixture-presenter/presenter_packet.json`. The
fixture proves deterministic redaction and command-authority boundaries against
carrier-shaped data only. It does not implement an OpenClaw Skill/plugin, send
messages, register tools, run commands, or make OpenClaw/MCP/A2A adapter
claims.

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

The public GitHub Actions slice workflow installs the current SCLite and GovEngine source lines before Ravenclaw test dependencies. That keeps Ravenclaw source CI deterministic across coordinated prerelease pushes while package-index propagation is still catching up; package publication still has to be verified separately with the clean PyPI install checks below.

## What this validates

Running the suite exercises public-visible correctness signals across areas such as:
- planner and runtime contracts
- policy and approval behavior
- execution contract shaping
- demo-only GovEngine signer/verifier trust-port binding for lifecycle tickets, using the published GovEngine demo ports rather than a Ravenclaw-local signing fallback (no PKI/key ownership claim)
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
- `engine/tests/test_govengine_control_gate_adapter.py`
- `engine/govengine_trust_demo.py`
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

## Demo scenario verification

For the compact reviewer-facing Ravenclaw -> GovEngine -> SCLite scenario, run:

```bash
./scripts/bootstrap_public_demo.sh scenario
```

This writes `demo-output/demo-scenario/demo_scenario_summary.json` and `.md`, validates generated SCLite lifecycle artifacts, verifies the artifact-chain manifest, and records the GovEngine `security_profile` boundary. Its version summary is taken from the GovEngine and SCLite modules actually executed in the scenario; distribution metadata resolution remains the job of the clean public-install gate. It remains local/demo-safe and dry-run/mock only.

## Current lifecycle/review-bundle validation

To generate and validate the current public-safe proof path, run:

```bash
bin/demo-bundle --output-dir demo-output --print-summary
sclite validate-chain demo-output/artifact_chain_manifest.json
sclite verify-lifecycle demo-output/artifact_chain_manifest.json
sclite review demo-output/review_bundle --format summary --fail-on review
```

The active demo bundle emits a current SCLite lifecycle using a scoped
`execution_ticket.v0.3` and materializes a canonical `review_bundle/`. Older
proof-trace fixtures are migration/history material and are not a current
public surface or release gate.

The SCLite verifier checks the hash chain and semantic lifecycle bindings: canonical role order, ticket -> execution contract, receipt -> ticket, evidence -> receipt, and manifest path containment.

For the repeatable local/public-safe Security Contract validation receipt, first ensure dev/test dependencies are present, then run:

```bash
python scripts/validate_public_install.py --dev
python scripts/run_security_contract_validation.py --include-pytest
```

Expected result: JSON with `artifact_type: security_contract_validation_receipt`, `schema_version: v0.1`, and `status: passed`. This runner validates the public validation surface index and public snapshot manifest, generates and reviews the current demo bundle from a disposable public snapshot, assembles a temporary public snapshot, audits snapshot residue, validates the public-safe Replayable Truth Runtime and Scope Fidelity fixtures, and optionally runs the focused current proof/public snapshot pytest slice. The receipt is produced and owned by Ravenclaw's host validation runner, schema-backed by `schemas/security_contract_validation_receipt.v0.1.schema.json`, and described in `references/security-contract-validation-receipt-v0.1.md`; SCLite remains the lifecycle/review-bundle verifier rather than the owner of this current host receipt.

For quick structural diagnostics in automation that must not execute the Ravenclaw demo planner/pipeline, use:

```bash
python scripts/run_security_contract_validation.py --structural-only --include-pytest
```

This structural profile skips demo bundle and demo scenario checks, and omits focused pytest targets that generate demo runtime artifacts. It is suitable for fast package-boundary and fixture hygiene checks. Use the full command above for reviewer/release validation when demo runtime artifact generation is intentional.

## What not to assume

Passing tests does **not** mean:
- every live deployment path is public-ready
- every subsystem is frozen
- the repo already has polished packaging or production ergonomics

Validation should be read together with `PUBLIC_STATUS.md`, not as a substitute for it.

## Current truth

Ravenclaw is already testable and inspectable in public form.
The remaining gap is less about whether verification exists, and more about making those verification surfaces easier for public readers to discover and interpret.
