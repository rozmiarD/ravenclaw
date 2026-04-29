# SECURITY_CONTRACT_LAYER.md

## Status

Draft v0.1 direction. This is a contract/schema layer emerging from Ravenclaw Runtime. It is not a new protocol and not a separate public package yet.

## What it is

The Security Contract Layer is the small set of structured artifacts Ravenclaw uses to carry security-critical truth through a governed workflow:

`scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run/execution receipt -> evidence summary`

Its purpose is to make scope, policy, approval, execution constraints, evidence, and provenance explicit enough to validate, redact, replay, and explain.

## What it is not

It is not:
- a new general agent protocol;
- an A2A replacement;
- an MCP replacement;
- an OpenClaw replacement;
- a claim that Ravenclaw is a polished production package;
- permission to run tools outside explicit scope and authorization.

OpenClaw, MCP, and A2A are potential carriers/adapters for these contracts later. They are not the core product claim of this sprint.

## Why it exists

Ravenclaw's strongest reusable idea is not raw autonomy. It is governed execution truth:
- what input/scope was intended;
- what policy decided;
- what an auditor approved;
- what the executor was allowed to build;
- what was actually executed or dry-run;
- what evidence supports a conclusion;
- what was redacted, mocked, local, external, or operator-specific.

A named contract layer lets the project expose that value without pretending every runtime subsystem is stable or public-ready.

## Relation to Ravenclaw Runtime

Ravenclaw Runtime remains the reference/proof implementation. Its Replayable Truth Runtime capability is the proof/evaluation engine behind the contract layer: preserved runtime artifacts can be replayed offline without live target execution by default.

The contract layer should be extracted only from real artifacts already produced or consumed by runtime code. The current proof path is intentionally narrow and public-safe: demo mode, safe demo targets, mock/dry-run execution, sanitized output, and deterministic replay fixtures.

The current internal boundary module is `engine/security_contract_layer.py`. It centralizes public-safe proof-trace artifact builders, manifest metadata, deterministic public-safety invariant checks, the lightweight JSON Schema subset validator used by public contract fixtures/receipts, and a small scope-fidelity report builder for local target-binding/request-shape hygiene checks while `engine/public_demo_bundle.py` remains the demo bundle orchestration/CLI surface.

A committed public-safe fixture lives at `examples/security-contract-proof/` and can be validated with `scripts/validate_security_contract_fixtures.py`. A replay fixture lives at `examples/replayable-truth-runtime/` and can be validated with `scripts/validate_replayable_truth_fixture.py`. Scope Fidelity report fixtures live at `examples/scope-fidelity-report/` and can be validated with `scripts/validate_scope_fidelity_fixtures.py`. The broader local/public-safe validation path is `scripts/run_security_contract_validation.py`, which emits a schema-backed `security_contract_validation_receipt` covering fixtures, demo-bundle smoke, temporary public snapshot assembly, snapshot-local fixture validation, residue audit, replay fixture validation, Scope Fidelity fixture validation, and optional focused pytest.

## Relation to OpenClaw, MCP, and A2A

- **OpenClaw**: first practical later adapter. A future skill/plugin can validate proposals, check scope, build/redact specs, and qualify evidence using these contracts.
- **MCP**: later policy-gated tool wrapper/gateway candidate after schemas are stable.
- **A2A**: later metadata/profile example, not an implementation priority.

No adapter should be promoted before the public proof bundle and schema validation are credible.

## v0.1 candidate artifacts

