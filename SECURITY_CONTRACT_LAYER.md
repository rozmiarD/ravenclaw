# SECURITY_CONTRACT_LAYER.md

## Status

Draft v0.2 direction. The reusable contract/schema core lives in the standalone public **SCLite** package/repository (`https://github.com/rozmiarD/SCLite`) and Ravenclaw consumes it as a pinned dependency. Ravenclaw Runtime remains the governed reference/proof implementation; SCLite remains a contract lifecycle, validation, redaction, integrity-chain, and public-safe fixture layer — not a new protocol.

## What it is

The Security Contract Layer is the small set of structured artifacts Ravenclaw uses to carry security-critical truth through a governed workflow.

Legacy v0.1 proof trace:

`scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run/execution receipt -> evidence summary`

SCLite v0.2 lifecycle chain:

`intent -> policy decision -> execution contract -> execution ticket -> execution receipt -> evidence contract -> artifact chain manifest`

Its purpose is to make scope, policy, approval, execution constraints, evidence, provenance, and local artifact-chain integrity explicit enough to validate, redact, replay, verify, and explain.

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

The reusable SCL implementation now lives in the external `sclite` package, with lifecycle projection helpers consumed through `govengine.sclite_adapter`. Ravenclaw keeps only integration code: `engine/security_contract_layer.py` adds host-owned OODA/demo projection around the GovEngine/SCLite adapter, and `engine/public_demo_bundle.py` remains the demo bundle orchestration/CLI surface. Root `schemas/`, `examples/security-contract-proof/`, and `examples/contract-lifecycle-v0.2/` are public-review copies synchronized from SCLite so Ravenclaw snapshots remain self-describing.

Ravenclaw also keeps `engine/govengine_boundary_profile.py` as a thin consumer for GovEngine's kernel/profile boundary report. Public install validation now requires the active package chain, `govengine>=0.10.0a0,<0.11` and `sclite-core>=0.5.1,<0.6`, to expose `govengine.kernel_boundary_report`, the Domain Profile SDK, and runtime contract proof surfaces, and reports failure if the boundary-profile check does not pass.

The current GovEngine wrapper classification is tracked in `references/govengine-wrapper-audit.md`. Pure alias wrappers are retired after Ravenclaw callers/tests migrate to direct package imports; host-side seams remain only where Ravenclaw owns runtime/profile glue rather than reusable GovEngine behavior.

A committed public-safe fixture lives at `examples/security-contract-proof/` and can be validated with `scripts/validate_security_contract_fixtures.py`. A replay fixture lives at `examples/replayable-truth-runtime/` and can be validated with `scripts/validate_replayable_truth_fixture.py`. The broader local/public-safe validation path is `scripts/run_security_contract_validation.py`, which emits a schema-backed `security_contract_validation_receipt` covering fixtures, demo-bundle smoke, demo scenario validation, temporary public snapshot assembly, snapshot-local fixture validation, residue audit, replay fixture validation, and optional focused pytest. For automation that must not execute the Ravenclaw demo planner/pipeline, pass `--structural-only` / `--no-demo-runtime` to skip demo-runtime checks and demo-runtime pytest targets.

## Relation to OpenClaw, MCP, and A2A

- **OpenClaw**: first practical later adapter. A future skill/plugin can validate proposals, check scope, build/redact specs, and qualify evidence using these contracts. Adapter-prep responsibilities are mapped in `references/openclaw-adapter-contract-map.md`; pre-implementation gates are listed in `references/carrier-readiness-checklist.md`, with proposal fields in `references/carrier-readiness-packet-template.md`. These are not implementations.
- **MCP**: later policy-gated tool wrapper/gateway candidate after schemas are stable.
- **A2A**: later metadata/profile example, not an implementation priority.

No adapter should be promoted before the public proof bundle and schema validation are credible.

## v0.2 lifecycle artifacts

