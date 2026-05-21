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

That gives you the project shape, the safe public demo path, the maturity status, and the proof surface.

## If you want to validate the repo

Start with:
1. `INSTALL.md`
2. `DEMO.md`
3. `REVIEWER_VALIDATION_GUIDE.md`
4. `VALIDATION.md`
5. `QUALITY_SIGNALS.md`
6. `PUBLIC_STATUS.md`
7. `scripts/validate_public_install.py`
8. `.github/workflows/pytest.yml`

Use this path to run the local demo scenario first, then separate current claims from checks that can be reproduced locally.

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
9. `references/ooda-receipt-evidence-notes.md`
10. `references/openclaw-adapter-contract-map.md`
11. `references/carrier-readiness-checklist.md`
12. `references/carrier-readiness-packet-template.md`
13. `references/openclaw-carrier-readiness-packet-2026-05-12.md`
14. `references/runtime-state-control-govengine-map.md`
15. `references/ravenclaw-consumer-cleanup-2026-05-12.md`

## If you want proof-of-value context

Start with:
1. `PUBLIC_STATUS.md`
2. `PROOF_OF_VALUE.md`
3. `references/public-safe-proof-walkthrough.md`
4. `QUALITY_SIGNALS.md`
5. `REVIEWER_VALIDATION_GUIDE.md`
6. `SECURITY_CONTRACT_LAYER.md`

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

## If you want the GovEngine migration roadmap

Start with:
1. `VERSION_ROADMAP.md`
2. `references/govengine-wrapper-audit.md`
3. `references/runtime-state-control-govengine-map.md`
4. `references/runtime-artifact-ownership.md`
5. `references/govengine-extraction-readiness-roadmap.md`
6. `STATE_FILES.md`

This path separates current Ravenclaw-owned runtime/control state from candidate GovEngine-compatible projections for later package work.

## If you want contributor / publication workflow

Start with:
1. `REPO_WORKFLOW.md`
2. `PUBLISHING.md`
3. `CONTRIBUTING.md`
4. `VALIDATION.md`

This path covers Git identity, clean worktrees, branch cleanup, public snapshot publication, and validation expectations.

## Short rule

Do not treat every file as equally important.
Ravenclaw is easier to review when read through a clear path instead of as a raw directory tree.
