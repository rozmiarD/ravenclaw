# QUALITY_SIGNALS.md

This file is the public trust surface for Ravenclaw.
It explains what evidence of quality exists in the repo today, what that evidence does support, and what it does not support.

## Why this file exists

A serious public repo should not ask readers to infer trust from tone alone.
Ravenclaw already has meaningful proof surfaces, but before this file they were scattered across CI, tests, references, and deeper architecture docs.

This document gathers the current signals into one honest public layer.

## Current quality signals

### 1. CI-backed regression execution

The repository includes a public GitHub Actions workflow:
- `.github/workflows/pytest.yml`

Current truth:
- runs on push and pull request
- uses Python 3.11
- installs the minimal test dependencies
- runs `pytest -q`

This is a real verification surface, not a placeholder badge-only claim.

### 2. Broad test corpus

Ravenclaw includes substantial automated coverage across:
- governance and policy behavior
- execution contracts
- planner/runtime contracts
- Logdash control and projection behavior
- runtime recovery and state truth
- evaluation and replay contracts
- qualification and signal semantics

Publicly visible examples:
- `tests/test_logdash_smoke.py`
- `tests/test_logdash_operator_truth_contracts.py`
- `tests/test_runtime_snapshot_integration.py`
- `engine/tests/test_execution_contracts.py`
- `engine/tests/test_runtime_plan_service_contracts.py`
- `engine/tests/test_runtime_execution_gate.py`
- `engine/tests/test_policy_core_approved_spec.py`
- `engine/tests/test_evaluation_replay.py`

The exact count will evolve, but the important signal is structural: this repo already tests contracts and truth surfaces, not just utility helpers.

### 3. Explicit contract documentation

Ravenclaw documents several important runtime and operator contracts directly in `references/`.
Examples include:
- `SECURITY_CONTRACT_LAYER.md`
- `references/approved-execution-spec-v0.1.md`
- `references/runtime-task-contract-v2.md`
- `references/planner-runtime-contract-map.md`
- `references/logdash-operator-truth-contracts.md`
- `references/evaluation-replay-contract.md`
- `references/effectiveness-metrics-contract.md`
- `references/runtime-artifact-ownership.md`

This matters because the project is not relying only on informal code behavior.
Important semantics are being pulled into named, reviewable reference docs.

### 4. Operator-truth orientation

Some tests and docs are specifically about whether operator-visible surfaces remain truthful under recovery, fallback, and partial-failure conditions.
That is a stronger signal than generic endpoint smoke testing.

Concrete examples:
- `references/logdash-operator-truth-contracts.md`
- `tests/test_logdash_operator_truth_contracts.py`
- `tests/test_logdash_runtime_recovery.py`
- `tests/test_logdash_services_projection.py`

### 5. Public-boundary discipline

The repo also includes publication-boundary and public-snapshot planning surfaces:
- `references/public-release-boundary.md`
- `references/public-release-review-matrix.md`
- `references/public-snapshot-plan.md`
- `scripts/assemble_public_snapshot.sh`

That is a useful trust signal because it shows the project is trying to separate a public artifact from a messy live workspace, instead of pretending they are the same thing.

## What these signals support

Taken together, these signals support the following public claims:
- the repo has a serious engineering core
- the project values contract clarity, not only feature growth
- important runtime and UI truth surfaces are tested
- the public repo is being shaped deliberately rather than dumped casually
- governance and operator-visibility behavior are treated as real correctness concerns
- the emerging Security Contract Layer is grounded in Ravenclaw Runtime artifacts, not protocol-first marketing

## What these signals do not prove

These signals do **not** prove:
- full production readiness in every subsystem
- broad deployment simplicity
- exhaustive security assurance
- complete absence of architectural churn
- a finished OpenClaw/MCP/A2A adapter ecosystem
- superior real-world outcomes by themselves

In other words, the trust surface is meaningful, but it is not magic.

## Best evidence trails for a new reader

If you want the shortest serious verification path, read these in order:
1. `PUBLIC_STATUS.md`
2. `DEMO.md`
3. `.github/workflows/pytest.yml`
4. `tests/test_logdash_smoke.py`
5. `SECURITY_CONTRACT_LAYER.md`
6. `references/approved-execution-spec-v0.1.md`
7. `references/runtime-task-contract-v2.md`
8. `references/logdash-operator-truth-contracts.md`
9. `ARCHITECTURE.md`

## Validation posture summary

The strongest honest quality claim today is:
Ravenclaw already has real contract, CI, and operator-truth validation surfaces, even though its public onboarding and proof presentation are still catching up to the strength of the technical core.