| Artifact | Current implementation status | Producer | Consumer | Notes |
|---|---|---|---|---|
| `IntentContract` | Implemented as public-safe SCLite v0.2 adapter output | `govengine.sclite_adapter` via `engine/security_contract_layer.py` | reviewer/public demo bundle, chain verifier | Records what Ravenclaw intended before authority exists. |
| `PolicyDecision` v0.2 | Implemented alongside legacy v0.1 decision | `govengine.sclite_adapter` via `engine/security_contract_layer.py` | lifecycle chain, reviewer | Links to the exact intent descriptor. |
| `ExecutionContract` | Implemented as v0.2 lifecycle execution-shape artifact | `govengine.sclite_adapter` via `engine/security_contract_layer.py` | execution ticket, reviewer | Captures target binding, execution shape, and bounds. |
| `ExecutionTicket` | Implemented as integrity-bound v0.2 ticket and enforced on the local approved-spec runtime path; demo mode adds GovEngine signer/verifier-port trust metadata | `govengine.sclite_adapter` plus demo projection in `engine/security_contract_layer.py` / `engine/govengine_trust_demo.py`; gate in `engine/executor.py` and `engine/govengine_control_gate_adapter.py` | lifecycle chain, local execution gate, reviewer | Binds to the exact execution contract digest. Demo signatures are fixture/reviewer evidence only; signer identity, PKI, CA, KMS, and key-store ownership are not claimed in core. |
| `ExecutionReceipt` v0.2 | Implemented as lifecycle receipt | `govengine.sclite_adapter` via `engine/security_contract_layer.py` | evidence contract, reviewer | Records what Ravenclaw dry-ran/executed in compact public-safe form. |
| `EvidenceContract` | Implemented as v0.2 claims/non-claims artifact | `govengine.sclite_adapter` via `engine/security_contract_layer.py` | reviewer/public bundle | Links evidence claims to the exact receipt/ticket. |
| `ArtifactChainManifest` | Implemented and verified by SCLite | `sclite.integrity.build_artifact_chain_manifest(...)` via Ravenclaw adapter | `sclite validate-chain` / `sclite verify-lifecycle` / public demo bundle | Lightweight hash-linked integrity chain plus semantic lifecycle binding checks, not PKI or legal authorization proof. |

## v0.1 compatibility artifacts

