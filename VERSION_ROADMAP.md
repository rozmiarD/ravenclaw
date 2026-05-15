# VERSION_ROADMAP.md

## Purpose

This file defines Ravenclaw's version roadmap after the GovEngine/SCLite package-chain stabilization.

Current public source version: `0.10.0`.
Current dependency baseline:

```text
Ravenclaw -> govengine>=0.1.7,<0.2 -> sclite-core>=0.5.1,<0.6
```

Use this as a milestone map, not as a promise that every milestone will become a PyPI/runtime release. Ravenclaw remains a source/reference security runtime until install, profile, execution, Logdash, and public-safety boundaries are ready for a stronger distribution claim.

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

Current line.

Intent:

- keep the current public-safe demo stable;
- consume published GovEngine/SCLite package ranges;
- keep Security Contract validation green;
- document Ravenclaw as the security reference runtime/profile for the GovEngine/SCLite ecosystem;
- mark legacy direct execution paths as compatibility/dev where appropriate;
- do not start carrier adapters or live-authority expansion.

Current baseline:

- Ravenclaw consumes `govengine>=0.1.7,<0.2` and `sclite-core>=0.5.1,<0.6`;
- public install validation and Security Contract validation pass;
- GovEngine/SCLite ticket and receipt-bounded-evidence surfaces are integrated into the public proof chain.

Exit criteria:

- docs consistently describe SCLite/GovEngine/Ravenclaw boundaries;
- public demo and validation receipts remain reproducible;
- stale roadmap language about older `0.8/0.9/1.x` directions is archived or remapped.

## `0.11.x` — GovEngine-compatible event/state/control mapping

Intent:

Map Ravenclaw runtime/control state onto GovEngine-compatible models while preserving Logdash behavior.

Planned work:

- map `.auto_campaign.state.json` to `GovRunState`;
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
