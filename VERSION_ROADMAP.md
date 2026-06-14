# VERSION_ROADMAP.md

## Purpose

This file defines Ravenclaw's version roadmap after the GovEngine/SCLite package-chain stabilization.

Current published public helper package version: `0.18.2`.
Current dependency baseline:

```text
Ravenclaw -> govengine>=0.13.0,<0.14 -> sclite-core>=1.0.2,<1.1
```

Use this as a milestone map, not as a promise that every milestone will become a full PyPI/runtime release. The current published public helper package is `ravenclaw-security==0.18.4`, carrying public profile/readiness helpers under the `ravenclaw` import package; Ravenclaw remains a source/reference security runtime until install, execution, Logdash, and public-safety boundaries are ready for a stronger distribution claim.

## Architecture direction

Target ecosystem:

```text
SCLite     = contract / proof / review layer
GovEngine  = deterministic governed-runtime kernel
Ravenclaw  = reference security-research runtime and security domain profile
Tecrax     = future governed infrastructure-operations runtime/profile
```

Ravenclaw's role is not to become a second GovEngine. Ravenclaw should preserve the security-research domain semantics, public-safe proof path, campaign UX, finding pipeline, Logdash/operator visibility, and future security harness adapters while generic mechanics move behind GovEngine contracts.

Core thesis:

```text
LLM intent is not execution authority.
```

Ravenclaw should demonstrate that authorized security automation can be bounded, reviewable, interruptible, and accountable:

```text
intent
  -> policy decision
  -> execution contract
  -> execution ticket
  -> GovEngine gate
  -> runner dry-run or bounded execution
  -> receipt
  -> evidence contract
  -> SCLite review bundle
```

## Boundary rules

Ravenclaw owns:

- security research runtime semantics;
- campaign and target/scope UX;
- security task families and planning stages;
- security-specific policies, audit checklists, and evidence rules;
- security tools/capabilities and host adapters;
- finding pipeline and reporting semantics;
- Logdash/operator UI;
- public demo/proof narrative;
- future OpenClaw/harness adapter work after kernel/profile boundaries are stable.

Ravenclaw should not own long-term generic versions of:

- orchestrator kernel mechanics;
- event/state/control envelopes;
- queue/scheduler/heartbeat/lease mechanics;
- generic planner/task contracts;
- generic admission/policy/approval/ticket controllers;
- generic runner protocol/supervision;
- generic evidence-review contracts;
- trust/signer/verifier ports;
- carrier protocols.

Refactor principle:

```text
Extract contracts and adapters, not files.
```

Do not mechanically move `engine/auto_campaign_runner.py` or other Ravenclaw modules into GovEngine. Define neutral GovEngine contracts first, route Ravenclaw through compatibility wrappers, validate parity, then thin legacy paths.

For the current extraction-readiness audit, use
`references/govengine-extraction-readiness-roadmap.md`. That roadmap classifies
which Ravenclaw concepts are already covered by GovEngine projection adapters,
which candidates are deferred until Tecrax proves the same need, and which
implementation behavior must remain Ravenclaw-owned.

## Ravenclaw Security Profile shape

Future profile-oriented structure should converge toward:

```text
ravenclaw/
  security_profile/
    task_families.py
    planning_stages.py
    capabilities.py
    tools.py
    audit_checklists.py
    policy_rules.py
    evidence_rules.py

  runtime/
    campaign.py
    target_surface.py
    finding_pipeline.py
    public_demo.py

  logdash/
    operator UI

  adapters/
    openclaw/     # later, after readiness review
```

Security profile examples:

- resource types: `host`, `url`, `endpoint`, `web_app`;
- task families: `recon`, `authz`, `idor`, `workflow`, `content_discovery`, `tls_assessment`;
- planning stages: `discovery`, `validation`, `control_boundary_confirmation`, `state_transition_confirmation`, `bounded_exploit_proof`, `report_artifact_capture`.

This structure is directional. It should emerge through compatibility layers and tests, not through a large unvalidated tree rewrite.

