# RAVENCLAW

[![pytest](https://github.com/rozmiarD/ravenclaw/actions/workflows/pytest.yml/badge.svg)](https://github.com/rozmiarD/ravenclaw/actions/workflows/pytest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Ravenclaw 0.10.0](https://img.shields.io/badge/version-0.10.0-blueviolet.svg)](pyproject.toml)
[![SCLite 0.2.1](https://img.shields.io/badge/SCLite-0.2.1-blueviolet.svg)](https://github.com/rozmiarD/SCLite)

**RAVENCLAW is a governance-first security research runtime for bounded, auditable security operations.**

Project owner: **Krzysztof Probola**.

It is built around a simple idea:
advanced autonomy is only useful when it remains bounded, observable, and accountable.

## What Ravenclaw does

Ravenclaw is a multi-layer runtime for running security workflows under explicit governance.
It combines:
- deterministic planning and runtime contracts
- policy and approval gates before execution
- constrained execution through a dedicated execution engine
- artifact analysis and evidence-oriented qualification
- operator-facing visibility through Logdash

The goal is not maximum automation.
The goal is reliable autonomy under governance.

The public repository should be read as a **public core** of that system:
a publishable runtime/control-plane artifact with explicit governance and validation surfaces, not a claim that every private operator integration is bundled here.

## What makes it different

Ravenclaw is not an unconstrained offensive automation system.
Its core design claim is narrower:
- planning, authorization, execution, and interpretation are separated
- policy is enforced in runtime paths, not only described in prompts or docs
- operator approval remains explicit for sensitive actions
- evidence quality and replayability matter as much as action generation

In short, Ravenclaw optimizes for useful actions that stay within policy, scope, and review boundaries.

Ravenclaw now consumes **GovEngine** for reusable governed-execution helpers and **SCLite** for contract lifecycle artifacts.

The current reusable direction is a small **Security Contract Layer** backed by Ravenclaw Runtime artifacts: scope binding, policy decisions, prepared/approved execution specs, execution receipts, evidence summaries, and runtime truth. The reusable contract core is now the standalone `sclite` package/repo, while Ravenclaw consumes it as the governed reference runtime. OpenClaw, MCP, and A2A are potential later carriers for these contracts, not new protocols Ravenclaw is trying to own.

## Safe quickstart

The current official public-safe path is local and dry-run oriented.

Recommended order:
1. `INSTALL.md`
2. `ENVIRONMENT_SUPPORT.md`
3. `DEMO.md`
4. `VALIDATION.md` / `PROOF_OF_VALUE.md`
5. `QUALITY_SIGNALS.md`
6. `PUBLIC_STATUS.md`
7. `AUDIENCE.md`
8. `DOCS_MAP.md`
9. `PUBLISHING.md`
10. `ARCHITECTURE_OVERVIEW.md`

This path is intentionally narrow and honest.
It shows the governed flow with a small one-command demo entrypoint (`bin/demo`), a shared bootstrap path (`scripts/bootstrap_public_demo.sh`), and an explicit `RAVENCLAW_MODE=demo` delivery profile, without pretending the repo already has a polished one-command public deployment story.

## Architecture at a glance

High-level governed flow:

`scope/input -> planner -> policy gate / auditor -> approved execution spec -> execution engine -> analysis -> operator visibility`

Main runtime layers:
- **Planner**: turns scope and operator input into structured campaign/runtime intent
- **Policy gate / Auditor**: enforces scope, tool, auth, and aggression rules before execution
- **Execution engine**: the only layer allowed to build and run final commands
- **Analysis / qualification**: turns raw artifacts into bounded findings and summaries
- **Logdash**: operator-facing control plane for visibility, control, and state truth

See `ARCHITECTURE_OVERVIEW.md` for the short version and `ARCHITECTURE.md` for the deeper map.

## Public maturity and status

Ravenclaw is not a flat-maturity repository.
Some parts are stable enough to be treated as strong public reference surfaces, while others remain experimental or local/internal.

Use `PUBLIC_STATUS.md` as the canonical public maturity guide.
For public proof and trust surfaces, use `VALIDATION.md`, `QUALITY_SIGNALS.md`, and `references/public-safe-proof-walkthrough.md`.
For the public-core/private-overlay split, read `references/public-core-private-overlay-boundary.md`.
For trusted-core authority boundaries, failure modes, and non-guarantees, read `THREAT_MODEL.md`.
For the emerging contract layer, read `SECURITY_CONTRACT_LAYER.md` and `references/approved-execution-spec-v0.1.md`.
For Logdash operator-facing control/recovery semantics, see `references/logdash-operator-truth-contracts.md`.

## Install and run posture

Fastest public-safe start:

```bash
./scripts/bootstrap_public_demo.sh demo
```

Reusable public demo bundle:

```bash
./scripts/bootstrap_public_demo.sh bundle
```

For containerized public-demo bring-up, see `.devcontainer/` and `compose.demo.yaml`.


Today, the repo is strongest as:
- a governance-first runtime architecture
- a research platform with real control and policy surfaces
- a codebase that can be inspected seriously

It now has an official public-safe local dry-run path, but it is not yet in its final lowest-friction form.
That remaining gap is real and still an active priority.

## Who this is for

Ravenclaw is best suited to technically serious readers who care about:
- governance-first security automation
- policy-gated execution
- operator-visible control and recovery
- contract-oriented runtime design
- evidence and replayability

If you want a clearer fit/non-fit guide, read `AUDIENCE.md`.

## Limits and non-goals

Ravenclaw is **not**:
- an unconstrained offensive automation platform
- an opaque autonomous attacker
- a replacement for operator judgment
- a guarantee of security outcomes
- a polished consumer product
- a beginner-first security starter kit

It is intended for authorized security research and controlled environments.
Its value depends on bounded behavior, explicit governance, and operator visibility.

## Why this project exists

Many autonomous security systems have a hard tradeoff:
- rigid systems can be safe but not useful enough;
- unconstrained systems can act quickly but are hard to trust.

Ravenclaw separates proposal, approval, execution, and review so adaptive parts can help without owning final authority.

For the short public thesis, read `WHY_RAVENCLAW.md`.

## Repository guide

Main areas:
- `engine/` - planning, runtime orchestration, policy, execution, qualification, evaluation
- `logdash/` - operator-facing dashboard and control plane
- `tests/` and `engine/tests/` - regression and contract coverage
- `references/` - short reference docs for important contracts and boundaries
- `implementation-plans/` - bounded plans for meaningful repo/runtime improvement waves

## Release and public-release framing

Version milestones are tracked in `VERSION_ROADMAP.md`.
High-level open-source/public-release direction is tracked in `OPEN_SOURCE_1_0_PLAN.md`.

Current public truth:
- the technical core is strong and serious
- the public repo is best understood as a governance-first public core, not a full private operator environment
- the public repo shape is improving, but is still being refined
- public clarity, demo usability, and proof surfaces are better than before, but remain active work

## Documentation map

For intent-based navigation, use `DOCS_MAP.md`.
For final publication workflow, use `PUBLISHING.md`.

## Deeper reading

If you want more depth, read in this order:
1. `PUBLIC_STATUS.md`
2. `AUDIENCE.md`
3. `QUALITY_SIGNALS.md`
4. `VALIDATION.md`
5. `DOCS_MAP.md`
6. `ARCHITECTURE_OVERVIEW.md`
7. `WHY_RAVENCLAW.md`
8. `ARCHITECTURE.md`
9. `STATE_FILES.md`
10. `OPEN_SOURCE_1_0_PLAN.md`

Ravenclaw should be understood as intelligence under governance: adaptive enough to be useful, bounded enough to remain inspectable and trustworthy.
