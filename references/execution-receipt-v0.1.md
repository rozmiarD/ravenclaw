# ExecutionReceipt v0.1

## Purpose

`ExecutionReceipt` records what the controlled execution path did or would have done.

For public demo bundles, v0.1 is intentionally compact and public-safe: it captures dry-run/mock execution truth, command input summaries, and counts, but does not publish raw stdout/stderr, raw command logs, credentials, or private paths.

## Producer

Current public demo producer:
- `build_execution_receipt_artifact(...)` in `engine/public_demo_bundle.py`

Runtime source data:
- `ExecutionEngine.execute_approved_spec(...)` output in `engine/executor.py`

## Schema

Schema file:
- `schemas/execution_receipt.v0.1.schema.json`

Artifact type:

```json
"artifact_type": "execution_receipt"
```

## Required fields

Top-level required fields:
- `artifact_type`
- `runtime_mode`
- `status`
- `returncode`
- `reason`
- `execution_source`
- `dry_run`
- `compiled_action`
- `command_input_summary`
- `planned_command_count`
- `executed_command_count`
- `stdout_present`
- `stderr_present`

Required command input summary fields:
- `target_delivery_mode`
- `tool`
- `stdin_present`

## Public proof semantics

In the demo proof path, a valid receipt should make these claims legible:
- execution was dry-run/mock rather than live offensive execution;
- executor handoff used an approved spec;
- command input shape was summarized;
- raw output was not published;
- planned/executed command counts are visible without exposing private command content.

## Non-claims

A public demo `ExecutionReceipt` does not claim:
- live vulnerability evidence;
- successful exploitation;
- authorization for any target outside explicit scope;
- that raw stdout/stderr is safe to publish.
