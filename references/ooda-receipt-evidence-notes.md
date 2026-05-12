# OODA Receipt and Evidence Notes

This note documents how Ravenclaw should carry GovEngine OODA safety decisions into receipt/evidence surfaces without publishing raw output.

## Purpose

GovEngine OODA decisions are governance/control evidence. They describe why a host runner continued, paused, aborted, cooled down, degraded to dry-run, required owner review, or replanned after a step.

They are not vulnerability evidence and are not a raw telemetry publication channel.

## Allowed public receipt shape

A public-safe receipt may include a compact control decision entry such as:

```json
{
  "decision": "cooldown",
  "reason_code": "host_health_transport_noise",
  "interrupting": true,
  "step_index": 1,
  "observation_kinds": ["before_step"],
  "orientation_summary": {
    "scope_ok": true,
    "policy_ok": true,
    "ticket_ok": true,
    "spec_ok": true,
    "host_health": "transport_noise",
    "output_shape": "expected",
    "operator_control": "run",
    "budget_state": "ok"
  }
}
```

Allowed fields:

- decision and reason code;
- interrupting/non-interrupting flag;
- bounded step index or safe step identifier;
- observation kinds/severities, not raw observations;
- summary orientation booleans/enums;
- redacted or public-safe cooldown subject;
- links or descriptors for approved specs, tickets, execution contracts, receipts, and evidence artifacts.

## Fields that must stay out

OODA receipt/evidence artifacts must not include:

- raw stdout/stderr;
- raw command logs;
- request/response bodies;
- credentials, cookies, bearer tokens, private headers, or private paths;
- unredacted private/live target identifiers;
- full host telemetry dumps;
- LLM private reasoning, prompts, or hidden chain-of-thought.

## Runtime behavior contract

Before scheduling the next approved-spec runner step, a Ravenclaw host adapter should evaluate GovEngine OODA control.

- `continue`: proceed according to the approved runner request.
- `replan_after_step`: stop the linear runner path and return to host planning policy.
- `pause`: stop scheduling and preserve a pause reason.
- `abort`: stop scheduling and preserve an abort reason.
- `cooldown`: stop scheduling and let host cooldown policy update host state.
- `degrade_to_dry_run`: prevent live/local execution escalation and preserve dry-run truth.
- `require_owner_review`: stop scheduling until explicit owner review.

## Evidence semantics

Evidence summaries may claim:

- OODA control was evaluated before or between runner steps;
- an interrupting decision stopped or reshaped execution;
- the decision is linked to the approved execution shape and receipt.

Evidence summaries must not claim:

- live vulnerability evidence;
- successful exploitation;
- authorization to exceed approved scope;
- that raw telemetry is public-safe.

## Current validation

Ravenclaw has a focused host-runner seam test:

- `engine/tests/test_govengine_ooda_adapter.py`

It proves a Ravenclaw adapter can honor GovEngine OODA `pause`, `abort`, and `cooldown` decisions between approved-spec runner steps while keeping live subprocess ownership in Ravenclaw.

## Integration status

Current status: contract/documentation, adapter seam test, and compact receipt/evidence projection are complete for public-safe Ravenclaw proof artifacts.

Implemented projection:

- `engine/ooda_receipts.py` compacts GovEngine OODA decision dictionaries into public-safe summaries.
- `engine/security_contract_layer.py` adds compact `control_decisions` to v0.1 and v0.2 execution receipts when a pipeline/runner receipt supplies OODA decisions.
- Evidence bundle/contract builders record OODA decisions as governance evidence only, not vulnerability evidence.
- `engine/tests/test_security_contract_layer_wrapper.py` covers redaction of raw observation detail/facts while preserving decision, reason, interrupting state, step index, and orientation summary.

Future work may wire more live-runtime sources into the same projection path, but the public artifact boundary is now explicit.
