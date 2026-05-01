# Proof of Value

Ravenclaw's public proof of value is not "the agent found a live bug in this repository".

The current public claim is narrower and more defensible:

> Ravenclaw shows that security autonomy can be made more valuable by making scope, policy, execution, evidence, replay, and review surfaces explicit and locally verifiable.

This document translates the existing validation surfaces into market-legible value signals without claiming live exploit performance or production readiness.

## Value thesis

Security automation is useful only when operators can answer:

1. What was the system allowed to touch?
2. Who or what approved the action?
3. What execution spec actually reached the engine?
4. Was the run dry-run/local/public-safe or live?
5. What evidence was produced?
6. Can a reviewer replay or inspect the result without private operator state?
7. What does the result **not** prove?

Ravenclaw's current public proof surfaces are designed around those questions.

## Public value signals

| Signal | Public evidence | What it supports | What it does not claim |
| --- | --- | --- | --- |
| Governance-first execution | `SECURITY_CONTRACT_LAYER.md`, `schemas/*.v0.1.schema.json`, `references/*v0.1.md` | The system models policy and execution as explicit contracts, not informal prompt intent. | Does not prove every live policy or deployment configuration is correct. |
| Dry-run proof trace | `examples/security-contract-proof/`, `scripts/validate_security_contract_fixtures.py` | A reviewer can inspect a complete local proof path from scope/input to evidence summary. | Does not claim live vulnerability evidence. |
| Validation receipt | `scripts/run_security_contract_validation.py`, `schemas/security_contract_validation_receipt.v0.1.schema.json` | Local proof checks can be repeated and summarized in a machine-readable receipt. | Does not authorize publication or live target testing. |
| CI parity | `.github/workflows/pytest.yml`, `scripts/run_pytest_slice.py` | Public CI behavior can be reproduced locally before push. | Does not replace post-push GitHub Actions status. |
| Snapshot reviewability | `scripts/assemble_public_snapshot.sh`, `scripts/build_public_snapshot_manifest.py`, `REVIEWER_VALIDATION_GUIDE.md` | A public snapshot can be checked for validation-surface completeness and review boundaries. | Does not prove the snapshot is the full live operator workspace. |
| Replayable truth | `examples/replayable-truth-runtime/`, `REPLAYABLE_TRUTH_RUNTIME.md` | Preserved runtime decisions can be replayed offline without live target execution by default. | Does not replay private operator state. |
| Scope fidelity | `examples/scope-fidelity-report/`, `scripts/build_scope_fidelity_report.py` | Target-binding/request-shape drift can be classified from local artifacts. | Does not scan hosts or infer authorization beyond supplied artifacts. |

## Benchmark framing

A useful public benchmark for Ravenclaw should measure reviewability and governance quality, not only whether an autonomous system can produce many actions.

Suggested public-safe benchmark dimensions:

1. **Scope fidelity** — Does the prepared or approved action stay bound to the intended target/scope?
2. **Policy decision clarity** — Is the approval/rejection reason structured and inspectable?
3. **Execution spec accountability** — Can a reviewer see the exact normalized spec handed to execution without trusting free-form model text?
4. **Dry-run/evidence separation** — Are dry-run receipts clearly separated from live evidence claims?
5. **Replayability** — Can representative decisions be replayed offline from public-safe fixtures?
6. **Snapshot completeness** — Do advertised validation surfaces exist in the assembled public snapshot?
7. **Non-claim preservation** — Do outputs state what they do not prove?

These dimensions are deliberately different from "number of discovered vulnerabilities". They are meant to test whether autonomous security work is auditable, bounded, and reviewable.

## Current public non-claims

Ravenclaw does **not** currently claim:

- live vulnerability discovery in the public fixtures;
- production readiness across all deployments;
- a complete OpenClaw/MCP/A2A adapter ecosystem;
- that public snapshots contain private operator state;
- that passing local tests replaces human authorization or legal scope review;
- superior real-world outcomes by itself.


Proof-of-value scorecard:

Committed fixture validation:

```bash
python scripts/validate_proof_of_value_scorecard.py examples/proof-of-value-scorecard/scorecard.json
```


```bash
python scripts/build_proof_of_value_scorecard.py . --check
python scripts/build_proof_of_value_scorecard.py . --format markdown --check
```

## How to verify this value layer

Start with:

1. `REVIEWER_VALIDATION_GUIDE.md`
2. `VALIDATION.md`
3. `QUALITY_SIGNALS.md`
4. `SECURITY_CONTRACT_LAYER.md`
5. `examples/security-contract-proof/`
6. `examples/replayable-truth-runtime/`
7. `examples/scope-fidelity-report/`

Then run:

```bash
python scripts/run_security_contract_validation.py --include-pytest
python scripts/build_public_snapshot_manifest.py . --format reviewer-report --check
```

Expected result: public-safe validation passes, and generated output preserves explicit non-claims.
