# DOCS_MAP.md

This file is the shortest navigation map for the public Ravenclaw repo.
Use it when you want to know where to start without reading everything.

## If you are new here

Start with:
1. `README.md`
2. `DEMO.md`
3. `PUBLIC_STATUS.md`
4. `QUALITY_SIGNALS.md`
5. `PROOF_OF_VALUE.md`

That gives you the project shape, the safe public demo path, the maturity truth, and the proof surface.

## If you want to validate the repo

Start with:
1. `PUBLIC_STATUS.md`
2. `REVIEWER_VALIDATION_GUIDE.md`
3. `INSTALL.md`
4. `VALIDATION.md`
5. `QUALITY_SIGNALS.md`
6. `scripts/validate_public_install.py`
7. `.github/workflows/pytest.yml`
8. `tests/test_logdash_smoke.py`

Use this path to separate current claims from checks that can be run locally.

## If you want the shortest architecture understanding

Start with:
1. `ARCHITECTURE_OVERVIEW.md`
2. `WHY_RAVENCLAW.md`
3. `ARCHITECTURE.md`
4. `STATE_FILES.md`

## If you want governance and contract depth

Start with:
1. `THREAT_MODEL.md`
2. `SECURITY_CONTRACT_LAYER.md`
3. `references/approved-execution-spec-v0.1.md`
4. `references/runtime-task-contract-v2.md`
5. `references/planner-runtime-contract-map.md`
6. `references/logdash-operator-truth-contracts.md`
7. `references/evaluation-replay-contract.md`
8. `references/effectiveness-metrics-contract.md`
9. `references/openclaw-adapter-contract-map.md`
10. `references/carrier-readiness-checklist.md`
11. `references/carrier-readiness-packet-template.md`

## If you want proof-of-value context

Start with:
1. `PROOF_OF_VALUE.md`
2. `references/public-safe-proof-walkthrough.md`
3. `QUALITY_SIGNALS.md`
4. `REVIEWER_VALIDATION_GUIDE.md`
5. `SECURITY_CONTRACT_LAYER.md`

## If you want public-release context

Start with:
1. `references/repository-publication-readiness-2026-05-08.md`
2. `OPEN_SOURCE_1_0_PLAN.md`
3. `PUBLISHING.md`
4. `references/public-release-boundary.md`
5. `references/public-release-review-matrix.md`

## If you want the older public-release context map

Start with:
1. `references/public-core-private-overlay-boundary.md`
2. `OPEN_SOURCE_1_0_PLAN.md`
3. `references/public-release-boundary.md`
4. `references/public-release-review-matrix.md`
5. `references/public-snapshot-plan.md`

## If you want to understand fit and expectations

Start with:
1. `AUDIENCE.md`
2. `PUBLIC_STATUS.md`
3. `WHY_RAVENCLAW.md`
4. `references/public-core-private-overlay-boundary.md`

## If you want the contract proof direction

Start with:
1. `references/public-safe-proof-walkthrough.md`
2. `SECURITY_CONTRACT_LAYER.md`
3. `schemas/approved_execution_spec.v0.1.schema.json`
4. `references/approved-execution-spec-v0.1.md`
5. `examples/security-contract-proof/`
6. `examples/contract-lifecycle-v0.2/`
7. `DEMO.md`

This direction keeps Ravenclaw Runtime as the proof/reference implementation, consumes SCLite as the reusable contract-core dependency, and treats OpenClaw, MCP, and A2A as later carriers, not new protocols. For the first future carrier boundary, read `references/openclaw-adapter-contract-map.md`; before implementation planning, use `references/carrier-readiness-checklist.md` and fill `references/carrier-readiness-packet-template.md`.

## If you want contributor / publication workflow

Start with:
1. `REPO_WORKFLOW.md`
2. `PUBLISHING.md`
3. `CONTRIBUTING.md`
4. `VALIDATION.md`

This path covers Git identity, clean worktrees, branch cleanup, public snapshot publication, and validation expectations.

## Short rule

Do not treat every file as equally important.
Ravenclaw makes more sense when read through a deliberate path instead of as a raw directory tree.