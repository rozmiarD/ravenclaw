# OpenClaw Approval UX Sketch

## Status

Readiness sketch only. This document does not implement an OpenClaw Skill,
plugin, MCP gateway, A2A profile, command runner, or live execution path.

Machine-readable approval-UX helpers live in
`engine/openclaw_adapter_readiness.py`.

## Required order

A future OpenClaw carrier must preserve this authority sequence:

1. Show scope before action.
2. Show structured policy decision.
3. Show prepared execution spec as proposal, not execution authority.
4. Show approved execution spec as the execution-engine boundary.
5. Show runner-supervision state.
6. Show dry-run/live truth from the receipt.
7. Show evidence review and non-claims.
8. Require operator confirmation for sensitive actions.

The prepared spec must never be shown as if it were approved. Chat/model prose
must never become executable command authority.

## Artifact mapping

| UX step | Required artifact | Authority boundary |
| --- | --- | --- |
| Show scope before action | `scope/input` | Operator scope |
| Show policy decision | `PolicyDecision` | Ravenclaw policy/auditor |
| Show prepared spec as proposal | `PreparedExecutionSpec` | Proposal only |
| Show approved spec as authority | `ApprovedExecutionSpec` | Execution-engine input |
| Show runner-supervision state | GovEngine supervision plan/lease/receipt | GovEngine runner-supervision |
| Show dry-run/live truth | `ExecutionReceipt` | Receipt truth label |
| Show evidence review and non-claims | GovEngine evidence qualification/review result | Evidence review, not live-vulnerability proof |
| Require operator confirmation | `ApprovalRequest` | Operator confirmation |

## Stop conditions

Pause future adapter work if any of these are ambiguous:

- scope;
- policy decision;
- prepared-vs-approved spec boundary;
- command authority;
- redaction;
- dry-run/live truth;
- evidence non-claims;
- rollback/stop-loss.

## Validation

```bash
python -m pytest -q engine/tests/test_openclaw_adapter_readiness.py
```
