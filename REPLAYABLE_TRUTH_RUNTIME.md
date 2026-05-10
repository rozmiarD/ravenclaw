# REPLAYABLE_TRUTH_RUNTIME.md

## Status

Draft v0.1 public proof direction. This is a Ravenclaw Runtime capability, not a separate product package yet.

## What it is

Replayable Truth Runtime is Ravenclaw's ability to preserve enough governed runtime truth to replay security-agent decisions offline.

It complements the Security Contract Layer:

- **Security Contract Layer** defines the portable artifacts: scope, policy, approved execution spec, receipt, evidence, validation receipt.
- **Replayable Truth Runtime** consumes persisted runtime artifacts and recomputes governance-aware outcomes without live target execution by default.

In short:

```text
security contract artifacts + runtime lineage -> deterministic replay result -> governance-aware metrics
```

## Why it matters

AI-assisted cyber systems need more than model transcripts. They need a flight recorder:

- what task and scope the agent believed it was acting under;
- what policy/auditor/execution state constrained the action;
- what signal/evidence contracts were observed;
- whether a decision was productive, blocked, divergent, partial, contaminated, or excluded from metrics;
- whether a later evaluation can happen without touching live targets again.

This is the core safety and evaluation value: Ravenclaw can separate **decision evaluation** from **live execution**.

## Public-safe proof fixture

A committed public-safe fixture lives at:

- `examples/replayable-truth-runtime/replay_bundle.json`
- `examples/replayable-truth-runtime/replay_result.json`

Validate it with:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_replayable_truth_fixture.py examples/replayable-truth-runtime
```

The fixture uses only `example.com` demo targets, includes no credentials/cookies/raw live output, and does not claim a live vulnerability.

## Current implementation surfaces

Primary code:

- `engine/evaluation_bundle.py` — builds and validates replay bundles.
- `engine/evaluation_replay.py` — replays decision bundles and datasets.
- `engine/evaluation_metrics.py` — aggregates governance-aware effectiveness metrics.
- `engine/evaluation_variants.py` — tracks replay/metric variants.
- `engine/evaluation_fixtures.py` — fixture helpers.

Primary references:

- `references/evaluation-replay-contract.md`
- `references/effectiveness-metrics-contract.md`
- `references/runtime-task-contract-v2.md`
- `references/planner-runtime-contract-map.md`

Validation:

- `tests/test_replayable_truth_fixture.py`
- `engine/tests/test_evaluation_replay.py`
- `scripts/validate_replayable_truth_fixture.py`
- `scripts/run_security_contract_validation.py --include-pytest`

## Relationship to Security Contract Layer

Security Contract Layer is the public contract surface. Replayable Truth Runtime is the reference runtime/evaluation engine that proves those contracts are useful beyond documentation.

The current public claim is therefore:

> Ravenclaw provides a governed replay layer for reviewing AI-assisted security decisions.

## Non-claims

Replayable Truth Runtime does not claim:

- live vulnerability evidence;
- execution simulation for arbitrary tools;
- permission to test targets outside scope;
- readiness for every production deployment;
- replacement for OpenClaw, MCP, A2A, SIEM, or scanner ecosystems.

It is a safety and evaluation layer for preserving and replaying governed security-agent decisions.

## Near-term roadmap

1. Keep public replay fixtures synthetic, deterministic, and public-safe.
2. Keep replay downstream of canonical runtime truth; do not create a parallel semantic model.
3. Tie replay outputs to Security Contract Layer artifacts and validation receipts.
4. Add small benchmark-style evidence/qualification fixtures only after the replay proof remains stable.
5. Treat adapters as carriers later, not as the core innovation.
