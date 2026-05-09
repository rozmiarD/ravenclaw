# Public-safe proof walkthrough

This walkthrough shows how to inspect Ravenclaw's public proof path without live target testing, private operator state, command transcripts, session material, or credentials.

It is a reviewer aid, not a new execution mode.

## Claim

Ravenclaw can produce and validate a local, dry-run, public-safe governance trace:

```text
scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence summary
```

The newer SCLite lifecycle fixture expresses the same direction as a hash-linked contract chain:

```text
intent_contract -> policy_decision -> execution_contract -> execution_ticket -> execution_receipt -> evidence_contract -> artifact_chain_manifest
```

## What to inspect

Start with these committed fixtures and references:

- `examples/security-contract-proof/` — legacy v0.1 proof trace fixture.
- `examples/contract-lifecycle-v0.2/` — SCLite v0.2 lifecycle-chain fixture.
- `examples/replayable-truth-runtime/` — offline replayability/truth fixture.
- `examples/scope-fidelity-report/` — public-safe scope fidelity examples.
- `references/execution-receipt-v0.1.md` — receipt semantics and non-claims.
- `references/evidence-bundle-v0.1.md` — evidence summary boundaries.
- `references/ooda-receipt-evidence-notes.md` — how OODA decisions are recorded without leaking raw output.
- `references/security-contract-validation-receipt-v0.1.md` — validation receipt shape.

## Commands

After installing dev/test dependencies from `INSTALL.md`, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_security_contract_fixtures.py examples/security-contract-proof
sclite validate-chain examples/contract-lifecycle-v0.2/artifact_chain_manifest.json
sclite verify-lifecycle examples/contract-lifecycle-v0.2/artifact_chain_manifest.json
python scripts/run_security_contract_validation.py --include-pytest
```

For a publication-style scaffold, assemble a disposable snapshot and validate that exact tree:

```bash
scripts/assemble_public_snapshot.sh /tmp/ravenclaw-public-snapshot-review
python scripts/audit_public_snapshot_residue.py /tmp/ravenclaw-public-snapshot-review
python scripts/build_public_snapshot_manifest.py /tmp/ravenclaw-public-snapshot-review --check
```

Expected outcomes:

- fixture validation passes;
- SCLite lifecycle validation passes;
- residue audit has `blockers=0`;
- validation receipt reports `status: passed`;
- focused public-safe pytest slice passes when `--include-pytest` is used.

## Public-safety boundaries

This proof path intentionally does **not** include or claim:

- live vulnerability evidence;
- live target execution;
- authorization to test any target;
- raw command transcript publication;
- private operator memory, pending queues, logs, Logdash databases, credentials, session material, or API tokens;
- production deployment readiness;
- OpenClaw, MCP, or A2A carrier implementation completeness.

## Why this matters

The point is not to show that Ravenclaw can run arbitrary actions.
The point is to show that Ravenclaw's public core has inspectable governance artifacts, local validation commands, and explicit non-claims.

A reviewer should be able to answer:

1. What scope/input was represented?
2. What policy decision was made?
3. What execution shape was prepared and approved?
4. Was execution represented as dry-run/public-safe?
5. What evidence summary was produced?
6. What was deliberately excluded from the public artifact?

If those questions are not answerable from the fixture and validation receipt, the proof path needs improvement before stronger public claims are made.