## Versioning principles

- Version bumps should reflect meaningful boundary, validation, or operator-control improvements.
- Internal refactors are valuable only when they preserve behavior and reduce real coupling.
- Public claims must lag behind validated behavior.
- Controlled live execution is a proof of governance, not a promise of offensive autonomy.
- Adapters come after kernel/profile/proof stability. Default order: OpenClaw first, MCP later, A2A last/example-first.

## `0.10.x` — package-chain and public-safe proof stabilization

Delivered foundation line.

Intent:

- keep the current public-safe demo stable;
- consume published GovEngine/SCLite package ranges;
- keep Security Contract validation green;
- document Ravenclaw as the security reference runtime/profile for the GovEngine/SCLite ecosystem;
- mark legacy direct execution paths as compatibility/dev where appropriate;
- do not start carrier adapters or live-authority expansion.

Current baseline:

- Ravenclaw consumes `govengine>=0.13.0,<0.14` and `sclite-core>=1.0.2,<1.1`;
- public install validation and Security Contract validation pass;
- GovEngine/SCLite ticket and receipt-bounded-evidence surfaces are integrated into the public proof chain.
- GovEngine 0.11 alpha kernel/profile boundary, runtime-shell, planning-contract, admission-policy, runner-supervision, evidence-review, Domain Profile SDK, and runtime contract proof validation is required by public install validation and focused projection tests.
- The structural Security Contract validation profile is available for automation that must not execute demo runtime checks.
- The active public proof path emits the current scoped-ticket lifecycle and a canonical SCLite review bundle; legacy proof trace material is migration/history-only and excluded from current public surface claims.
- Ravenclaw owns lifecycle projection from its host/runtime payloads; GovEngine no longer exposes a Ravenclaw-shaped projection adapter and SCLite no longer exposes the retired proof-trace path as a supported product surface.

Exit criteria:

- docs consistently describe SCLite/GovEngine/Ravenclaw boundaries;
- public demo and validation receipts remain reproducible;
- stale roadmap language about older `0.8/0.9/1.x` directions is archived or remapped.

## `0.11.x` — GovEngine-compatible event/state/control mapping

Intent:

Map Ravenclaw runtime/control state onto GovEngine-compatible models while preserving Logdash behavior.

Current mapping source:

- `references/runtime-state-control-govengine-map.md`

Planned work:

- map `.auto_campaign.state.json` to a GovEngine runtime-shell state projection;
- map `.orchestrator.state.json` to `GovOrchestratorState`;
- map `.auto_campaign.queues.json` or current queue snapshots to `GovQueueSnapshot`;
- map `.runtime_snapshot.json` or equivalent status projections to `GovRuntimeSnapshot`;
- map Logdash/start/pause/resume/stop/cancel/replan/cooldown/archive semantics to GovEngine control actions;
- keep state storage host-owned and public/private boundaries explicit.

Definition of done:

- Ravenclaw control semantics still work;
- GovEngine-compatible state/control adapters have focused tests;
- no Logdash UI behavior is moved into GovEngine;
- public docs explain canonical vs compatibility state paths.

Current status: the first 0.11 adapter slice is implemented through
`engine/govengine_state_control_projection.py`, backed by GovEngine 0.3
`runtime_shell` validators and focused tests.

## `0.12.x` — Planning and runtime task contract migration

Intent:

Route Ravenclaw planner/runtime task semantics through GovEngine planning/task contracts while preserving security meaning in Ravenclaw.

Planned work:

- map `engine/runtime_task_schema.py` to `GovTaskContract` compatibility;
- map `engine/planer/planner_intent_contract.py` to `PlanIntentContract` compatibility;
- preserve planning ladder, evidence goals, activation/depth/priority semantics, and security profile stages;
- add semantic-preservation tests from blueprint -> runtime plan -> queue/admission payload;
- keep security-specific planning heuristics in Ravenclaw profile.

Definition of done:

