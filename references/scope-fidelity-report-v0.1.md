# Scope Fidelity Report v0.1

## Purpose

`scope_fidelity_report` is a small Security Contract Layer artifact for target-binding and request-shape hygiene checks.

It answers a narrow question: do the hosts embedded in a proposed/approved request shape match the intended target host, or does the structure contain hidden/mixed out-of-scope hosts?

It does **not** execute against live targets and does **not** claim vulnerability evidence.

## Producer

Current producers:
- `build_scope_fidelity_report(...)` in `engine/security_contract_layer.py`
- `scripts/build_scope_fidelity_report.py` for local JSON specs or manual CLI args

The producer wraps Ravenclaw's existing request-shape host extraction logic and emits a public-safe JSON artifact.

## Schema

Schema file:
- `schemas/scope_fidelity_report.v0.1.schema.json`

## Verdicts

- `pass` — detected hosts match the target host.
- `review` — no host was detected in the request shape, so the binding is ambiguous.
- `fail` — at least one detected host does not match the target host.

## CLI usage

The command below exercises the retained static scope-fidelity helper with
local public-safe arguments; it does not define Ravenclaw's current generated
lifecycle/review proof path.

```bash
python scripts/build_scope_fidelity_report.py --target https://example.com --arg https://example.com/login --target-in-scope
```

The CLI reads only local JSON and emits a schema-validated `scope_fidelity_report`. It accepts prepared/approved-spec-like objects containing `target`, `normalized_args` or `args`, and `execution_plan` or `tool_chain`.

For CI/preflight use, add `--fail-on fail` to return exit code `2` only for cross-host mismatch, or `--fail-on review` to return exit code `2` for ambiguous or failed binding.

## Public-safety boundary

The report is deterministic and local-only:
- no live target execution;
- no protocol adapter work;
- no raw stdout/stderr;
- no secrets or raw credential values required.

## Why this matters

Scope fidelity is one of Ravenclaw's most legible reusable contract surfaces. A small report can catch cross-host drift in arguments, stdin, or request headers before execution, which is more valuable than merely documenting that scope matters.
