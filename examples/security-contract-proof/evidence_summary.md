# Ravenclaw Demo Evidence Summary

- final_status: `warning`
- reason_code: `pipeline_warning`
- success_status: `dry_run_contract_proof`
- success_met: `True`
- evidence_gap: `live_target_evidence_not_collected_by_design`
- evidence_items: `6`

## Evidence criteria

- `met` — demo_runtime_mode: Demo bundle was generated in demo mode. Source: `run_pipeline.demo.json`. Observed: `demo`.
- `met` — policy_decision_recorded: Policy gate decision was captured as a contract artifact. Source: `policy_decision.json`. Observed: `demo_scope_target_override`.
- `met` — prepared_spec_redacted: Prepared execution spec can be redacted for public/auditor review. Source: `prepared_execution_spec.redacted.json`.
- `met` — approved_spec_recorded: Approved execution spec was produced before executor handoff. Source: `approved_execution_spec.json`. Observed: `2026-03-18.approved.v1`.
- `met` — dry_run_receipt_recorded: Execution receipt records dry-run/mock execution instead of live offensive execution. Source: `execution_receipt.json`. Observed: `dry-run`.
- `met` — public_safe_target: Public demo target remains example.com/local-safe. Source: `approved_execution_spec.json`. Observed: `example.com`.

## Non-claims

- `does_not_claim_live_vulnerability_evidence`
- `does_not_execute_against_live_private_targets`
- `does_not_include_raw_stdout_stderr_or_private_paths`

This public demo bundle is dry-run/local and intentionally does not include raw live-target evidence.
