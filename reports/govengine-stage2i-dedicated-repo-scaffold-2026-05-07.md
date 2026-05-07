# GovEngine Stage 2I Dedicated Repo Scaffold Report — 2026-05-07

Status: completed locally; no remote created; no push performed.
Ravenclaw migration branch at start: `7ad135c docs: rehearse standalone GovEngine scaffold`.
Dedicated local repo path: `/home/probo/.openclaw/worktrees/govengine-standalone`.
Dedicated local repo branch: `main`.
Dedicated local repo commit: `aa461b0 chore: scaffold GovEngine standalone repo`.

## Objective

Create a dedicated local GovEngine repository scaffold outside Ravenclaw with real package metadata, API-boundary docs, focused tests, and CI, while keeping subprocess execution and Ravenclaw runtime ownership out of GovEngine.

## Created repository contents

Top-level scaffold:

- `README.md`
- `LICENSE`
- `pyproject.toml`
- `.gitignore`
- `.github/workflows/pytest.yml`
- `docs/API_BOUNDARY.md`
- `docs/VALIDATION.md`
- `tests/test_standalone_smoke.py`
- `tests/test_execution_helpers.py`
- `govengine/` package copied from the Stage 2G migration branch

## Package metadata

The standalone `pyproject.toml` declares:

- package name: `govengine`
- version: `0.0.0`
- Python: `>=3.11`
- dependencies:
  - `PyYAML>=6,<7`
  - `sclite @ git+https://github.com/rozmiarD/SCLite.git@43dae49b44602da76611fb42cd0b10aac3b3ae3f`
- dev dependency: `pytest>=8,<9`
- package data: `govengine = ["*.yaml"]`

This preserves the intended dependency direction:

```text
Ravenclaw -> GovEngine -> SCLite
```

## API boundary docs

`docs/API_BOUNDARY.md` defines GovEngine-owned areas:

- action schema/validators/compiler;
- capability recipes;
- semantic loss policy;
- policy core/gateway helpers;
- execution contracts;
- approved-spec/ticket/command-shape/dry-run helpers;
- neutral scope and JSON state primitives;
- explicit SCLite integration seams.

It explicitly excludes:

- Logdash;
- Ravenclaw public snapshot/publishing scripts;
- OpenClaw session wiring;
- LLM/provider/persona configuration;
- MCP/A2A/protocol adapters;
- Ravenclaw campaign UX;
- live subprocess execution backend for now.

## CI scaffold

Added `.github/workflows/pytest.yml` with Python `3.11` and `3.12` matrix:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Validation performed

In `/home/probo/.openclaw/worktrees/govengine-standalone`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

Results:

- pytest: `5 passed`
- pip check: `No broken requirements found.`

Additional dependency hygiene probe:

- scanned `govengine/**/*.py` for forbidden Ravenclaw helper imports such as `campaign_utils`, `json_state_io`, and `paths`;
- result: `no_forbidden_ravenclaw_imports`.

Git/remotes:

- repo initialized locally on `main`;
- no remote configured;
- no push performed.

## Important implementation note

The first test run caught two incorrect scaffold tests rather than package issues:

- `validate_approved_execution_spec(...)` returns the `execution_truth` envelope, not the outer approved spec;
- `validate_execution_ticket_gate(...)` raises `missing_execution_ticket` when called directly without a ticket.

Tests were corrected before amending the local scaffold commit.

## Current readiness

Ready now:

- dedicated local repo exists and installs editable;
- standalone package imports and focused helpers pass;
- explicit API boundary and non-ownership docs exist;
- CI shape exists;
- no remote/push side effects.

Still pending before public/private remote creation:

- decide repository name/visibility/remote owner;
- decide whether to keep SCLite as git-pinned dependency or migrate to a release/package source;
- add public-facing status/security/contributing docs if publishing publicly;
- decide which Ravenclaw focused tests should be ported permanently into GovEngine;
- decide whether the Ravenclaw migration branch should consume GovEngine via path/git dependency or remain package-in-place for one more stabilization wave.

## Recommended next action

Before any subprocess migration, choose one of these:

1. **Remote-prep path**: polish standalone repo docs/tests and prepare a private/public remote, still without moving execution backend.
2. **Consumption path**: update Ravenclaw migration branch to consume the local standalone GovEngine via editable/path dependency and run full Ravenclaw validation.

Recommendation: do consumption path first. It proves the repo split does not break Ravenclaw before publishing or moving live execution mechanics.
