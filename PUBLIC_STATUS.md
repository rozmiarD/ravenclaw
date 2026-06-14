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
- SCLite-backed Security Contract Layer integration: SCLite is the reusable contract/schema dependency, GovEngine is the reusable governed-runtime kernel dependency, and Ravenclaw remains the governed security reference runtime/profile rather than a new protocol
- demo-mode GovEngine signing/trust-port projection on lifecycle tickets, explicitly as fixture evidence rather than PKI or production identity proof

These are the parts of the repo most ready to be read as intentional system design rather than rough experimentation.

## Experimental or evolving

These areas are real and important, but should still be treated as actively evolving:
- adaptive runtime behavior and some queue/orchestration semantics
- parts of qualification and confirmation behavior
- some planner-to-runtime semantics that have recently been hardened but are still being refined
- public onboarding, quickstart, and demo ergonomics
- public proof presentation and trust documentation, including demo signing/trust-port evidence, even though the underlying validation surfaces are now more explicit
- the current published public helper package, `ravenclaw-security==0.18.4`, which packages narrow public profile/readiness APIs while the full runtime remains a source/reference workflow
- Ravenclaw-owned lifecycle artifact projection into current SCLite review artifacts; GovEngine does not own host-shaped projection and SCLite no longer exposes the retired proof-trace product path as current
- the current security helper ownership line: Ravenclaw executes security policy/scope decisions through `engine/security_policy_gateway.py` and owns active action/tooling helpers through local `engine/security_action_*`, `engine/security_tool_registry.py`, `engine/security_policy_core.py`, `engine/security_capability_recipes.py`, and `engine/security_semantic_loss_policy.py` modules
- Ravenclaw owns active security signal, analysis, and confirmation-policy behavior through `engine/security_signal_contract.py`, `engine/security_analysis_contract.py`, and `engine/security_evidence_policy.py`; the separate `engine/govengine_review_projection.py` consumes neutral receipt-bounded `govengine.review` contracts
- Ravenclaw depends on the published GovEngine `0.13.0` line; retired `security_profile_helpers` modules are no longer part of the required upstream package surface, and Ravenclaw owns the active security runtime authority locally
- adapter/carrier ideas such as an OpenClaw Skill, MCP Policy Gateway, and A2A security metadata profile; these should follow stable contract proof rather than lead it. The docs/contracts-only OpenClaw boundary is mapped in `references/openclaw-adapter-contract-map.md`; future carrier gates are listed in `references/carrier-readiness-checklist.md`, and proposal packets should use `references/carrier-readiness-packet-template.md`.
- the OpenClaw fixture-presenter example under `examples/openclaw-fixture-presenter/`, which is a review harness for redaction and command-authority boundaries, not an implemented adapter.

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
- an easy consumer install experience
- a complete PyPI-published Ravenclaw runtime runner; `ravenclaw-security==0.18.4` is a narrow public profile/readiness package, while the full runtime remains source/reference
- a fully stable package/distribution shape beyond the documented `0.18.2` helper APIs
- that every internal subsystem is final
- that the public checkout equals the operator's full live environment
- that public docs already cover every advanced runtime seam equally well
- a new general agent protocol or near-term A2A/MCP implementation
- that autonomy removes the need for operator judgment, legal authorization, or organizational accountability
- PKI, CA, KMS, trust-store, key-store, or production identity ownership from demo signing/trust metadata

The strongest honest claim today is:
Ravenclaw is a governance-first security research runtime with a publishable public core, a separate private/operator overlay, and public docs and setup paths that are still improving.

For the current public validation, trust, and proof-of-value layer, start with:
- `VALIDATION.md`
- `QUALITY_SIGNALS.md`
- `PROOF_OF_VALUE.md`
- `references/public-core-private-overlay-boundary.md`
