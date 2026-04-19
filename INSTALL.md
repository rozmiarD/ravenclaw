# INSTALL.md

This file describes the current public install posture for Ravenclaw.

## Supported public posture

The current supported public path is a **local, dry-run oriented setup**.
It is designed to let a public reader inspect the governed flow safely without requiring a full offensive toolchain or a live operator environment.

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

From the repository root:

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

## What it does not assume

This public install path does **not** assume:
- a full bug bounty or offensive CLI stack
- a production operator environment
- live credentials or campaign secrets
- a public-ready autonomous execution setup

## Recommended next reads

After install, continue with:
1. `ENVIRONMENT_SUPPORT.md`
2. `DEMO.md`
3. `PUBLIC_STATUS.md`

## Current truth

Ravenclaw is strongest today as a serious local research/runtime codebase with a safe dry-run path.
That is the current public install story.
A more polished zero-friction path may come later, but it should not be claimed before it is real.