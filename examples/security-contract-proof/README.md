# Security Contract Layer proof fixture

This directory contains a clean synthetic v0.1 proof trace:

1. `policy_decision.json`
2. `prepared_execution_spec.redacted.json`
3. `approved_execution_spec.json`
4. `execution_receipt.json`
5. `evidence_bundle.json`
6. `evidence_summary.md`

The fixture uses the reserved documentation host `example.com`, dry-run semantics, and synthetic metadata. It is authored as public-safe data from the start; it is not a redacted export from a private runtime.

Validate it with:

```bash
python -m sclite.cli validate examples/security-contract-proof
```

Non-claims:

- no live vulnerability evidence;
- no private target execution;
- no raw stdout/stderr;
- no credentials, cookies, tokens, operator state, or private local paths.
