# Scope Fidelity Report v0.1

## Purpose

`scope_fidelity_report` is a small Security Contract Layer artifact for target-binding and request-shape hygiene checks.

It answers a narrow question: do the hosts embedded in a proposed/approved request shape match the intended target host, or does the structure contain hidden/mixed out-of-scope hosts?

It does **not** execute against live targets and does **not** claim vulnerability evidence.

## Producer

Current producer:
- `build_scope_fidelity_report(...)` in `engine/security_contract_layer.py`

The producer wraps Ravenclaw's existing request-shape host extraction logic and emits a public-safe JSON artifact.

## Schema

Schema file:
- `schemas/scope_fidelity_report.v0.1.schema.json`

## Verdicts

- `pass` — detected hosts match the target host.
- `review` — no host was detected in the request shape, so the binding is ambiguous.
- `fail` — at least one detected host does not match the target host.

## Public-safety boundary

The report is deterministic and local-only:
- no live target execution;
- no protocol adapter work;
- no raw stdout/stderr;
- no secrets or raw credential values required.

## Why this matters

Scope fidelity is one of Ravenclaw's most legible reusable contract surfaces. A small report can catch cross-host drift in arguments, stdin, or request headers before execution, which is more valuable than merely documenting that scope matters.
