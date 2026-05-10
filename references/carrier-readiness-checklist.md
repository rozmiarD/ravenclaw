# Carrier Readiness Checklist

## Status

Docs/contracts-only readiness checklist for future carriers of Ravenclaw's Security Contract Layer.

This is **not** an implementation plan for an adapter. It is a gate list that must be satisfied before implementation starts.

## Purpose

Ravenclaw's Security Contract Layer is carrier-independent. Future OpenClaw, MCP, or A2A work should transport and present the existing governance/evidence artifacts without weakening scope, approval, command authority, or evidence provenance.

This checklist defines minimum readiness gates for any future carrier wave.

## Non-goals

This checklist does **not**:

- implement OpenClaw, MCP, A2A, or any protocol adapter;
- authorize live target execution;
- approve offensive tooling;
- claim production deployment readiness;
- claim live vulnerability discovery;
- replace the public validation runner;
- permit private operator state, credentials, memory, raw logs, or unredacted runtime artifacts in public outputs.

## Carrier order

Default order remains:

1. OpenClaw first, as the operator-facing carrier candidate.
2. MCP later, as a policy-gated tool wrapper/gateway candidate.
3. A2A last or example-first, as metadata/profile demonstration only.

Do not pivot protocol-first into MCP or A2A before the OpenClaw boundary is credible.

## Required gates

| Gate | Required evidence before implementation | Blocker if missing |
| --- | --- | --- |
| Scope UX | The carrier can display or reference explicit authorized scope before action proposal. | Operator cannot tell what authority is being used. |
| Policy decision preservation | The carrier preserves structured `PolicyDecision` status/reason/constraints instead of flattening to prose. | Approval state becomes ambiguous or unreviewable. |
| Command authority boundary | The carrier never lets LLM prose become executable authority; only Ravenclaw execution-engine-approved specs may reach execution. | Prompt text could bypass deterministic guards. |
| Prepared/approved spec separation | The carrier can show the difference between proposed/prepared/redacted specs and approved execution specs. | Reviewers cannot see where authorization changed state. |
| Secrets and redaction | The carrier has an explicit secret/redaction rule for stdin, cookies, auth headers, tokens, private paths, memory, logs, and raw runtime state. | Public/channel output could leak operator-specific data. |
| Tool allowlists | The carrier maps allowed tool classes and destructive-action restrictions to Ravenclaw policy/whitelist decisions. | Carrier could widen runtime authority by accident. |
| Dry-run/live truth | The carrier labels dry-run, local, mock, external, and live truth explicitly in user-facing output. | Dry-run receipts could be mistaken for live evidence. |
| Evidence provenance | Evidence summaries include artifact paths, source labels, and non-claims; dry-run proof stays separated from vulnerability claims. | Reviewer cannot tell what supports the conclusion. |
| Replayability | The carrier can point to a validation receipt, public-safe fixture, or replayable artifact path. | Results cannot be independently reviewed. |
| Channel leakage review | The carrier has a per-channel output policy for chat surfaces, files, embeds, attachments, and group contexts. | Sensitive details could be over-shared. |
| Stop-loss and escalation | The carrier can surface budget/risk/repeated-failure stop conditions and require operator review. | Automation may continue past governance boundaries. |
| Public non-claims | The carrier preserves Ravenclaw public non-claims in summaries and reports. | Public narrative could imply production deployment readiness or live exploit proof. |

## Minimum implementation-entry packet

Before a carrier implementation branch starts, require a short packet. Use `references/carrier-readiness-packet-template.md` and include:

1. target carrier and mode, for example `OpenClaw Skill`, `MCP gateway`, or `A2A metadata profile`;
2. explicit non-goals;
3. scope UX sketch;
4. secret/redaction handling sketch;
5. command authority boundary statement;
6. expected contract artifacts consumed and emitted;
7. validation commands;
8. rollback/stop conditions;
9. public/private output boundary;
10. reviewer checklist owner.

## OpenClaw-specific readiness notes

For OpenClaw, the first credible implementation should be a Skill or plugin that validates and presents Ravenclaw contracts. It should not begin by wiring arbitrary tool execution.

Minimum OpenClaw-specific gates:

- preserve Ravenclaw role/status language when helpful, but do not expose private prompts or operator memory;
- use OpenClaw messaging/output surfaces only after redaction decisions are made;
- treat group chats as high-leakage contexts by default;
- keep config changes and gateway restarts outside the adapter unless explicitly scoped;
- ensure any future tool invocation remains behind Ravenclaw execution-engine authority.

## MCP-specific readiness notes

For MCP, no implementation should start until the OpenClaw carrier boundary is clearer.

Minimum future gates:

- policy-gated server/tool registration;
- strict schema version negotiation;
- refusal behavior for unsupported contract versions;
- deterministic redaction before tool result exposure;
- no direct execution of model-supplied shell commands.

## A2A-specific readiness notes

For A2A, treat the work as example-first metadata/profile documentation unless explicitly re-scoped.

Minimum future gates:

- carry contract metadata without implying autonomous trust;
- preserve provenance and non-claims;
- avoid using A2A as a reason to invent a new general agent protocol.

## Validation before any implementation wave

Run the public-safe validation receipt before starting implementation:

```bash
python scripts/run_security_contract_validation.py --include-pytest
```

Before publishing carrier-related docs or adapter prep:

```bash
python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix
```

For implementation work later, add carrier-specific tests before merging and treat any weakened gate as a publication-safety regression.
