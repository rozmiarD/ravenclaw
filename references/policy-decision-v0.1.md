# PolicyDecision v0.1

## Purpose

`PolicyDecision` records the policy gate's decision before runtime proceeds toward preparation/approval/execution.

In v0.1 this is a compatibility artifact around the legacy `{pass, reason}` result. It makes the decision public-stable enough for demo proof traces while preserving old runtime callers.

## Producer

Current producer:
- `normalize_policy_decision_v0(...)` in `govengine.policy.gateway`

Public demo bundle producer path:
- `build_policy_decision_artifact(...)` in `engine/public_demo_bundle.py`

## Schema

Schema file:
- `schemas/policy_decision.v0.1.schema.json`

Schema version:

```json
"schema_version": "2026-04-27.policy-decision.v0.1"
```

## Required fields

Top-level required fields:
- `schema_version`
- `decision`
- `reason_code`
- `reasons`
- `scope_facts`
- `tool_facts`
- `approval_required`
- `constraints`
- `redaction_required`
- `compatibility`

Decision values:
- `allow_prepare`
- `owner_approval_required`
- `deny`

## Compatibility

The `compatibility` object preserves the legacy shape:

```json
{
  "pass": true,
  "reason": "demo_scope_target_override"
}
```

This lets newer proof artifacts expose structured policy truth without forcing a full pipeline migration in the same wave.

## Public safety notes

Public examples should avoid raw credentials, private targets, and local operator state. `redaction_required` should normally remain `true` for public proof bundles.
