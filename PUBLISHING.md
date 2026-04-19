# PUBLISHING.md

This file is the short final publication checklist for Ravenclaw.
Use it before any real public GitHub push.

## Default rule

Do **not** publish directly from the live working tree.
Publish from a deliberate assembled snapshot.

Primary assembly path:
- `scripts/assemble_public_snapshot.sh`

Supporting boundary docs:
- `references/public-release-boundary.md`
- `references/public-snapshot-plan.md`
- `references/public-release-review-matrix.md`

## What should be true before a public push

### 1. Assemble the snapshot

Create a fresh public snapshot scaffold and review that output, not the live workspace.

### 2. Confirm front-door docs are present

The public-facing snapshot should include at least:
- `README.md`
- `INSTALL.md`
- `ENVIRONMENT_SUPPORT.md`
- `DEMO.md`
- `VALIDATION.md`
- `QUALITY_SIGNALS.md`
- `PUBLIC_STATUS.md`
- `AUDIENCE.md`
- `DOCS_MAP.md`
- `ARCHITECTURE_OVERVIEW.md`
- `WHY_RAVENCLAW.md`
- `ARCHITECTURE.md`
- `STATE_FILES.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `CODE_OF_CONDUCT.md`

### 3. Confirm excluded areas remain excluded

Do not publish mixed local/internal areas such as:
- `memory/`
- `logs/`
- `pending/`
- `tmp/`
- `state/`
- most of `reports/`
- operator/bootstrap/persona files

### 4. Review sensitive residue risk

Explicitly check for:
- tokens
- credentials
- cookies
- private targets
- live runtime/control-plane state
- internal operator notes
- deployment-specific secrets or identifiers

### 5. Review examples and placeholders

If examples are included, they should be:
- intentionally prepared
- redacted
- structurally illustrative
- not copied blindly from live state

### 6. Validate the snapshot

At minimum, run in the snapshot:

```bash
pytest -q
```

If the public demo path is meant to be advertised immediately, also walk through `DEMO.md` inside the assembled snapshot.

## Current recommendation

The safest current release posture is:
- publish a deliberate public snapshot
- keep the story architecture-first, governance-first, and honesty-first
- do not wait for perfect visual/demo polish if the goal is a serious technical public repo
- do not overclaim ease, maturity, or deployment simplicity

## Short version

Before public push:
1. assemble snapshot
2. review boundary and residue
3. verify docs are present
4. run validation
5. publish the snapshot, not the live tree