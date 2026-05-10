# ENVIRONMENT_SUPPORT.md

This file defines the current environment support truth for the public Ravenclaw repo.

## Minimum supported environment

Supported for public orientation and safe dry-run work:
- Linux environment
- Python 3.11+
- local virtualenv
- repository checked out locally

This is the narrowest environment Ravenclaw currently supports well in public form.

## Recommended environment

Recommended for the current public path:
- Linux workstation or VM
- Python 3.11+
- virtualenv-based local install
- ability to run Flask locally for Logdash
- ability to run local pytest slices

Equivalent supported convenience paths now include:
- `./scripts/bootstrap_public_demo.sh install`
- `./scripts/bootstrap_public_demo.sh bundle`
- `.devcontainer/` for devcontainer/Codespaces-style bring-up
- `compose.demo.yaml` for reproducible public demo startup

## Optional tooling

Some parts of the repository refer to broader runtime/offensive toolchains.
Those are **not required** for the current public-safe demo path.

Treat such tooling as optional or advanced until explicit public guidance says otherwise.

## Unsupported or not-yet-first-class public combinations

The following should not currently be assumed as first-class public support:
- full production Docker deployment
- full public autonomous runtime deployment
- public cloud deployment story
- zero-config offensive toolchain setup
- polished cross-platform support guarantees

## Support boundary

Public readers should assume:
- local inspection is supported;
- local dry-run flow is supported;
- local Logdash bring-up is supported for public-demo inspection;
- generated public demo artifacts are supported via the same demo contract;
- devcontainer/compose demo bootstrap is supported for the public-safe path;
- live target operation, cloud deployment, and production deployment need separate review.

## Why this file exists

Ravenclaw has more runtime depth than its current public install path exposes.
This file exists to keep the support claim honest.