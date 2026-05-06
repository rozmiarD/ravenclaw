# Security Contract Layer Evidence Summary

- proof_mode: `dry_run_contract_proof`
- target_host: `example.com`
- dry_run: `true`
- evidence_items: `5`

## Evidence criteria

- `met` — policy_decision_recorded: A policy decision artifact exists before approval. Source: `policy_decision.json`. Observed: `allow_prepare`.
- `met` — prepared_spec_recorded: A prepared execution spec artifact exists for review. Source: `prepared_execution_spec.redacted.json`. Observed: `synthetic_public_fixture`.
- `met` — approved_spec_recorded: An approved execution spec exists before execution receipt creation. Source: `approved_execution_spec.json`. Observed: `2026-03-18.approved.v1`.
- `met` — dry_run_receipt_recorded: The execution receipt records dry-run behavior and zero executed commands. Source: `execution_receipt.json`. Observed: `dry-run`.
- `met` — public_safe_target: The fixture target is the reserved documentation host example.com. Source: `approved_execution_spec.json`. Observed: `example.com`.

## Non-claims

- `does_not_claim_live_vulnerability_evidence`
- `does_not_execute_against_live_private_targets`
- `does_not_include_raw_stdout_stderr_or_private_paths`

This fixture is synthetic, dry-run/local, and intentionally contains no raw live-target evidence.
