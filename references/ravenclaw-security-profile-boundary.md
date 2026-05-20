# Ravenclaw Security Profile Boundary

## Status

Ravenclaw is the security-research runtime/profile over GovEngine and SCLite.
This boundary is profile metadata and validation guidance, not a package split,
not an adapter implementation, and not a live-execution claim.

Machine-readable profile metadata is exposed by
`engine/ravenclaw_security_profile.py`.

## Ownership

Ravenclaw owns:

- security-research runtime/profile semantics;
- finding taxonomy and report language;
- scope and policy interpretation for the Ravenclaw domain;
- Logdash/operator visibility;
- public demo and snapshot projection;
- host-side projection adapters into GovEngine contracts.

GovEngine owns reusable governed-runtime mechanics:

- kernel boundary report and public surface registry;
- runtime shell, planning, admission, runner supervision, and evidence-review
  validators;
- optional `govengine.security_profile` helper facade.

SCLite owns:

- lifecycle schemas and validation;
- artifact-chain verification;
- review-bundle validation and verdict authority.

## Current package chain

```text
Ravenclaw source/reference runtime
  -> govengine>=0.7.0,<0.8
  -> sclite-core>=0.5.1,<0.6
```

## Profile non-claims

This profile boundary does not:

- make Ravenclaw own GovEngine kernel APIs;
- make Ravenclaw own SCLite schemas or review-bundle verdict authority;
- implement OpenClaw, MCP, or A2A adapters;
- authorize live target execution;
- claim production deployment readiness;
- move credentials, key stores, carrier protocols, or raw runtime storage into
  the public profile.

## Adapter-readiness gate

OpenClaw remains the first future carrier candidate. The current 0.16 boundary
requires an adapter-readiness packet, not adapter implementation. The active
packet is:

```text
references/openclaw-adapter-readiness-packet-2026-05-20.md
```

Required gates before implementation:

- scope UX;
- redaction;
- command authority;
- lifecycle artifacts;
- rollback;
- public/private boundary.

MCP stays later and policy-gated. A2A stays last or example-first.

## Validation

Focused profile validation:

```bash
python -m pytest -q engine/tests/test_ravenclaw_security_profile.py
```

Public install validation also checks this profile boundary:

```bash
python scripts/validate_public_install.py --dev
```
