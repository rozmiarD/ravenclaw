# OpenClaw Command Authority and Rollback Tests

## Status

Contract/test surface only. This document does not implement an OpenClaw
adapter, command runner, MCP gateway, A2A profile, or live execution path.

Machine-readable checks live in `engine/openclaw_adapter_readiness.py`.

## Command authority negative rules

A future OpenClaw carrier must block execution handoff when any of these are
true:

- chat text contains a shell command or tool invocation;
- no structured policy decision is present;
- no prepared execution spec exists;
- no approved execution spec exists;
- the prepared spec is treated as the approved spec;
- runner-supervision state is missing or not ready.

Only a complete structured chain may reach Ravenclaw's execution engine:

```text
operator_scope
  -> policy_decision
  -> prepared_execution_spec
  -> approved_execution_spec
  -> runner_supervision
  -> execution_receipt
```

## Rollback and stop propagation

A future carrier must surface and preserve structured stop states:

- scope ambiguity;
- owner review required;
- pause requested;
- abort requested;
- cooldown required;
- validation failed;
- redaction failed;
- dry-run/live truth ambiguous.

Every stop state must be operator-visible, carry a structured reason, and block
execution until reviewed. Validation-failure stops must include a validation
receipt reference.

## Validation

```bash
python -m pytest -q engine/tests/test_openclaw_adapter_readiness.py
```
