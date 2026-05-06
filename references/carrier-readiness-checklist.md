# Carrier Readiness Checklist

Status: pre-implementation gate for future OpenClaw/MCP/A2A carrier work.

Use this checklist before any carrier/adapter implementation. It is intentionally conservative: Security Contract Layer proof stability comes first, adapters come later.

## Scope and authority

- [ ] The carrier has explicit operator scope for the target use case.
- [ ] The carrier does not authorize live target execution by default.
- [ ] Dry-run/local-public-safe behavior is the default for demos and public artifacts.
- [ ] Out-of-scope or missing-scope requests pause for operator review.

## Contract stability

- [ ] The carrier maps to the canonical trace:
  `scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence summary`.
- [ ] Referenced schemas are stable enough for a carrier boundary.
- [ ] Fixture validation passes against committed public-safe examples.
- [ ] Any schema or artifact-shape change is treated as contract work, not docs-only work.

## Redaction and leakage controls

- [ ] Redaction happens before conversational/public display.
- [ ] Private workspace paths, raw runtime artifacts, cookies, tokens, credentials, and local state are excluded from public output.
- [ ] Public snapshot residue audit reports `blockers=0`.
- [ ] Residue warnings have been reviewed as contextual warnings, not live secret leaks.

## Command authority

- [ ] LLMs/carriers do not construct trusted final shell commands.
- [ ] Final command/spec construction remains inside Ravenclaw-owned guarded runtime boundaries.
- [ ] Rejected policy decisions cannot be reinterpreted or downgraded by the carrier.
- [ ] Approval-required decisions preserve the operator review requirement.

## Provenance and receipts

- [ ] Execution receipts preserve runtime mode, dry-run state, return status, and provenance.
- [ ] Evidence summaries distinguish proof receipts from live vulnerability evidence.
- [ ] Public demos do not claim production readiness or live target findings.

## Validation before public push

- [ ] `python scripts/run_security_contract_validation.py --include-pytest` passes.
- [ ] Before public push, the GitHub Actions parity path passes when available:
  `python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix`.
- [ ] The public pytest slice matrix passes from the exact final public tree:
  `contracts_policy`, `auto_campaign`, `runtime_core`, `runtime_runner`, `logdash`, `misc_public`.
- [ ] Fixture validation and residue audit pass on the final clean publish tree.

## Stop conditions

Stop before implementation or publication if:

- live target execution would be introduced;
- adapter work would bypass existing runtime policy gates;
- redaction cannot be proven before display;
- validation receipts fail;
- public docs would imply Ravenclaw has a general protocol replacement or live vulnerability evidence when it does not.
