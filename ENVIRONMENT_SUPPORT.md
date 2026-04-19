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

## Optional tooling

Some parts of the repository refer to broader runtime/offensive toolchains.
Those are **not required** for the current public-safe demo path.

Treat such tooling as optional or advanced until explicit public guidance says otherwise.

## Unsupported or not-yet-first-class public combinations

The following should not currently be assumed as first-class public support:
- one-command Docker deployment
- full public autonomous runtime deployment
- public cloud deployment story
- zero-config offensive toolchain setup
- polished cross-platform support guarantees

## Support boundary

Public readers should assume:
- local inspection is supported
- local dry-run flow is supported
- local Logdash bring-up is supported
- broader live-operation ergonomics remain a later maturity target

## Why this file exists

Ravenclaw has a stronger technical core than its current public install ergonomics.
This file exists to keep the support claim honest.