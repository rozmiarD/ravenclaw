# Security Contract Proof Fixture

This directory contains a minimal public-safe Security Contract Layer proof trace generated from Ravenclaw demo mode.

Proof trace:

`scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence bundle/summary`

## Files

- `policy_decision.json` — schema-backed PolicyDecision v0.1 compatibility artifact.
- `prepared_execution_spec.redacted.json` — redacted prepared spec for public/auditor review.
- `approved_execution_spec.json` — schema-backed ApprovedExecutionSpec v0.1 artifact.
- `execution_receipt.json` — schema-backed public-safe dry-run execution receipt.
- `evidence_bundle.json` — schema-backed public-safe dry-run evidence bundle.
- `evidence_summary.md` — human-readable evidence summary and non-claims.

## Public-safety constraints

This fixture is demo/local/dry-run only. It uses `example.com`, includes no live vulnerability evidence, and must not contain credentials, private workspace paths, raw stdout/stderr, or private operator state.

## Validation

Run:

```bash
python scripts/validate_security_contract_fixtures.py examples/security-contract-proof
```

The validator checks the schema-backed artifacts, Security Contract Layer public invariants, and a small sanitization denylist.
