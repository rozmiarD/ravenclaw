# INSTALL.md

This file describes the current public install posture for Ravenclaw.

## Supported public posture

The current supported public path is a **local, dry-run oriented setup**.
It is designed to let a public reader inspect the governed flow safely without requiring a full offensive toolchain or a live operator environment.
This is a public-core path, not a claim that the repository contains the operator's full private overlay.

This is the current public position.

## Minimum environment

Required:
- Python 3.11+
- `pip`
- ability to create a local virtual environment

Runtime Python dependencies:
- `PyYAML>=6,<7`
- `sclite-core>=1.0.1,<1.1` (PyPI distribution; Python import package `sclite`)
- `govengine>=0.12.2a0,<0.13` (published neutral-only GovEngine 0.12.2 alpha line)

Dev/test dependencies:
- `pytest>=8,<9` for tests and `--include-pytest` validation receipts
- `Flask>=3,<4` for Logdash and public demo/dev paths

## Recommended install

Fastest supported path from the repository root:

```bash
./scripts/bootstrap_public_demo.sh install
```

Quick readiness check after install:

```bash
./scripts/bootstrap_public_demo.sh doctor
```

Manual runtime-only install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/validate_public_install.py
```

PyPI package install for the public contract/profile helpers:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ravenclaw-security==0.18.3
python - <<'PY'
import ravenclaw
from ravenclaw.security_profile import security_profile_manifest
print(ravenclaw.__version__)
print(security_profile_manifest()["profile"]["name"])
PY
```

The `0.18.2` wheel is intentionally a narrow public contract/profile package.
Use the repository install path above for the full source/reference runtime,
demo scripts, Logdash, and validation fixtures.

Manual dev/test install for validation, demos, Logdash, and pytest:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/validate_public_install.py --dev
```

For release-readiness checks, prefer a disposable clean virtual environment so
`pip check` is scoped to Ravenclaw's dependency chain rather than any unrelated
packages installed in the operator's global interpreter:

```bash
python scripts/validate_clean_public_install.py \
  --venv /tmp/ravenclaw-clean-public-install \
  --dev
```

For read-only checkouts or external runtime state, set
`RAVENCLAW_REPORTS_DIR=/path/to/reports`, `RAVENCLAW_TMP_DIR=/path/to/tmp`, and
`RAVENCLAW_LOGDASH_DB=/path/to/logs.db` before running the full test suite or
Logdash. Set `RAVENCLAW_PIPELINE_CONFIG=/path/to/pipeline_config.json` when
pipeline configuration should also be written outside the checkout.

If editable install is not suitable in your environment, install the same explicit package dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install PyYAML "sclite-core>=1.0.1,<1.1" "govengine>=0.12.2a0,<0.13"
python scripts/validate_public_install.py
```

For the equivalent explicit dev/test dependency set:

```bash
pip install PyYAML "Flask>=3,<4" "pytest>=8,<9" \
  "sclite-core>=1.0.1,<1.1" "govengine>=0.12.2a0,<0.13"
python scripts/validate_public_install.py --dev
```

## What this gives you

This setup is enough to:
- read and validate the code and documentation surfaces;
- run the planner entrypoint locally;
- run the governed pipeline in dry-run mode;
- start Logdash locally for public-demo inspection;
- validate runtime and dev/test dependency readiness;
- execute focused tests;
- use the public bootstrap, devcontainer, and compose demo paths.

## What it does not assume

This public install path does **not** assume or provide:
- a full bug bounty or offensive CLI stack;
- a production operator environment;
- live credentials or campaign secrets;
- authorization for live target testing;
- autonomous live execution that is ready for public use.

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

Ravenclaw is strongest today as a local research/runtime codebase with a safe dry-run path.
That is the current public install story.
An easier install path may come later, but the docs should not claim it before it exists.
