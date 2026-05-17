# OpenClaw Adapter Contract Map

## Status

Adapter-prep reference only. This document maps how Ravenclaw's Security Contract Layer could be carried by a future OpenClaw Skill or plugin.

It is **not** an adapter implementation, not an OpenClaw integration guide, and not permission to run security tools. This is not an adapter implementation.

## Purpose

Ravenclaw's current public proof shows a local, dry-run, schema-backed path:

`scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence summary`

A future OpenClaw carrier should preserve that path instead of translating it into informal chat intent or free-form shell commands.

This map defines the minimum contract responsibilities that an OpenClaw-facing adapter must satisfy later.

## Non-goals

This document does **not**:

- implement an OpenClaw Skill, plugin, node integration, or runtime hook;
- start MCP or A2A adapter work;
- authorize live target execution;
- claim production deployment readiness;
- claim live vulnerability discovery;
- require private operator state, local memory, credentials, or raw runtime artifacts;
- replace Ravenclaw Runtime as the reference/proof implementation.

## Carrier responsibilities

| Responsibility | Future OpenClaw carrier behavior | Required Ravenclaw artifact | Public-safe validation surface |
| --- | --- | --- | --- |
| Scope intake | Accept or reference explicit operator-authorized scope before any action proposal. | `scope/input` fixture fields, `campaign.md`, policy context | `examples/security-contract-proof/input_scope.json` |
| Policy decision handoff | Preserve approval/rejection reason as structured data, not only prose. | `PolicyDecision` | `schemas/policy_decision.v0.1.schema.json`, `references/policy-decision-v0.1.md` |
| Prepared spec boundary | Carry normalized tool intent and request-shape facts without treating LLM prose as executable authority. | `PreparedExecutionSpec` / redacted prepared spec | `govengine.contracts.execution`, `examples/security-contract-proof/redacted_prepared_execution_spec.json` |
| Approval boundary | Require an approved execution spec before execution-engine construction. | `ApprovedExecutionSpec` | `schemas/approved_execution_spec.v0.1.schema.json`, `references/approved-execution-spec-v0.1.md` |
| Execution truth | Preserve whether the run was dry-run/local/mock/external/live and what command/spec was actually executed. | `ExecutionReceipt` | `schemas/execution_receipt.v0.1.schema.json`, `references/execution-receipt-v0.1.md` |
| Evidence separation | Keep evidence summaries separate from dry-run receipts and explicit about what they do not prove. | `EvidenceBundle` | `schemas/evidence_bundle.v0.1.schema.json`, `references/evidence-bundle-v0.1.md` |
| Replay/review | Provide enough artifact pointers for offline replay or reviewer validation without private state. | validation receipt, public snapshot manifest, proof-of-value scorecard | `scripts/run_security_contract_validation.py`, `scripts/build_public_snapshot_manifest.py`, `scripts/build_proof_of_value_scorecard.py` |
| Non-claim preservation | Preserve explicit non-claims when summarizing results back into OpenClaw chat or task output. | public status / proof-of-value docs | `PUBLIC_STATUS.md`, `PROOF_OF_VALUE.md`, `QUALITY_SIGNALS.md` |

## Minimum future adapter gates

A future OpenClaw carrier should not be considered credible until it can demonstrate all of the following locally:

1. It can ingest a bounded scope artifact without expanding target authority.
2. It can surface a `PolicyDecision` with structured status/reason fields.
3. It can expose the prepared and approved execution-spec boundary.
4. It can produce or reference a receipt that labels dry-run/local/mock truth explicitly.
5. It can attach evidence summaries without claiming live vulnerability discovery from dry-run artifacts.
6. It can emit a validation receipt or equivalent pointer that a reviewer can replay locally.
7. It can preserve public non-claims in its user-facing summary.

## Suggested future adapter flow

1. OpenClaw receives an operator request and campaign/scope reference.
2. The future Ravenclaw Skill/plugin converts that request into a Ravenclaw action proposal or runtime task, but does not construct shell commands directly.
3. Ravenclaw policy/auditor logic returns a structured decision.
4. The future carrier displays the decision and required operator approval boundary.
5. Only an approved execution spec reaches Ravenclaw's execution engine.
6. The execution engine returns a receipt with dry-run/local/mock/live truth labeled.
7. OpenClaw presents a compact summary plus artifact paths and explicit non-claims.

## Publication boundary

This document is safe for public release because it is only a contract map. It contains no credentials, private targets, operator memory, raw runtime state, or live execution evidence.

Before any actual OpenClaw adapter implementation is published, require a separate review for:

- authorization and scope UX;
- secret handling and redaction;
- command construction authority;
- tool allowlists and destructive-action guards;
- receipt/evidence provenance;
- channel-specific leakage risks;
- parity with the public validation runner.

## Relationship to other carriers

OpenClaw remains the recommended first carrier because it is the operator-facing environment around this work.

MCP should remain later and policy-gated.

A2A should remain last or example-first.

The contract layer should stay carrier-independent: carriers transport and present the artifacts; they should not redefine the security truth model.
