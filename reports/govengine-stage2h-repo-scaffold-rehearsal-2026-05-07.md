# GovEngine Stage 2H Repo Scaffold Rehearsal Report — 2026-05-07

Status: local rehearsal only; no push performed.
Base before this wave: `be39a46 feat: isolate GovEngine package dependencies`.
Persistent Ravenclaw worktree: `/home/probo/.openclaw/worktrees/ravenclaw-govengine-plan`.
Temporary standalone scaffold: `/tmp/govengine-repo-rehearsal.pStsVl`.

## Objective

Rehearse an independent GovEngine repository shape after Stage 2G dependency isolation, without creating or pushing a real public repo.

## Scaffold contents

The temporary scaffold contains:

- `govengine/` copied from the Ravenclaw migration branch;
- `README.md` stub marking it as a local extraction-readiness scaffold;
- `LICENSE` copied from Ravenclaw;
- standalone `pyproject.toml`;
- focused `tests/test_standalone_smoke.py`.

Standalone package metadata used in rehearsal:

```toml
[project]
name = "govengine"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = [
  "PyYAML>=6,<7",
  "sclite @ git+https://github.com/rozmiarD/SCLite.git@43dae49b44602da76611fb42cd0b10aac3b3ae3f",
]

[tool.setuptools]
packages = ["govengine", "govengine.contracts", "govengine.execution", "govengine.policy"]

[tool.setuptools.package-data]
govengine = ["*.yaml"]
```

## Install/test rehearsal

Commands executed:

```bash
python3 -m venv --system-site-packages "$SCAFFOLD/.venv"
"$SCAFFOLD/.venv/bin/python" -m pip install -e "$SCAFFOLD"
cd "$SCAFFOLD"
"$SCAFFOLD/.venv/bin/python" -m pytest -q
```

Result: `3 passed`.

Focused smoke coverage:

- imports public GovEngine modules from the installed standalone scaffold;
- compiles a minimal direct action spec with `govengine.action_compiler.compile_action_spec`;
- assembles a legacy dry-run result with `govengine.execution.runner.legacy_action_spec_dry_run_result`;
- verifies local scope helpers in `govengine.scope`.

## Important dependency finding

The first rehearsal attempt intentionally used only `PyYAML` and failed because `govengine.__init__` imports `govengine.sclite_contracts`, which imports `sclite.integrity`.

Failure mode:

```text
ModuleNotFoundError: No module named 'sclite'
```

This is not a Ravenclaw dependency blocker. It confirms the intended dependency chain:

```text
Ravenclaw -> GovEngine -> SCLite
```

The scaffold passed after declaring the pinned SCLite dependency used by Ravenclaw today:

```toml
sclite @ git+https://github.com/rozmiarD/SCLite.git@43dae49b44602da76611fb42cd0b10aac3b3ae3f
```

## Current extraction readiness

GovEngine is now ready for a **controlled standalone repo rehearsal branch**, not yet for a public push as a final product.

Ready:

- package imports independently from a temp repo;
- neutral action/compiler/policy/contract/execution helper modules are package-local;
- package-local YAML data files are included;
- SCLite dependency is explicit;
- Ravenclaw compatibility wrappers remain green in the source branch.

Still not done:

- real repo metadata/docs are only stubbed;
- no CI workflow has been designed for GovEngine;
- no public README/API boundary has been written;
- live subprocess execution remains in Ravenclaw by design;
- Logdash/Ravenclaw runtime integration remains outside GovEngine by design.

## Recommended next action

Stage 2I should be **repo split preparation**, not subprocess migration:

1. create a dedicated local GovEngine repo/worktree scaffold path outside Ravenclaw;
2. copy the Stage 2H scaffold contents;
3. add real README/API boundary docs and CI;
4. add focused tests copied from Ravenclaw that are meaningful for GovEngine alone;
5. only after that, decide whether to create a private/public remote.

Subprocess execution should still wait until after the standalone repo has CI and API ownership boundaries.
