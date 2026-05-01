# Carrier Readiness Packet Template

## Status

Template for future carrier proposals that want to move from readiness discussion toward implementation planning.

This is **not** an adapter implementation and does **not** authorize OpenClaw, MCP, A2A, live target execution, offensive tooling, production-readiness claims, or live vulnerability discovery.

Use this packet before any implementation branch starts.

## How to use

1. Copy this template into a proposal-specific document.
2. Fill every required field.
3. Link the completed packet from the implementation issue/plan.
4. Run the validation commands listed in the packet.
5. Do not begin implementation until blockers are resolved and the reviewer checklist owner signs off.

## Packet metadata

- Packet ID: `<carrier>-readiness-YYYY-MM-DD`
- Date:
- Author/operator:
- Reviewer checklist owner:
- Target carrier:
  - `[ ]` OpenClaw Skill/plugin
  - `[ ]` MCP gateway/tool wrapper
  - `[ ]` A2A metadata/profile
  - `[ ]` Other: `<describe>`
- Proposed mode:
  - `[ ]` docs/contracts-only
  - `[ ]` local-only prototype
  - `[ ]` dry-run integration
  - `[ ]` live-capable integration — requires separate explicit scope and approval

## Explicit non-goals

This proposal does not:

- implement unreviewed adapter execution paths;
- authorize live target execution;
- bypass Ravenclaw policy/auditor/execution-engine authority;
- expose private operator state, credentials, memory, raw logs, or unredacted runtime artifacts;
- claim production readiness;
- claim live vulnerability discovery from dry-run/local artifacts;
- change carrier order from OpenClaw first, MCP later, A2A last/example-first.

Add proposal-specific non-goals:

-
-
-

## Scope UX

Describe how the carrier will show explicit authorized scope before action proposal.

Required answers:

- Where does scope come from?
- How is scope displayed to the operator?
- How are out-of-scope requests refused?
- How is scope preserved in generated artifacts?

Evidence / links:

-

Blockers:

-

## Secrets and redaction

Describe how the carrier handles sensitive data.

Required answers:

- What fields are always redacted?
- How are stdin, cookies, auth headers, tokens, private paths, memory, logs, and raw runtime state handled?
- What is allowed in public output?
- What is allowed in private/operator-only output?
- What channel-specific leakage risks exist?

Evidence / links:

-

Blockers:

-

## Command authority boundary

Describe how the carrier prevents model prose or chat text from becoming executable authority.

Required answers:

- What creates the proposed action/spec?
- What policy/auditor decision is required?
- What produces the approved execution spec?
- What, if anything, reaches Ravenclaw's execution engine?
- Which commands/tools are impossible from this carrier by design?

Evidence / links:

-

Blockers:

-

## Contracts consumed and emitted

List the Security Contract Layer artifacts consumed and emitted.

| Artifact | Consumed | Emitted | Schema/reference | Notes |
| --- | --- | --- | --- | --- |
| Scope/input | `[ ]` | `[ ]` | `examples/security-contract-proof/input_scope.json` | |
| `PolicyDecision` | `[ ]` | `[ ]` | `schemas/policy_decision.v0.1.schema.json` | |
| `PreparedExecutionSpec` / redacted prepared spec | `[ ]` | `[ ]` | `engine/execution_contracts.py` | |
| `ApprovedExecutionSpec` | `[ ]` | `[ ]` | `schemas/approved_execution_spec.v0.1.schema.json` | |
| `ExecutionReceipt` | `[ ]` | `[ ]` | `schemas/execution_receipt.v0.1.schema.json` | |
| `EvidenceBundle` | `[ ]` | `[ ]` | `schemas/evidence_bundle.v0.1.schema.json` | |
| Validation receipt | `[ ]` | `[ ]` | `schemas/security_contract_validation_receipt.v0.1.schema.json` | |
| Public snapshot manifest | `[ ]` | `[ ]` | `schemas/public_snapshot_manifest.v0.1.schema.json` | |
| Proof-of-value scorecard | `[ ]` | `[ ]` | `schemas/proof_of_value_scorecard.v0.1.schema.json` | |

Missing contracts / blockers:

-

## Policy and tool allowlists

Describe how policy and tool restrictions are preserved.

Required answers:

- Which policy decision controls execution?
- Which whitelist/tool classes are allowed?
- Which destructive actions are impossible?
- What happens when policy rejects or requests owner approval?

Evidence / links:

-

Blockers:

-

## Dry-run/live truth and evidence provenance

Describe how the carrier labels execution truth and evidence.

Required answers:

- How are dry-run, local, mock, external, and live modes labeled?
- How are evidence summaries separated from execution receipts?
- What artifact paths or validation receipts can reviewers inspect?
- Which non-claims must appear in summaries?

Evidence / links:

-

Blockers:

-

## Replayability and validation commands

Required local/public-safe validation commands:

```bash
python scripts/run_security_contract_validation.py --include-pytest
```

Before publication:

```bash
python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix
```

Carrier-specific tests to add before implementation merge:

-
-
-

Validation blockers:

-

## Rollback and stop conditions

Describe when the carrier work must pause or roll back.

Required stop conditions:

- scope ambiguity;
- missing policy decision;
- missing approved execution spec;
- unredacted secret/operator state risk;
- command authority ambiguity;
- dry-run/live truth ambiguity;
- repeated validation failure;
- channel leakage risk;
- budget/risk stop-loss trigger;
- reviewer checklist owner rejects the packet.

Proposal-specific stop conditions:

-
-

Rollback plan:

-

## Public/private output boundary

Describe what can be published and what must remain private.

Public-safe outputs:

-

Private/operator-only outputs:

-

Never publish:

- credentials, tokens, cookies, auth headers;
- private operator memory/persona/bootstrap files;
- raw runtime state/logs unless explicitly sanitized and reviewed;
- live target artifacts without explicit scope and publication review;
- unredacted command output containing secrets or private paths.

## Reviewer checklist

Reviewer checklist owner must confirm:

- `[ ]` Scope UX is explicit and bounded.
- `[ ]` Secrets/redaction plan is adequate.
- `[ ]` Command authority boundary is deterministic.
- `[ ]` Required contracts are listed with schema/reference links.
- `[ ]` Policy/tool allowlist behavior is clear.
- `[ ]` Dry-run/live truth cannot be confused.
- `[ ]` Evidence provenance and non-claims are preserved.
- `[ ]` Replay/validation path is defined.
- `[ ]` Rollback and stop conditions are defined.
- `[ ]` Public/private output boundary is safe.
- `[ ]` Carrier order remains OpenClaw first, MCP later, A2A last/example-first unless explicitly re-scoped.

Reviewer notes:

-

Decision:

- `[ ]` Approved for implementation planning
- `[ ]` Rejected
- `[ ]` Owner approval required

Reason:

-