| Artifact | Current implementation status | Producer | Consumer | Notes |
|---|---|---|---|---|
| `RuntimeTaskV2` | Implemented / evolving | `normalize_runtime_task_v2(...)` in `engine/runtime_task_schema.py` | planner/runtime handoff | Documented in `references/runtime-task-contract-v2.md`; schema version `2`. |
| `PolicyDecision` | Implemented as legacy `{pass, reason}` plus schema-backed v0.1 compatibility artifact | `evaluate_action_spec(...)` / `normalize_policy_decision_v0(...)` in `govengine.policy.gateway`; public artifact via `govengine.sclite_adapter` and `engine/security_contract_layer.py` host wrapper | pipeline/policy gate, public demo bundle | Schema: `schemas/policy_decision.v0.1.schema.json`; reference: `references/policy-decision-v0.1.md`. |
| `PreparedExecutionSpec` | Implemented | `build_prepared_execution_spec(...)` in `govengine.contracts.execution` | auditor/redaction/approval path | Version `2026-03-18.prepared.v1`; includes scope facts and request-shape hygiene. |
| `RedactedPreparedExecutionSpec` | Implemented | `redact_prepared_execution_spec_for_auditor(...)` in `govengine.contracts.execution` | auditor/public proof | Removes or masks stdin, cookies, basic auth, and sensitive request decoration. |
| `ApprovedExecutionSpec` | Implemented; schema v0.1 introduced | `build_approved_execution_spec(...)` in `govengine.contracts.execution` | `ExecutionEngine.execute_approved_spec(...)` in `engine/executor.py` | Schema: `schemas/approved_execution_spec.v0.1.schema.json`; reference: `references/approved-execution-spec-v0.1.md`. |
| `ExecutionReceipt` | Implemented in executor output; public-safe demo receipt schema-backed in v0.1 | `ExecutionEngine.execute_approved_spec(...)`; public artifact via SCLite and `engine/security_contract_layer.py` host projection wrapper | pipeline/demo/reporting | Schema: `schemas/execution_receipt.v0.1.schema.json`; reference: `references/execution-receipt-v0.1.md`; compact/sanitized, no raw stdout/stderr. |
| `EvidenceBundle` | Public-safe demo evidence bundle schema-backed in v0.1; broader qualification schema later | evidence and qualification modules such as `engine/vuln_qualification.py` plus GovEngine confirmation-evidence policy helpers; public artifact via SCLite and `engine/security_contract_layer.py` host projection wrapper | reporting/follow-up/public proof | Schema: `schemas/evidence_bundle.v0.1.schema.json`; reference: `references/evidence-bundle-v0.1.md`; states dry-run proof criteria and non-claims. |
| `ScopeFidelityReport` | Implemented in SCLite core as a neutral static host-binding review artifact | `sclite.scope_fidelity.build_scope_fidelity_report(...)` / `sclite scope-fidelity` | reviewer/preflight, later carrier-agnostic API surfaces | Public fixtures still exercise `schemas/scope_fidelity_report.v0.1.schema.json`; Ravenclaw also mirrors SCLite 0.5's `schemas/scope_fidelity_report.v0.2.schema.json` for review-bundle readiness. Reports `pass`, `review`, or `fail` without executing tools or proving legal authorization. |
| `SecurityContractValidationReceipt` | Implemented as local/public-safe validation receipt schema-backed in v0.1 | `scripts/run_security_contract_validation.py` / `sclite.validation` | publication prep, CI/reviewer validation, later adapter surfaces | Schema: `schemas/security_contract_validation_receipt.v0.1.schema.json`; reference: `references/security-contract-validation-receipt-v0.1.md`; records validation checks and explicit non-authorizations. |
| `RuntimeTruth` | Implemented for demo/delivery truth | `engine/public_delivery.py`, pipeline output, Logdash truth docs | public bundle/operator UI | Includes demo/local/external mode, adapter mode, dry-run/mock truth, provenance/source labels. |

## Demo signing/trust projection

Ravenclaw demo lifecycle artifacts may include deterministic signing/trust metadata on `execution_ticket.json`. The signature binds to the `execution_contract` descriptor digest and is evaluated through GovEngine signer/verifier-port shapes. This is intentionally host/demo projection glue: it lets reviewers see how a future host-provided trust decision would travel through the lifecycle chain while preserving the non-claim that GovEngine, SCLite, and Ravenclaw do not own PKI, CA, KMS, trust stores, key storage, or production identity proof.

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

1. Keep Ravenclaw consuming SCLite as the single contract-core source of truth.
2. Keep the public demo/proof bundle trace deterministic and sanitized.
3. Maintain schema-backed v0.1 artifacts for `PolicyDecision`, `PreparedExecutionSpec`, `RedactedPreparedExecutionSpec`, `ApprovedExecutionSpec`, public-safe `ExecutionReceipt`, public-safe `EvidenceBundle`, redaction/public-surface artifacts, `ScopeFidelityReport`, and `SecurityContractValidationReceipt`.
4. Keep Ravenclaw root `schemas/` and `examples/security-contract-proof/` synchronized with the pinned SCLite baseline for reviewer/snapshot readability.
5. Keep `scripts/run_security_contract_validation.py` as a Ravenclaw host entrypoint delegating to `engine/scl_validation_runner.py`; core fixture/schema validation comes from `sclite.validation`.
6. Keep Replayable Truth Runtime visible as the proof/evaluation engine for offline governance-aware replay.
7. Keep Ravenclaw Runtime as proof/reference while sharpening the internal contract boundary.
8. Plan engine extraction only after the SCLite dependency seam is validated.
9. Build OpenClaw Skill later as the first adapter.
10. Build MCP Policy Gateway later after schemas/examples are stable.
11. Add A2A security metadata/profile later as an example-first carrier.

## Explicit non-goal

Ravenclaw is not building a new general agent protocol. The Security Contract Layer defines governance/evidence artifacts that can be carried through existing systems.
