# Post-Proof Roadmap Reassessment — 2026-05-01

## Trigger

GitHub Actions is green for `0fa41f1`, closing the current Security Contract Layer / public proof / proof-of-value fixture sequence.

## Current state

The public proof path is now materially stronger than at the start of the sequence:

- CI drift was reduced with local GitHub Actions parity validation.
- Public validation surfaces are indexed and schema-backed.
- Public snapshots have a schema-backed manifest and reviewer report output.
- A reviewer guide now gives a short public-safe validation path.
- Proof-of-value framing is explicit and avoids live exploit claims.
- A schema-backed proof-of-value scorecard exists and has a committed public-safe fixture.
- The consolidated validation runner now covers the scorecard and scorecard fixture.

## Assessment

The SCL/public-proof lane is now at a reasonable pause point.

More work is possible, but the highest-value remaining improvements are no longer basic discoverability or validation plumbing. Continuing to add more public-proof helper artifacts risks becoming documentation/validation overgrowth unless it unlocks the next carrier or review surface.

The strongest current public claim is:

> Ravenclaw is a governance-first security runtime whose public core can demonstrate scope, policy, execution, evidence, replay, snapshot review, and proof-of-value signals locally and without live target execution.

That is coherent and defensible.

## Recommended next development wave

**OpenClaw adapter-prep contract map — docs/contracts only, no adapter implementation yet.**

Purpose:

- Define how the existing Security Contract Layer would be carried by a future OpenClaw Skill or plugin.
- Map public artifacts to adapter responsibilities without building the adapter yet.
- Keep OpenClaw as the first future carrier, consistent with the standing roadmap.
- Preserve the rule that adapters follow stable contracts instead of leading the architecture.

Bounded output:

- `references/openclaw-adapter-contract-map.md`
- optional focused test ensuring the map preserves non-claims and references required SCL artifacts
- small docs link from `SECURITY_CONTRACT_LAYER.md` or `DOCS_MAP.md`

Must not do:

- no OpenClaw runtime integration;
- no MCP/A2A implementation;
- no live target execution;
- no new protocol claims;
- no credentials, operator state, or private workspace assumptions.

Why this is the right next step:

- The proof surfaces are now stable enough to describe carrier responsibilities.
- OpenClaw is the planned first adapter/carrier later.
- A contract map is reversible, low-risk, and clarifies future implementation without prematurely building it.

## Alternatives considered

### More benchmark artifacts

Possible next artifact: a richer benchmark report or scorecard fixture variants.

Rejected for now because the current proof-of-value scorecard already gives a machine-readable baseline. More variants would likely be incremental unless tied to a concrete external benchmark goal.

### Runtime hardening

Always valuable, but this sequence has been public-proof focused. Jumping back into runtime now would mix lanes. Better to first record how the public contract layer would be carried forward.

### MCP/A2A prep

Rejected for now. Standing roadmap says OpenClaw first, MCP later, A2A last/example-first.

## Validation posture before next wave

Before implementing the next wave:

```bash
python scripts/run_security_contract_validation.py --include-pytest
```

Before publishing it:

```bash
python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix
```

## Recommended [NEXT]

1. Push/publish only when a local wave is complete and parity receipt is green.
2. Next non-push development step: implement the **OpenClaw adapter-prep contract map** as docs/contracts-only groundwork.
