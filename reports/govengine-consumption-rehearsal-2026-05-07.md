# GovEngine Consumption Rehearsal Report — 2026-05-07

Status: completed locally; no remote created; no push performed.
Ravenclaw migration branch before rehearsal: `3fb30bd docs: record GovEngine dedicated repo scaffold`.
Ravenclaw migration branch fix commit: `ccf71e4 fix: support external GovEngine consumption`.
Standalone GovEngine repo path: `/home/probo/.openclaw/worktrees/govengine-standalone`.
Standalone GovEngine repo commits used:

- `aa461b0 chore: scaffold GovEngine standalone repo`
- `ba707ba fix: detect standalone GovEngine repo root`

Consumption rehearsal tree: `/home/probo/.openclaw/worktrees/ravenclaw-consume-govengine-rehearsal`.

## Objective

Prove Ravenclaw can consume the dedicated local standalone GovEngine package without an in-tree `govengine/` directory, before any remote creation or subprocess execution migration.

## Rehearsal setup

Created a disposable Ravenclaw rehearsal tree from the migration branch:

```bash
git archive --format=tar HEAD | tar -x -C /home/probo/.openclaw/worktrees/ravenclaw-consume-govengine-rehearsal
rm -rf /home/probo/.openclaw/worktrees/ravenclaw-consume-govengine-rehearsal/govengine
```

Adjusted the rehearsal `pyproject.toml` so Ravenclaw no longer packages in-tree GovEngine:

```toml
[tool.setuptools]
packages = []
py-modules = []
```

Installed local standalone GovEngine as an editable dependency in the rehearsal venv:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,logdash]'
.venv/bin/python -m pip uninstall -y govengine
.venv/bin/python -m pip install --no-deps -e /home/probo/.openclaw/worktrees/govengine-standalone
```

Verified import source:

```text
govengine_import_path=/home/probo/.openclaw/worktrees/govengine-standalone/govengine/__init__.py
```

## Findings and fixes

### 1. Standalone repo-root discovery bug

Initial consumption exposed a real split bug: `govengine.context.discover_repo_root()` only recognized Ravenclaw-style roots with both `pyproject.toml` and `engine/`.

In a standalone GovEngine repo, this caused the package root to resolve incorrectly and added `govengine/` itself to `sys.path`, allowing top-level imports such as `tool_registry` to bypass Ravenclaw compatibility wrappers.

Fix applied in both:

- Ravenclaw migration branch: `ccf71e4 fix: support external GovEngine consumption`
- standalone GovEngine repo: `ba707ba fix: detect standalone GovEngine repo root`

New root rule: discover a root with `pyproject.toml` plus either `engine/` or `govengine/`.

### 2. Consumption-mode test assumption

`engine/tests/test_govengine_dependency_isolation.py` assumed `REPO_ROOT/govengine` always exists. That is true for package-in-place migration, but false after split.

Fix: the test now copies in-tree `govengine/` when present, otherwise it imports `govengine` and copies the installed package source path. This makes the test useful in both package-in-place and external-consumption modes.

### 3. Local path dependency is not publish-safe

A first broad validation attempt failed snapshot residue audit because rehearsal `pyproject.toml` used an absolute local path dependency:

```text
BLOCKER absolute_home_path pyproject.toml
```

This confirms local path dependencies must never enter a public snapshot.

For the public-safety validation pass, the rehearsal tree used a public-safe placeholder dependency string:

```toml
govengine @ git+https://github.com/rozmiarD/GovEngine.git@LOCAL_REHEARSAL_PLACEHOLDER
```

The actual test environment still consumed local GovEngine through editable install in the venv.

## Validation

Focused consumption gate after fixes:

```bash
.venv/bin/python -m pytest -q \
  engine/tests/test_govengine_dependency_isolation.py \
  engine/tests/test_govengine_stage2b_seams.py \
  engine/tests/test_govengine_policy_seam.py \
  engine/tests/test_govengine_command_shape_seam.py \
  engine/tests/test_govengine_runner_seam.py \
  engine/tests/test_executor_v2.py
```

Result: passed.

Security Contract receipt in consumption tree:

```bash
.venv/bin/python scripts/run_security_contract_validation.py --include-pytest --format markdown
```

Result: `status: passed`.

Full Ravenclaw slice matrix in consumption tree:

```bash
for slice in contracts_policy auto_campaign runtime_core runtime_runner logdash misc_public; do
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_pytest_slice.py "$slice"
done
.venv/bin/sclite verify-lifecycle examples/contract-lifecycle-v0.2/artifact_chain_manifest.json
```

Result:

- all requested slices passed;
- SCLite lifecycle verification passed:
  `lifecycle_ok:6:ddb006900727142b8095e918a93f3dba484d3820b66fff813c169c3b16c6b295`.

Focused source-branch regression gate for the committed fix:

```bash
/tmp/ravenclaw-docs-venv/bin/python -m pytest -q \
  engine/tests/test_govengine_dependency_isolation.py \
  engine/tests/test_govengine_stage2b_seams.py \
  engine/tests/test_govengine_policy_seam.py
```

Result: passed.

## Current readiness

Ready:

- Ravenclaw can consume local standalone GovEngine without in-tree `govengine/`;
- compatibility wrappers remain valid in consumption mode;
- full Ravenclaw validation passes in the external-consumption rehearsal tree;
- local path dependency residue risk is identified and documented;
- no remote or push side effects occurred.

Still pending:

- choose real GovEngine remote URL/name/visibility;
- replace placeholder dependency with real git/package dependency before publishable Ravenclaw branch;
- decide whether to push standalone GovEngine first, then update Ravenclaw to consume that remote dependency;
- do not move subprocess execution until after remote/CI boundary is stable.

## Recommended next action

Create the real GovEngine remote only after operator chooses visibility/name. Then:

1. push `/home/probo/.openclaw/worktrees/govengine-standalone` to that remote;
2. replace Ravenclaw placeholder dependency with the real GovEngine git pin;
3. rerun the same consumption validation against the real remote dependency;
4. only then consider live execution backend migration.
