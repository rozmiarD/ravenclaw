# ApprovedExecutionSpec v0.1

## Purpose

`ApprovedExecutionSpec` is Ravenclaw's first schema-stabilization target for the Security Contract Layer.

It captures the execution shape that has passed policy/auditor review and can be handed to the controlled execution engine. It is not a raw model-generated command and not a permission bypass.

## Producer

Current producer:
- `build_approved_execution_spec(...)` in `engine/execution_contracts.py`

The producer starts from `PreparedExecutionSpec`, adds approval metadata, adds execution-truth summaries, and sets:

```json
"spec_version": "2026-03-18.approved.v1"
```

## Consumer

Current primary consumer:
- `ExecutionEngine.execute_approved_spec(...)` in `engine/executor.py`

The executor consumes the approved spec, re-normalizes/checks tool and arguments, preserves scope controls, and can return a dry-run receipt.

## Schema

Schema file:
- `schemas/approved_execution_spec.v0.1.schema.json`

The v0.1 schema intentionally covers the runtime-critical and public-stable subset, not every internal field.

## Required fields

Top-level required fields:
- `spec_version`
- `target`
- `target_host`
- `target_in_scope`
- `resolved_tool`
- `normalized_args`
- `execution_plan`
- `scope_facts`
- `approval`
- `execution_truth`

Required approval fields:
- `decision`
- `reason`
- `reason_code`
- `constraints`
- `approval_source`
- `owner_override_applied`
- `approval_transform_chain`

Required execution-truth fields:
- `artifact_type`
- `resolved_tool`
- `normalized_args`
- `execution_plan`
- `command_preview`
- `command_input_summary`
- `execution_input_summaries`
- `target_host_match_status`
- `request_shape_hygiene_status`

## Example lifecycle

1. Planner/runtime proposes an action under scope.
2. Policy gate checks action/tool/scope/credential constraints.
3. Runtime builds `PreparedExecutionSpec`.
4. Auditor or local demo adapter approves or rejects the prepared spec.
5. Runtime builds `ApprovedExecutionSpec`.
6. Executor consumes the approved spec and produces an execution receipt or dry-run receipt.
7. Public demo bundle may emit a sanitized approved spec as part of the proof trace.

## Redaction notes

The schema does not require raw secrets, credential values, cookies, private output paths, or sensitive stdout/stderr.

Public-facing examples must be sanitized before publication:
- redact cookies and auth values;
- redact campaign/operator header values when appropriate;
- redact private local paths;
- prefer redacted prepared specs for auditor/public review;
- keep execution receipts compact and dry-run/local for public demo bundles.

## Compatibility notes

This is a v0.1 public-stable subset. The current runtime may include additional fields, and the schema allows additional properties to avoid blocking internal evolution.

Breaking future changes should either:
- introduce a new schema file/version, or
- keep the v0.1 subset valid for existing public demo artifacts.

The schema is validated by focused tests against live/generated specs from `build_approved_execution_spec(...)`.
