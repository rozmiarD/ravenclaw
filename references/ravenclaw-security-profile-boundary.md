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
- the active security policy/scope gateway in
  `engine/security_policy_gateway.py`, using Ravenclaw scope state.
- active security action/tooling helpers in `engine/security_action_*`,
  `engine/security_tool_registry.py`, `engine/security_policy_core.py`,
  `engine/security_capability_recipes.py`, and
  `engine/security_semantic_loss_policy.py`.
- active security review interpretation in `engine/security_signal_contract.py`,
  `engine/security_analysis_contract.py`, and
  `engine/security_evidence_policy.py`.

GovEngine owns reusable governed-runtime mechanics:

- kernel boundary report and public surface registry;
- runtime shell, planning, admission, runner supervision, and evidence-review
  validators;
- neutral boundary/runtime proof surfaces. The retired optional
  `govengine.security_profile` helper facade is tolerated on the current
  published compatibility line but is not Ravenclaw runtime authority.

`govengine.action_*`, `govengine.tool_registry`, `govengine.policy.core`,
`govengine.semantic_loss_policy`, `govengine.policy.gateway`,
`govengine.contracts.signal`, `govengine.contracts.analysis`, and
`govengine.contracts.evidence_policy` remain part of that optional published
compatibility facade, but Ravenclaw no longer uses them as active runtime
authority. Neutral receipt-bounded `govengine.review` remains in use through
`engine/govengine_review_projection.py`.

SCLite owns:

- lifecycle schemas and validation;
- artifact-chain verification;
- review-bundle validation and verdict authority.

## Current package chain

```text
Ravenclaw source/reference runtime
  -> govengine>=0.11.0a0,<0.12
  -> sclite-core>=0.8.0a0,<0.9
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

OpenClaw remains the first future carrier candidate. The current 0.18 boundary
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

Current readiness-contract docs:

- `references/openclaw-redaction-output-matrix.md`
- `references/openclaw-approval-ux-sketch.md`

MCP stays later and policy-gated. A2A stays last or example-first.

## Validation

Focused profile validation:

```bash
python -m pytest -q engine/tests/test_ravenclaw_security_profile.py
python -m pytest -q engine/tests/test_openclaw_adapter_readiness.py
```

Public install validation also checks this profile boundary:

```bash
python scripts/validate_public_install.py --dev
```
