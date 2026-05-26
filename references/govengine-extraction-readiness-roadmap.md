# Ravenclaw -> GovEngine Extraction Readiness Roadmap

Current baseline:

```text
Ravenclaw: ravenclaw-security==0.18.2
Package chain: Ravenclaw -> govengine>=0.12.1a1,<0.13 -> sclite-core>=0.8.0b2,<0.9
Maturity: alpha public helper/profile package; full runtime remains source/reference
```

This roadmap records which Ravenclaw concepts are already covered by
GovEngine, which future candidates may be extracted as neutral contracts, and
which implementation behavior should remain Ravenclaw-owned.

It is not an implementation claim. No new GovEngine runtime behavior is claimed
here.

## Executive Summary

Do not perform a large extraction now. Ravenclaw already has the right bridge
shape: host-owned projection adapters over existing GovEngine contracts.

Highest-value current action: keep the adapters tested and make this extraction
roadmap mechanically validated so future work does not turn GovEngine into a
copy of Ravenclaw Runtime.

Highest-value future candidate: a runtime-owned artifact descriptor contract,
but only after Tecrax proves the same need. Until then, Ravenclaw's state-file
model remains Ravenclaw-specific evidence, not neutral core truth.

Wave C checkpoint: the first Tecrax local-fixture host slice can use existing
GovEngine profile/planning/supervision/review contracts plus SCLite artifact
descriptors without a new GovEngine surface. The next bounded work stays in
Ravenclaw as an OpenClaw fixture presenter harness; it is not a carrier adapter
implementation.

GovEngine boundary health: healthy. GovEngine owns deterministic contracts and
validators. Ravenclaw owns security runtime behavior, Logdash, state files,
queue mutation, concrete execution, findings, and operator UX. SCLite owns
lifecycle, proof, artifact-chain, review, validation, and integrity artifacts.
Ravenclaw also owns projection of its host/runtime payloads into current
lifecycle artifacts; that projection is no longer a GovEngine host-shaped
adapter and it does not reintroduce SCLite's retired proof-trace product path.

Current ownership result: after containing the optional helper surface,
Ravenclaw returned the executed policy/scope gateway and the coupled
action/tooling helper group to Ravenclaw-owned modules:
`engine/security_policy_gateway.py`, `engine/security_policy_core.py`,
`engine/security_tool_registry.py`, `engine/security_action_schema.py`,
`engine/security_action_validators.py`, `engine/security_action_compiler.py`,
`engine/security_capability_recipes.py`, and
`engine/security_semantic_loss_policy.py`. The remaining active
security-review interpretation is also Ravenclaw-owned through
`engine/security_signal_contract.py`, `engine/security_analysis_contract.py`,
and `engine/security_evidence_policy.py`: finding/workflow signals,
security-semantic analysis, and confirmation policy are not the neutral
receipt-bounded contract modeled by `govengine.review`. The published
GovEngine optional helpers remain compatibility surfaces for now.

## Already Covered By GovEngine

These are not new extraction targets. Ravenclaw should maintain projection
adapters and prevent drift.

| Ravenclaw adapter | GovEngine surface | Current posture |
| --- | --- | --- |
| `engine/govengine_state_control_projection.py` | `govengine.runtime_shell` | Already covered by GovEngine; keep Ravenclaw projection adapter. |
| `engine/govengine_planning_projection.py` | `govengine.planning` | Already covered by GovEngine; keep security planning meaning in Ravenclaw. |
| `engine/govengine_admission_projection.py` | `govengine.admission` | Already covered by GovEngine; keep admission policy meaning in Ravenclaw. |
| `engine/govengine_runner_supervision_projection.py` | `govengine.execution.supervision` | Already covered by GovEngine; keep concrete tool execution in Ravenclaw. |
| `engine/govengine_review_projection.py` | `govengine.review` | Already covered by GovEngine; keep finding taxonomy and SCLite review verdict authority outside GovEngine. |

## Extraction Candidate Table