| Artifact | Current implementation status | Producer | Consumer | Notes |
|---|---|---|---|---|
| `RuntimeTaskV2` | Implemented / evolving | `normalize_runtime_task_v2(...)` in `engine/runtime_task_schema.py` | planner/runtime handoff | Documented in `references/runtime-task-contract-v2.md`; schema version `2`. |
| `PolicyDecision` | Implemented as legacy `{pass, reason}` plus schema-backed v0.1 compatibility artifact | `evaluate_action_spec(...)` / `normalize_policy_decision_v0(...)` in `engine/policy_gateway.py`; public artifact via `engine/security_contract_layer.py` | pipeline/policy gate, public demo bundle | Schema: `schemas/policy_decision.v0.1.schema.json`; reference: `references/policy-decision-v0.1.md`. |
| `PreparedExecutionSpec` | Implemented | `build_prepared_execution_spec(...)` in `engine/execution_contracts.py` | auditor/redaction/approval path | Version `2026-03-18.prepared.v1`; includes scope facts and request-shape hygiene. |
| `RedactedPreparedExecutionSpec` | Implemented | `redact_prepared_execution_spec_for_auditor(...)` in `engine/execution_contracts.py` | auditor/public proof | Removes or masks stdin, cookies, basic auth, and sensitive request decoration. |
| `ApprovedExecutionSpec` | Implemented; schema v0.1 introduced | `build_approved_execution_spec(...)` in `engine/execution_contracts.py` | `ExecutionEngine.execute_approved_spec(...)` in `engine/executor.py` | Schema: `schemas/approved_execution_spec.v0.1.schema.json`; reference: `references/approved-execution-spec-v0.1.md`. |
| `ExecutionReceipt` | Implemented in executor output; public-safe demo receipt schema-backed in v0.1 | `ExecutionEngine.execute_approved_spec(...)`; public artifact via `engine/security_contract_layer.py` | pipeline/demo/reporting | Schema: `schemas/execution_receipt.v0.1.schema.json`; reference: `references/execution-receipt-v0.1.md`; compact/sanitized, no raw stdout/stderr. |
| `EvidenceBundle` | Public-safe demo evidence bundle schema-backed in v0.1; broader qualification schema later | evidence and qualification modules such as `engine/vuln_qualification.py`, `engine/evidence_policy.py`; public artifact via `engine/security_contract_layer.py` | reporting/follow-up/public proof | Schema: `schemas/evidence_bundle.v0.1.schema.json`; reference: `references/evidence-bundle-v0.1.md`; states dry-run proof criteria and non-claims. |
| `SecurityContractValidationReceipt` | Implemented as local/public-safe validation receipt schema-backed in v0.1 | `scripts/run_security_contract_validation.py` | publication prep, CI/reviewer validation, later adapter surfaces | Schema: `schemas/security_contract_validation_receipt.v0.1.schema.json`; reference: `references/security-contract-validation-receipt-v0.1.md`; records validation checks and explicit non-authorizations. |
| `ScopeFidelityReport` | Implemented as local/public-safe schema-backed v0.1 report | `build_scope_fidelity_report(...)` in `engine/security_contract_layer.py` | reviewer validation, future proposal/spec preflight, later adapter surfaces | Schema: `schemas/scope_fidelity_report.v0.1.schema.json`; reference: `references/scope-fidelity-report-v0.1.md`; classifies exact, ambiguous, and cross-host request-shape binding without live target execution. |
| `RuntimeTruth` | Implemented for demo/delivery truth | `engine/public_delivery.py`, pipeline output, Logdash truth docs | public bundle/operator UI | Includes demo/local/external mode, adapter mode, dry-run/mock truth, provenance/source labels. |

## Public safety and redaction requirements

Public contract examples must:
- use demo/local/dry-run paths only;
- use public-safe targets such as `example.com`;
- avoid live target testing and offensive execution;
- exclude credentials, cookies, auth tokens, private local paths, memory, reports, and raw operator state;
- prefer redacted prepared specs for public/auditor-facing examples;
- keep execution receipts compact and sanitized;
- label mock/local/external/dry-run truth explicitly.

## Near-term roadmap

1. Keep the public demo/proof bundle trace deterministic and sanitized.
2. Maintain schema-backed v0.1 artifacts for `ApprovedExecutionSpec`, `PolicyDecision`, public-safe `ExecutionReceipt`, and public-safe `EvidenceBundle`.
3. Keep `engine/security_contract_layer.py` as the internal helper/invariant boundary and avoid growing `engine/public_demo_bundle.py` back into contract logic.
4. Keep `examples/security-contract-proof/` synchronized with schemas and boundary invariants when the public proof trace changes.
5. Keep `scripts/run_security_contract_validation.py` as the repeatable schema-backed contract-validation receipt surface for local/public-safe proof checks.
6. Keep Replayable Truth Runtime visible as the proof/evaluation engine for offline governance-aware replay.
7. Keep `ScopeFidelityReport` small and deterministic as a reusable target-binding/request-shape hygiene proof surface, with exact/mismatch/ambiguous fixtures kept public-safe.
8. Keep Ravenclaw Runtime as proof/reference while sharpening the internal contract boundary.
9. Build OpenClaw Skill later as the first adapter.
10. Build MCP Policy Gateway later after schemas/examples are stable.
11. Add A2A security metadata/profile later as an example-first carrier.

## Explicit non-goal

Ravenclaw is not building a new general agent protocol. The Security Contract Layer defines governance/evidence artifacts that can be carried through existing systems.
