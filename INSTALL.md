# INSTALL.md

This file describes the current public install posture for Ravenclaw.

## Supported public posture

The current supported public path is a **local, dry-run oriented setup**.
It is designed to let a public reader inspect the governed flow safely without requiring a full offensive toolchain or a live operator environment.
This is a public-core path, not a claim that the repository contains the operator's full private overlay.

This is the official Wave B position for now.

## Minimum environment

Required:
- Python 3.11+
- `pip`
- ability to create a local virtual environment

Minimal Python dependencies:
- `PyYAML>=6,<7`
- `Flask>=3,<4` for Logdash
- `pytest>=8,<9` if you want test validation

## Recommended install

Fastest supported path from the repository root:

```bash
./scripts/bootstrap_public_demo.sh install
```

Quick readiness check after install:

```bash
./scripts/bootstrap_public_demo.sh doctor
```

Manual equivalent:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

If editable install is not suitable in your environment, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install PyYAML "Flask>=3,<4" "pytest>=8,<9"
```

## What this gives you

This setup is enough to:
- read and validate the code/doc surfaces
- run the planner entrypoint locally
- run the governed pipeline in dry-run mode
- start Logdash locally
- execute focused tests
- use the public bootstrap/devcontainer/compose demo path

## What it does not assume

This public install path does **not** assume:
- a full bug bounty or offensive CLI stack
- a production operator environment
- live credentials or campaign secrets
- a public-ready autonomous execution setup

## Container/devcontainer option

The repo now also includes:
- `.devcontainer/` for devcontainer/Codespaces-style bring-up
- `compose.demo.yaml` for reproducible local demo/logdash startup
- `demo/` + `bin/demo-bundle` / `./scripts/bootstrap_public_demo.sh bundle` for generated public demo artifacts

These reuse the same public-safe bootstrap script instead of introducing a separate hidden setup path.

## Recommended next reads

After install, continue with:
1. `ENVIRONMENT_SUPPORT.md`
2. `DEMO.md`
3. `PUBLIC_STATUS.md`
4. `references/public-core-private-overlay-boundary.md`

## Current truth

Ravenclaw is strongest today as a serious local research/runtime codebase with a safe dry-run path.
That is the current public install story.
A more polished zero-friction path may come later, but it should not be claimed before it is real.