| Candidate | Ravenclaw source files | Generic concept | Recommendation | Risk | Status |
| --- | --- | --- | --- | --- | --- |
| Extraction governance hardening | `VERSION_ROADMAP.md`, `DOCS_MAP.md`, this file, `scripts/validate_extraction_roadmap.py` | mechanically guarded extraction truth | Add Ravenclaw validation/docs hardening, not GovEngine runtime code. | low | implement now as Ravenclaw validation/docs hardening |
| Runtime state/control projection | `engine/govengine_state_control_projection.py`, `STATE_FILES.md`, `references/runtime-state-control-govengine-map.md` | control action, runtime snapshot, queue snapshot | Use existing GovEngine API; do not extract state storage. | low | already covered by GovEngine; maintain projection adapter |
| Runtime task handoff fields | `engine/runtime_task_schema.py`, `engine/govengine_planning_projection.py` | task contract, activation/depth/priority hints | Use existing GovEngine API; add GovEngine fields only after a second profile needs them. | medium | already covered by GovEngine; maintain projection adapter |
| Admission decision and blocked reason record | `engine/runtime_admission_policy.py`, `engine/runtime_execution_gate.py`, `engine/govengine_admission_projection.py` | admission result, blockers, explainability | Keep Ravenclaw policy logic; project redacted neutral decisions. | medium | already covered by GovEngine; maintain projection adapter |
| Security action/tooling helpers | `engine/security_action_*`, `engine/security_tool_registry.py`, `engine/security_policy_core.py`, `engine/security_capability_recipes.py`, `engine/security_semantic_loss_policy.py`, `engine/security_policy_gateway.py` | security action vocabulary, tool registry, recipe lowering, action validation, semantic-loss and policy gate behavior | Keep active implementation in Ravenclaw; published GovEngine `0.12.1a1` removes the optional upstream copies. | low | host-owned in Ravenclaw; removed in published GovEngine 0.12 |
| Security review-contract helpers | `engine/security_signal_contract.py`, `engine/security_analysis_contract.py`, `engine/security_evidence_policy.py`, `engine/govengine_review_projection.py` | finding/workflow signal, security-semantic analysis, confirmation policy versus neutral receipt review projection | Keep active security interpretation in Ravenclaw and retain only the separate neutral `govengine.review` projection; published GovEngine `0.12.1a1` removes the optional upstream facade. | low | host-owned in Ravenclaw; removed in published GovEngine 0.12 |
| Runtime-owned artifact descriptor | `STATE_FILES.md`, `engine/paths.py`, `engine/runtime_persist_services.py`, `logdash/services.py` | descriptor of host-owned state artifact, retention, source, public/private status | Extract later as a contract only if Tecrax proves the same need. | medium | defer until Tecrax proves need |
| Host gate reason-code registry | `engine/runtime_admission_policy.py`, `engine/runtime_execution_gate.py`, `engine/runtime_effective_decision.py` | portable reason-code catalog and severity mapping | Extract later only as an optional neutral registry if duplication appears across profiles. | medium | extract later as contract |
| Replay/evaluation summary | `engine/evaluation_metrics.py`, `engine/evaluation_replay.py`, `QUALITY_SIGNALS.md` | replay result and governance-quality metrics | Wait for another domain profile; current metrics are security-shaped. | medium | defer until Tecrax proves need |
| State-file manifest | `STATE_FILES.md`, `engine/paths.py`, `logdash/services.py` | local truth-source inventory | Do not extract now; storage ownership would blur the kernel boundary. | high | defer until Tecrax proves need |
| Queue implementation and campaign loop | `engine/auto_campaign.py`, `engine/auto_campaign_runner.py`, `engine/runtime_queue_strategy.py` | concrete queue mutation and scheduler loop | Keep implementation in Ravenclaw; only neutral snapshots/contracts may be reconsidered after Tecrax proves the same need. | high | keep implementation in Ravenclaw |
| Logdash operator workflow | `logdash/services.py`, `logdash/api_*.py`, `logdash/templates/*` | operator UX and runtime control-plane behavior | Keep in Ravenclaw. | high | keep in Ravenclaw |
| Vulnerability qualification | `engine/vuln_qualification.py`, `engine/auto_campaign_qualification.py`, `engine/analysis.py` | security evidence taxonomy and confidence model | Keep in Ravenclaw; GovEngine only bounds neutral review claims. | high | keep in Ravenclaw |
| Concrete execution adapter | `engine/executor.py`, `engine/runtime_task_execution.py` | concrete command/tool/runtime execution | Keep implementation in Ravenclaw; GovEngine gates/supervises approved requests. | high | keep implementation in Ravenclaw |

Allowed extraction statuses for this roadmap:

- `implement now as Ravenclaw validation/docs hardening`
- `already covered by GovEngine; maintain projection adapter`
- `extract later as contract`
- `defer until Tecrax proves need`
- `keep implementation in Ravenclaw`
- `keep in Ravenclaw`
- `host-owned in Ravenclaw; removed in published GovEngine 0.12`

## Boundary Analysis

The boundary is healthy where Ravenclaw uses GovEngine validators without
moving Ravenclaw behavior:

```text
GovEngine owns deterministic contracts, validators, gates, receipts, snapshots,
and profile conformance shapes.

Ravenclaw owns security runtime behavior, Logdash, state files, queue mutation,
target/scope UX, concrete tool execution, security finding taxonomy, public demo
assembly, and operator workflows.

SCLite owns lifecycle, artifact-chain, proof, review, validation, and integrity
artifacts.
```

The blurry areas are runtime state files, queue/scheduler behavior, admission
reasoning, and replay metrics. Current code already handles these through
projection adapters rather than moving implementation into GovEngine.

No roadmap item should move `engine/auto_campaign_runner.py`,
`engine/auto_campaign.py`, `logdash/services.py`, `engine/executor.py`, or
Ravenclaw state-file mutation into GovEngine.

## Rejected / Deferred Extraction Decisions

