# PUBLISHING.md

This file is the short final publication checklist for Ravenclaw.
Use it before any real public GitHub push or PyPI release.

## Identity guard

For maintainer releases/pushes performed from the operator-controlled publish tree, verify the effective repo-local Git identity:

```bash
git config --get user.name
git config --get user.email
```

Required maintainer value for this publish tree:

```text
0x505badc0de <32790662+rozmiarD@users.noreply.github.com>
```

External contributors should use their own GitHub-associated identity; this guardrail is not a contributor identity requirement.

If a clean publish tree has a stale local config such as `OpenClaw <openclaw@local>`, fix it before committing:

```bash
git config user.name '0x505badc0de'
git config user.email '32790662+rozmiarD@users.noreply.github.com'
```

Never rewrite already-published history to fix authorship, contribution graphs, cleanup, or cosmetics. Preserve history and add corrective commits instead.

## Default rule

Do **not** publish directly from the live working tree.
Publish from a deliberate assembled snapshot.

Primary assembly path:
- `scripts/assemble_public_snapshot.sh`

Supporting boundary docs:
- `references/public-release-boundary.md`
- `references/public-core-private-overlay-boundary.md`
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

The Security Contract Layer proof fixture is intentionally publishable when present:
- `examples/security-contract-proof/`
- validator: `scripts/validate_security_contract_fixtures.py`

### 6. Validate the snapshot

At minimum, run in the snapshot after a dev/test install:

```bash
python scripts/validate_public_install.py --dev
pytest -q
```

If the public demo path is meant to be advertised immediately, also walk through `DEMO.md` inside the assembled snapshot.

If the Security Contract Layer proof fixture is included, also run inside the snapshot without writing bytecode into the publish tree:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_security_contract_fixtures.py examples/security-contract-proof
```

Then run the residue audit against the exact snapshot:

```bash
python scripts/audit_public_snapshot_residue.py .
python scripts/build_public_snapshot_manifest.py . --check
```

For a consolidated local receipt before publication prep, run from the live workspace. For routine SCL/public-snapshot work, use the focused path:

```bash
python scripts/validate_public_install.py --dev
python scripts/run_security_contract_validation.py --include-pytest
```

Before every public push, use the GitHub Actions parity path so the receipt also runs the exact public pytest slice matrix from a disposable public snapshot:

```bash
python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix
```

Also reproduce the exact GitHub Actions pytest matrix from the final clean publish tree or exact public tree immediately before pushing:

```bash
for slice in contracts_policy auto_campaign runtime_core runtime_runner logdash misc_public; do
  PYTHONDONTWRITEBYTECODE=1 python scripts/run_pytest_slice.py "$slice"
