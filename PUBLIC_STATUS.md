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

These are the parts of the repo most ready to be read as intentional system design rather than rough experimentation.

## Experimental or evolving

These areas are real and important, but should still be treated as actively evolving:
- adaptive runtime behavior and some queue/orchestration semantics
- parts of qualification and confirmation behavior
- some planner-to-runtime semantics that have recently been hardened but are still being refined
- public onboarding, quickstart, and demo ergonomics
- public proof presentation and broader trust storytelling, even though the underlying validation surfaces are now more explicit

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
- that public docs already cover every advanced runtime seam equally well
- that autonomy removes the need for operator judgment, legal authorization, or organizational accountability

The strongest honest claim today is:
Ravenclaw is a serious governance-first security research runtime with a stronger technical core than its current public ergonomics, and the repo is being deliberately elevated to close that gap.

For the current public validation and trust layer, start with:
- `VALIDATION.md`
- `QUALITY_SIGNALS.md`