- `engine/auto_campaign_runner.py`: rejected now as implementation-heavy runtime behavior.
- `engine/auto_campaign.py`: rejected now as security campaign loop behavior.
- `logdash/services.py`: rejected as operator UX/control-plane behavior.
- `engine/executor.py`: rejected as concrete command-building and execution adapter behavior.
- `engine/vuln_qualification.py`: rejected as security finding taxonomy and confidence behavior.
- Ravenclaw state files under `reports/`: deferred; neutral descriptors may be reconsidered after Tecrax proves the same need.
- Queue mutation and scheduler behavior: keep implementation in Ravenclaw; only neutral snapshots/contracts may be reconsidered after Tecrax proves the same need.

## Recommended Extraction Plan

Immediate low-risk work:

1. Keep the existing projection adapters and strengthen focused tests around them.
2. Validate this roadmap through `scripts/validate_extraction_roadmap.py`.
3. Keep this roadmap under `scripts/validate_public_truth.py`.
4. Add negative tests when adapters touch raw targets, commands, credentials,
   storage paths, carrier payloads, or live-execution flags.
5. Keep the active security scope/policy decision in
   `engine/security_policy_gateway.py`, keep the active security action/tooling
   group in local `engine/security_*` modules, and reject runtime
   reintroduction of the corresponding upstream optional helper modules.
6. Keep active signal/analysis/confirmation behavior in
   `engine/security_signal_contract.py`, `engine/security_analysis_contract.py`,
   and `engine/security_evidence_policy.py`; use
   `engine/govengine_review_projection.py` only for neutral receipt-bounded
   review projection.

Medium-term work:

1. Consider a neutral runtime-owned artifact descriptor only after another
   profile needs the same shape.
2. Consider a neutral reason-code registry only if Ravenclaw and Tecrax need
   shared classification without shared domain meaning.
3. Thin Ravenclaw runtime code by routing import sites toward projection helpers,
   not by moving runtime loops into GovEngine.

Defer until Tecrax proves need:

1. Runtime artifact manifest and retention descriptors.
2. Replay/evaluation metric contracts.
3. Cross-profile state-file inventory conventions.
4. Scheduler/queue abstractions beyond redacted snapshots.

Keep in Ravenclaw:

1. Logdash UI/API/services.
2. Security planning stages, task families, vulnerability classes, qualification
   confidence, report narrative, and public demo UX.
3. OpenClaw/MCP/A2A adapter implementation work unless a later adapter package
   is deliberately created.

Keep implementation in Ravenclaw; only neutral snapshots/contracts may be
reconsidered after Tecrax proves the same need:

1. Auto-campaign loop, queue mutation, retry strategy, and host health behavior.
2. Concrete executor, tool registry usage, command building, and live backend
   decisions.

## Validator Design

`scripts/validate_extraction_roadmap.py` should check:

- current Ravenclaw version;
- GovEngine dependency range;
- SCLite dependency range;
- allowed extraction statuses;
- forbidden claims: production readiness, implemented OpenClaw/MCP/A2A, GovEngine owning Ravenclaw runtime;
- required `defer until Tecrax proves need` language for cross-profile candidates;
- required `keep in Ravenclaw` language for Logdash, executor, auto-campaign runtime, and finding taxonomy;
- required `already covered by GovEngine; maintain projection adapter` language for the current projection adapters.

## GovEngine Impact

This roadmap does not require a new GovEngine host projection. GovEngine 0.11 alpha
already has the relevant public surfaces:

- runtime shell;
- planning contracts;
- admission/policy contracts;
- runner supervision;
- evidence review;
- domain profile SDK;
- runtime contract proofs.

Future GovEngine changes should be small and contract-first. A new surface is
justified only when it is profile-neutral, deterministic, testable without
Logdash/filesystem state/credentials/network/live subprocesses, and useful for
Ravenclaw plus at least one other profile.

## Ravenclaw Impact

Ravenclaw gains a clearer roadmap and less pressure to move behavior for its own
sake. The runtime can continue to mature while projecting neutral evidence into
GovEngine/SCLite contracts.

The migration burden is mostly test discipline:

- keep projection adapters covered;
- keep public docs aligned with dependency baselines;
- keep non-claims explicit;
- prevent raw targets, commands, credentials, local storage paths, and carrier
  payloads from entering GovEngine-shaped artifacts.

## Final Recommendation

Extract now: no new GovEngine extraction. Ravenclaw has taken host ownership of
the active security action/tooling, policy/scope, and security review
interpretation implementation while retaining the published GovEngine optional
compatibility surface.

Use existing GovEngine API now: state/control projections, planning projection,
admission projection, runner-supervision projection, and review projection.

Extract later as contract: runtime-owned artifact descriptors and a possible
neutral reason-code registry, only after cross-profile evidence exists.

Defer until Tecrax proves need: evaluation/replay metrics, state-file manifest
shape, and scheduler/queue abstractions beyond snapshots.

Keep in Ravenclaw: Logdash, security campaign runtime, finding taxonomy,
security qualification, public demo UX, and carrier adapter implementation.

Keep implementation in Ravenclaw while allowing future neutral contracts:
queue mutation, auto-campaign runtime, concrete execution, and live backend
decisions.