- RuntimeTaskContract v2 is backed by or convertible to GovEngine task contracts;
- planner intent contracts can be validated through GovEngine-compatible paths;
- existing public demo and targeted runtime-plan tests remain green.

Current status: the first 0.12 adapter slice is implemented through
`engine/govengine_planning_projection.py`, backed by GovEngine 0.4
`planning` validators and focused tests. Raw Ravenclaw targets are hashed into
redacted `target_ref` values before entering GovEngine contracts.

## `0.13.x` — Admission, audit, policy, and approval migration

Intent:

Move generic admission/go-no-go mechanics behind GovEngine while Ravenclaw keeps security policy semantics.

Planned work:

- adapt `runtime_admission_policy.py` and generic parts of `runtime_execution_gate.py` to GovEngine `AdmissionController`/gate contracts;
- map Ravenclaw auditor decisions to GovEngine `AuditDecision`/`ApprovalRequest` shapes;
- keep security-specific signals, rules of engagement, target/scope policies, and owner-gated semantics in Ravenclaw;
- add negative tests for policy drift, scope drift, budget/depth violation, cooldown, missing owner approval, and dry-run degradation.

Definition of done:

- Ravenclaw can ask GovEngine whether a task may continue, must dry-run, requires approval/replan, or is blocked;
- security-specific policy remains profile-owned;
- public docs accurately describe non-claims and approval boundaries.

Current status: the first 0.13 adapter slice is implemented through
`engine/govengine_admission_projection.py`, backed by GovEngine 0.5
`admission` validators and focused tests. Raw Ravenclaw hosts/targets are
hashed into redacted `subject_ref` values before entering GovEngine contracts.

## `0.14.x` — Execution supervision and Controlled Live Mode groundwork

Intent:

Route approved execution through GovEngine runner gate/supervisor while keeping live execution disabled unless explicitly authorized and bounded.

Planned work:

- introduce Ravenclaw host adapter/profile runner around GovEngine `RunnerGate`/`ExecutionSupervisor`;
- mark legacy `execute(action_spec)` style paths as compatibility/dev-only where possible;
- support `demo`, `dry-run`, `local-lab`, and future `authorized-live`/`controlled-live` mode names;
- require scope, operator authorization, policy decision, execution contract, ticket, runner profile, bounded args, timeout/env/cwd/stdin policy, receipt, evidence bounds, and stop/pause controls;
- start with safe classes only: metadata collection, DNS/TLS/header inspection, bounded HTTP probing, controlled content discovery, local lab validation, and evidence capture.

Controlled Live Mode framing:

```text
Execution is possible, but never from raw intent.
```

Definition of done:

- dry-run remains the default;
- live backend is blocked by default and negative-tested;
- local-lab/controlled-live paths require explicit operator approval and receipts;
- no raw prompt/tool execution path bypasses GovEngine.

Current status: the first 0.14 adapter slice is implemented through
`engine/govengine_runner_supervision_projection.py`, backed by GovEngine 0.6
`execution.supervision` validators and focused tests. It projects approved-spec
runner requests, supervision plans, leases, and receipts while leaving concrete
tool execution and live backend authority in Ravenclaw.

## `0.15.x` — Evidence/review migration

Intent:

Move generic evidence qualification/review contracts behind GovEngine while Ravenclaw keeps finding taxonomy and security reporting semantics.

Planned work:

- map confirmation policy, false-positive guards, control comparison, reproduction requirements, and evidence qualification to GovEngine review contracts;
- bridge Ravenclaw finding/evidence output to SCLite review bundles;
- preserve security finding taxonomy and report narrative in Ravenclaw;
- add overclaim tests: dry-run cannot support live vulnerability claims, missing receipts cannot support execution truth, blocked receipts cannot support completed-action claims.

Definition of done:

- Ravenclaw evidence pipeline consumes GovEngine review contracts;
- SCLite review-bundle validation remains the proof boundary;
- public proof narrative is clearer and less Ravenclaw-specific.

