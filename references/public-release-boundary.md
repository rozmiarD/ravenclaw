# Public release boundary

This document defines the current boundary for preparing a public/open-source Ravenclaw release.

## Goal
Publish a coherent governance-first research platform without accidentally shipping private deployment state, sensitive runtime artifacts, or environment-specific local residue.

## Default publication rule
Treat the current workspace as a mixed internal working tree, not as an automatically publishable repository snapshot.
A public release should be assembled deliberately.

## Safe-to-publish by default
These areas are generally candidates for public release, subject to normal review:
- core source code under `engine/` and `logdash/`
- top-level architecture and usage docs
- policy/config examples that do not contain secrets or environment-specific values
- shared references explaining contracts, ownership, and operator-facing behavior
- tests that do not embed private deployment data

## Review-before-publish areas
These paths require explicit review before public release because they may contain local state, generated artifacts, internal notes, or deployment-specific history:
- `reports/`
- `memory/`
- `logs/`
- `pending/`
- `tmp/`
- `state/`
- workspace/operator-specific notes and bootstrap files

## Publication cautions
Before publishing, explicitly check for:
- credentials, tokens, cookies, and approval artifacts
- local runtime state or host-state snapshots
- private target data, campaign notes, or deployment-specific identifiers
- internal-only planning notes that describe non-public operational intent
- generated archives or findings bundles that were useful locally but are not appropriate for the public repo

## Recommended release posture
The safest near-term public story is:
- governance-first research platform
- bounded operator control and inspectability
- deliberate open-core/public-shell release posture
- private or sensitive deployment residue excluded from the public repository

## Rule for future prep waves
If a future public-release prep wave changes this boundary, update:
- this document
- `OPEN_SOURCE_1_0_PLAN.md`
- `README.md` if the public-facing story changes materially
