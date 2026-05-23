# SecurityContractValidationReceipt v0.1

## Purpose

`SecurityContractValidationReceipt` records the result of Ravenclaw's local/public-safe Security Contract validation runner.

It answers a narrow question:

> Did the requested public-safe validation surfaces validate, and which checks produced that answer?

The receipt is intended to be machine-readable enough for CI, publication prep, and later adapter surfaces while staying clear about its authority boundaries.

## Producer

Current producer:

- `scripts/run_security_contract_validation.py`

Schema:

- `schemas/security_contract_validation_receipt.v0.1.schema.json`

Artifact type:

```json
"artifact_type": "security_contract_validation_receipt"
```

Schema version:

```json
"schema_version": "v0.1"
```

## Checks represented

The default runner covers:

- committed legacy Security Contract proof fixture validation;
- current lifecycle/review-bundle public demo smoke from a disposable public snapshot;
- current Ravenclaw/GovEngine/SCLite demo scenario with versions taken from the modules actually executed;
- temporary public snapshot assembly;
- snapshot-local fixture validation;
- public snapshot residue audit.

With `--include-pytest`, it also runs focused Security Contract/public snapshot pytest checks from a disposable public snapshot.

## Required top-level fields

- `artifact_type`
- `schema_version`
- `schema_ref`
- `generated_at`
- `status`
- `scope`
- `validated_trace`
- `checks_requested`
- `checks_passed`
- `checks_failed`
- `checks`
- `summary`

## Public-safety scope

The receipt must state these non-authorizations explicitly:

```json
{
  "mode": "local_public_safe_validation",
  "live_target_execution": false,
  "protocol_adapter_work": false,
  "public_push": false
}
```

This makes the receipt useful as evidence of validation without implying permission to run live target tests, start protocol adapter work, or publish.

## Semantics

A `passed` receipt means all checks that actually ran completed with return code `0`.

`validated_trace` names the retained v0.1 compatibility fixture validated by
`fixture_validation`; it is not a claim that the active demo emits that trace.
The current scoped-ticket lifecycle/review-bundle path is covered by
`demo_bundle_smoke` and `demo_scenario_package_chain` when demo-runtime checks
are enabled.

A `failed` receipt may be partial: the runner stops after the first failed check and emits the checks completed up to that point.

`checks_requested` records the intended check set. `checks_passed`, `checks_failed`, `checks`, and `summary` record the observed outcome.

## Non-claims

A valid receipt does not claim:

- live vulnerability evidence;
- live target testing;
- production deployment readiness;
- absence of every possible private residue pattern;
- approval to push to a public remote;
- implementation of OpenClaw, MCP, or A2A adapters.

It is a validation receipt for the narrow Security Contract proof path.