Current status: the first 0.15 adapter slice is implemented through
`engine/govengine_review_projection.py`, backed by GovEngine 0.7 `review`
validators and focused tests. It projects receipt-bounded evidence claims and
review results while keeping Ravenclaw finding taxonomy and SCLite review-bundle
verdict authority outside GovEngine. Active finding-signal, semantic-analysis,
and confirmation-policy behavior remains Ravenclaw-owned through
`engine/security_signal_contract.py`, `engine/security_analysis_contract.py`,
and `engine/security_evidence_policy.py`; it is not part of neutral
`govengine.review`.

## `0.16.x` — Security profile packaging and adapter readiness

Intent:

Make Ravenclaw visibly a domain profile/runtime over GovEngine rather than a mixed generic/runtime monolith.

Planned work:

- converge toward `security_profile/` and `runtime/` structure where compatibility allows;
- add profile conformance metadata once GovEngine Domain Profile SDK exists;
- produce OpenClaw adapter readiness packet covering scope UX, redaction, command authority, lifecycle artifacts, rollback, and public/private boundaries;
- defer MCP/A2A until OpenClaw readiness is proven and kernel/profile boundaries remain boring.

Definition of done:

- profile boundary is documented and tested;
- OpenClaw adapter work has a readiness packet, not implementation sprawl;
- no carrier bypasses GovEngine or SCLite.

Current status: the first 0.16 profile-boundary slice is implemented through
`engine/ravenclaw_security_profile.py`, focused profile tests, and
`references/openclaw-adapter-readiness-packet-2026-05-20.md`. Ravenclaw is now
validated as the security runtime/profile over GovEngine + SCLite. The second
0.16 prep slice adds `engine/openclaw_adapter_readiness.py`, redaction/output
matrix tests, and an approval UX sketch; OpenClaw remains readiness-contracts
only, while MCP and A2A remain deferred.

## `0.17.x` — Runtime/profile consolidation over landed projections

Intent:

Use the GovEngine contracts already projected in Ravenclaw before requesting
more kernel breadth. This is a runtime adoption and boundary-hardening line,
not a new protocol or adapter line.

Planned work:

- audit active runtime/control paths against the already-landed state/control,
  planning, admission, runner-supervision, and review projections;
- keep projection adapters where Ravenclaw owns host semantics, and remove
  wrapper layers that only duplicate direct GovEngine/SCLite package surfaces;
- keep security-profile meaning, demo narration, and readiness UX
  Ravenclaw-owned; reject GovEngine `security_profile_helpers` as a retired
  upstream surface in the current package line;
- keep Logdash state/control truth aligned with persisted runtime-state docs and
  machine checks;
- keep public helper-package claims narrow while source/runtime install and
  validation boundaries are clarified.

Already covered by GovEngine; maintain Ravenclaw projection adapters unless a
compatibility test proves a thinner path:

- `engine/govengine_state_control_projection.py`;
- `engine/govengine_planning_projection.py`;
- `engine/govengine_admission_projection.py`;
- `engine/govengine_runner_supervision_projection.py`;
- `engine/govengine_review_projection.py`.

Definition of done:

- changed runtime seams have focused compatibility tests and public truth/state
  validators still pass;
- Ravenclaw retains security task families, finding taxonomy, execution engine,
  auto-campaign behavior, Logdash, and operator UX ownership;
- no new GovEngine extraction is proposed from a single Ravenclaw-only shape
  when a projection adapter is already sufficient;
- public docs do not overclaim full PyPI runtime readiness, carrier
  implementation, or live target authority.

