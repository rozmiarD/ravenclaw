# PUBLIC_STATUS.md

This file is the shortest public maturity guide for Ravenclaw.
Use it when deciding what to rely on, what to treat as evolving, and what not to assume from the public repo alone.

## Stable and recommended

These areas are currently the strongest public reference surfaces:
- governance-first architecture and role separation
- runtime policy and approval posture
- execution-engine-first command construction model
- major architecture and state-file documentation
- substantial regression and contract-test coverage
- bounded public snapshot assembly path
- the explicit public-core/private-overlay boundary model
- the emerging Security Contract Layer direction, as a contract/schema layer backed by Ravenclaw Runtime rather than a new protocol

These are the parts of the repo most ready to be read as intentional system design rather than rough experimentation.

## Experimental or evolving

These areas are real and important, but should still be treated as actively evolving:
- adaptive runtime behavior and some queue/orchestration semantics
- parts of qualification and confirmation behavior
- some planner-to-runtime semantics that have recently been hardened but are still being refined
- public onboarding, quickstart, and demo ergonomics
- public proof presentation and broader trust storytelling, even though the underlying validation surfaces are now more explicit
- adapter/carrier ideas such as an OpenClaw Skill, MCP Policy Gateway, and A2A security metadata profile; these should follow stable contract proof rather than lead it

In other words, the system is real, but not every surface should be read as frozen.

## Internal or live-workspace only

The public repo is not the same thing as the live operator workspace.
The following categories should be treated as internal/live-workspace concerns unless explicitly documented otherwise:
- mixed runtime residue and local state
- operator memory/bootstrap/persona files
- local control-plane state and generated artifacts
- deployment-specific residue, host-specific assumptions, and local helper state
- internal runtime guidance that is pruned from the public snapshot path

Public readers should evaluate Ravenclaw from the intentionally published surfaces, not from assumptions about the operator's full live environment.

## Not promised or guaranteed

Ravenclaw does **not** currently promise:
- a zero-friction consumer install experience
- a fully stable package/distribution shape
- that every internal subsystem is final
- that the public checkout equals the operator's full live environment
- that public docs already cover every advanced runtime seam equally well
- a new general agent protocol or near-term A2A/MCP implementation
- that autonomy removes the need for operator judgment, legal authorization, or organizational accountability

The strongest honest claim today is:
Ravenclaw is a serious governance-first security research runtime with a publishable public core, a separate private/operator overlay reality, and a stronger technical core than its current public ergonomics.

For the current public validation, trust, and proof-of-value layer, start with:
- `VALIDATION.md`
- `QUALITY_SIGNALS.md`
- `PROOF_OF_VALUE.md`
- `references/public-core-private-overlay-boundary.md`
