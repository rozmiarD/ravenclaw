# Proof-of-Value Scorecard

This scorecard summarizes public-safe benchmark dimensions for Ravenclaw. It does not claim live vulnerability discovery, production deployment readiness, or protocol-adapter completeness.

status: `passed`
dimensions: `7`
passed: `7`
failed: `0`

| Dimension | Status | Evidence | Non-claim |
| --- | --- | --- | --- |
| Scope fidelity | `passed` | `examples/scope-fidelity-report`<br>`scripts/build_scope_fidelity_report.py`<br>`schemas/scope_fidelity_report.v0.1.schema.json`<br>`schemas/scope_fidelity_report.v0.2.schema.json` | Does not scan hosts or infer authorization beyond supplied artifacts. |
| Policy decision clarity | `passed` | `schemas/policy_decision.v0.2.schema.json`<br>`engine/public_demo_bundle.py`<br>`SECURITY_CONTRACT_LAYER.md` | Does not prove every live policy configuration is correct. |
| Execution spec accountability | `passed` | `schemas/execution_contract.v0.2.schema.json`<br>`schemas/execution_ticket.v0.3.schema.json`<br>`engine/public_demo_bundle.py` | Does not authorize live command execution. |
| Dry-run/evidence separation | `passed` | `schemas/execution_receipt.v0.2.schema.json`<br>`schemas/evidence_contract.v0.2.schema.json`<br>`engine/public_demo_bundle.py` | Does not claim live vulnerability evidence. |
| Replayability | `passed` | `examples/replayable-truth-runtime`<br>`scripts/validate_replayable_truth_fixture.py`<br>`REPLAYABLE_TRUTH_RUNTIME.md` | Does not replay private operator state. |
| Snapshot completeness | `passed` | `scripts/build_public_snapshot_manifest.py`<br>`schemas/public_snapshot_manifest.v0.1.schema.json`<br>`REVIEWER_VALIDATION_GUIDE.md` | Does not prove the snapshot is the full live operator workspace. |
| Non-claim preservation | `passed` | `PROOF_OF_VALUE.md`<br>`QUALITY_SIGNALS.md`<br>`PUBLIC_STATUS.md` | Does not prove superior real-world outcomes by itself. |