done
```

This catches slice-only failures that are not covered by focused local validation. The consolidated runner uses temporary output directories and does not replace the final clean publish-tree validation steps below.

If validation is run inside a clean publish worktree, remember that pytest or demo checks may generate local runtime artifacts. Before committing that publish tree, re-apply the already validated snapshot with `rsync --delete --exclude='.git'`, then rerun fixture validation and residue audit on the exact final tree.

## Document ownership and source-of-truth map

Use the following ownership model to avoid parallel truths:

- `README.md` = canonical public front-door truth about what Ravenclaw is.
- `REPO_WORKFLOW.md` = canonical Git/worktree/branch/identity rules.
- `PUBLISHING.md` = canonical GitHub publication and branch procedure.
- `PUBLIC_STATUS.md` = canonical public maturity/status guide.
- `references/public-release-boundary.md` = canonical publication boundary and exclusion policy.
- `references/public-snapshot-plan.md` = canonical snapshot design/reference plan.
- `WORKFLOW.md` = local development workflow, not the public front-door project description.
- `SOUL.md`, `AGENTS.md`, `USER.md`, and `TOOLS.md` = local workspace-operational context, not public project truth.
- generated directories such as `public-snapshot/` are build artifacts for publication prep, not the primary documentation source of truth.

When two files appear to overlap, prefer the more specific canonical owner above and update the other file only as a pointer or short summary.

## GitHub branch and push procedure

This is the canonical GitHub publication flow unless the operator explicitly asks for a review/PR branch flow.

### Default branch rule

- The final public state belongs on `main`.
- Do **not** leave temporary helper branches on the remote by default.
- Do **not** push straight from a dirty live workspace.
- `README.md` is a shared truth document and must remain public-truth-safe both in the live workspace and in the published repo.
- Do **not** maintain separate "workspace README" and "public README" narrative variants.

### Default publish flow

1. Assemble a clean public snapshot.
2. Validate the exact snapshot that is intended for publication.
3. Create an isolated clean publish tree from that validated snapshot.
4. Confirm git identity is `0x505badc0de <32790662+rozmiarD@users.noreply.github.com>`.
5. Fetch the current `origin/main`.
6. Apply only the bounded public-release delta on top of current `origin/main`.
7. Re-run validation if the publish tree changed materially while rebasing or applying the delta.
8. Push to `origin/main`.
9. If any temporary helper branch was used during preparation, delete it from the remote after `main` is updated.

### Why this rule exists

This avoids four common publication mistakes:
- pushing private/local residue from the live tree
- any force-push or published-history rewrite
- leaving branch clutter on GitHub that does not match the intended one-branch public repo shape
- letting the live workspace and public repo drift into different README-level stories about what Ravenclaw is

### If `origin/main` moved while preparing the release

If `origin/main` changed after the snapshot was validated:
- do **not** force-push the prepared snapshot branch onto `main`
- fetch the current `origin/main`
- apply the bounded public delta on top of that latest `main`
- validate again
- then push normally

### When a temporary remote branch is allowed

A temporary remote branch is allowed only if the operator explicitly wants one of these:
- review via PR
- side-by-side approval before updating `main`
- collaboration that requires a visible intermediate branch

If that is not explicitly requested, publish directly to `main` through the clean publish-tree procedure.

### Force-push rule

Do **not** force-push to `main` or rewrite already-published history.
Normal case: preserve remote history and apply the public-release delta on top of current `origin/main`.

## Current recommendation

The safest current release posture is:
- publish a deliberate public snapshot
- land the final public state on `main`
- use a clean publish tree, not the mixed live workspace
- keep the public explanation architecture-first, governance-first, and accurate
- do not wait for perfect visual/demo polish if the goal is a useful technical public repo
- do not overclaim ease, maturity, or deployment simplicity

## PyPI release procedure

Ravenclaw's first PyPI line is `ravenclaw-security` `0.16.x`, importing as
`ravenclaw`. It is intentionally pre-1.0 and packages the public
profile/readiness helper API, not the complete source runtime runner.

Before uploading:

1. Keep `pyproject.toml`, `README.md`, `INSTALL.md`, `PUBLIC_STATUS.md`,
   `VALIDATION.md`, `VERSION_ROADMAP.md`, `PUBLISHING.md`, and `CHANGELOG.md`
   aligned with the exact version.
2. Run focused package tests:

```bash
python -m pytest -q tests/test_ravenclaw_package.py engine/tests/test_ravenclaw_security_profile.py engine/tests/test_openclaw_adapter_readiness.py
```

3. Run public install validation and the structural Security Contract receipt:

```bash
python scripts/validate_public_install.py --dev
python scripts/run_security_contract_validation.py --structural-only --include-pytest
```

4. Build and check distributions:

```bash
python -m build
python -m twine check dist/*
```

5. Test a clean wheel install and verify:

```bash
python -m venv /tmp/ravenclaw-wheel-venv
/tmp/ravenclaw-wheel-venv/bin/python -m pip install dist/ravenclaw_security-0.16.1-py3-none-any.whl
/tmp/ravenclaw-wheel-venv/bin/python -m pip check
/tmp/ravenclaw-wheel-venv/bin/python - <<'PY'
import importlib.metadata as metadata
import ravenclaw
from ravenclaw.security_profile import security_profile_manifest
print(metadata.version("ravenclaw-security"))
print(ravenclaw.__version__)
print(security_profile_manifest()["profile"]["name"])
PY
```

6. Commit, push, create an annotated version tag, then upload only with
   operator approval and configured PyPI credentials.

Never print, inspect, or commit PyPI credentials.

## Short version

Before public push:
1. assemble snapshot
2. review boundary and residue
3. verify docs are present
4. run validation
5. verify Git identity
6. apply the bounded publish state onto current `origin/main`
7. push to `main`
8. remove any temporary remote branch if one was used only during preparation
