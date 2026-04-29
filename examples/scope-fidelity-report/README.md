# Scope Fidelity Report Examples

These fixtures demonstrate Ravenclaw's schema-backed Scope Fidelity report without live target execution.

Cases:
- `exact.json` — all detected request-shape hosts match the target host, so the verdict is `pass`.
- `cross_host_mismatch.json` — args/execution-plan structure contains hosts that differ from the target host, so the verdict is `fail`.
- `ambiguous.json` — no host is detected in the request shape, so the verdict is `review`.

Validate locally:

```bash
python scripts/validate_scope_fidelity_fixtures.py examples/scope-fidelity-report
```

Build a report from a local prepared/approved spec JSON:

```bash
python scripts/build_scope_fidelity_report.py --spec examples/security-contract-proof/approved_execution_spec.json
```

Public-safety boundary:
- no live target execution;
- no protocol adapter work;
- no raw stdout/stderr;
- no credential material.