Current status: Ravenclaw has completed the first consumer-first narrowing
sequence for GovEngine's optional legacy `security_profile_helpers` surface and
no longer imports or requires the retired optional security-profile facade.
Active
security policy/scope decisions run through `engine/security_policy_gateway.py`,
and active action/tooling helpers run through Ravenclaw-local
`engine/security_action_*`, `engine/security_tool_registry.py`,
`engine/security_policy_core.py`, `engine/security_capability_recipes.py`, and
`engine/security_semantic_loss_policy.py` modules. Active security signal,
analysis, and confirmation-policy helpers also run through
`engine/security_signal_contract.py`, `engine/security_analysis_contract.py`,
and `engine/security_evidence_policy.py`, while
`engine/govengine_review_projection.py` retains the separate neutral
`govengine.review` projection. The helper-boundary validator rejects
reintroducing those upstream optional modules into Ravenclaw runtime authority.
Published GovEngine `0.12.1a1` removes that compatibility facade. Ravenclaw
now requires the neutral-only 0.12 line and keeps security helper authority
host-owned.

## `0.18.x` — Package/runtime readiness checkpoint

Intent:

Decide what the public Ravenclaw distribution should actually promise after
0.17 consolidation.

Candidate work:

- map the minimum installable public runtime subset, if one exists, without
  publishing operator overlay or local state assumptions;
- keep the existing `ravenclaw-security` helper distribution narrow if source
  runtime boundaries are still the truthful contract;
- build package/snapshot/public-install checks that fail on missing dependency,
  state-path, fixture, residue, and maturity truth;
- revisit a first OpenClaw fixture presenter only after this package/runtime
  checkpoint and the carrier readiness gates remain green.

Entry criteria:

- 0.17 runtime/profile consolidation did not expose unresolved ownership drift;
- docs, state truth, residue audit, public install validation, and security
  contract validation agree on what is source runtime versus public package;
- a carrier or installability slice can be validated with no credentials, live
  targets, or external side effects.

Definition of done:

- Ravenclaw either has a validated, bounded next package promise or an explicit
  decision to keep the full runtime source/reference-owned;
- OpenClaw/MCP/A2A implementation remains out of scope unless a separate
  approved carrier packet proves its authority boundary;
- GovEngine and SCLite stay upstream dependencies rather than hidden Ravenclaw
  copies.

Current decision: keep the public distribution as the bounded
`ravenclaw-security` helper/profile package until a public runtime subset can
pass the install, state-path, residue, and public-safety checks without operator
overlay assumptions.

Current checkpoint hardening: package/runtime truth is guarded by
`scripts/validate_package_runtime_boundary.py`, and the OpenClaw
fixture-presenter review harness is guarded by
`scripts/validate_openclaw_fixture_presenter.py` plus committed fixture data
under `examples/openclaw-fixture-presenter/`. This is review hardening, not
carrier implementation.

## Future `1.0` bar

Ravenclaw should not claim `1.0` maturity until all of the following are true:

- public demo/proof path is reproducible and truthful;
- GovEngine/SCLite boundaries are integrated without duplicate generic logic;
- Logdash state/control truth matches runtime behavior;
- execution path is governed through contracts, tickets, policy, trust, runner gate, receipt, and review;
- profile boundary is clear enough that Tecrax can exist as a second dry-run domain proof;
- docs and non-claims are aligned with behavior;
- validation, install, residue, and public-safety gates pass on the exact tree to be published.

`1.0` should mean governance maturity and evidence-backed operator control, not merely feature volume.

## Tecrax relationship

Tecrax is the reserved name for the future governed infrastructure-operations runtime/profile built on GovEngine + SCLite. It should not inherit temporary working-name/product framing until naming language is deliberately chosen.

Ravenclaw should prepare for Tecrax by extracting generic mechanics into GovEngine, not by importing infrastructure semantics into the security runtime.

Tecrax should eventually prove portability with infrastructure tasks such as:

- inspect service state;
- diagnose failure;
- propose a bounded change;
- dry-run the change;
- request approval;
- execute only under explicit policy/ticket/runner bounds;
- verify;
- rollback if needed;
- emit SCLite review bundle.

Initial Tecrax proofs should be dry-run/local-lab only.

## Stop conditions

Pause for operator review if:

- live execution authority would expand;
- a carrier/harness could bypass GovEngine;
- public docs would claim more than tests prove;
- private operator state or target material might enter public commits;
- a refactor requires published-history rewrite;
- Ravenclaw behavior drifts without a compatibility test.
