# RAVENCLAW Architecture

This document is the operator/developer map of the current production architecture.

The runtime root is configurable with `RAVENCLAW_WORKSPACE`; when unset, Ravenclaw resolves the checkout root from the running script/module location. Do not hardcode historical operator-home paths in code or docs that describe portable public operation.

It complements `README.md` by describing the concrete runtime path, key modules, persisted state, and handoff contracts used by the live system.

---

## 1. Current production execution path

Canonical runtime path:

1. `logdash/app.py` + `logdash/api_*` + `logdash/services.py` — operator-facing control plane and shared projection/service layer
2. `engine/auto_campaign.py` / `engine/auto_campaign_runner.py` + adjacent `engine/runtime_*` modules — long-lived campaign orchestration, loop/session flow, queueing, runtime control, and persistence
3. `engine/runtime_plan_service.py` + `engine/runtime_task_schema.py` — planner→runtime transformation and canonical runtime-plan persistence
4. `engine/run_pipeline.py` + extracted `engine/pipeline_*` stage modules — single-task governed pipeline
5. `engine/executor.py` — final command construction + execution from approved artifacts
6. `engine/plan_campaign.py` + `engine/planer/*` — deterministic campaign planning and blueprint generation

Reference: `engine/RUNTIME_MANIFEST.md`.
Version milestone intent is tracked separately in `VERSION_ROADMAP.md` so architecture cleanup and release thresholds stay aligned.

---

## 2. High-level component model

### Planner
Responsible for turning operator input and scope text into an immutable campaign blueprint.
The parser core is deterministic, but the full planning pipeline may record either deterministic or hybrid provenance when LLM-assisted interpretation/reconciliation contributes.

Main files:
- `engine/plan_campaign.py`
- `engine/planer/parser.py`
- `engine/planer/interpretation.py`
- `engine/planer/blueprint.py`
- `engine/planer/planner.py`
- `engine/planer/registry.py`
- `engine/planer/schema.py`

Outputs:
- immutable campaign versions in `reports/campaign_registry/<campaign_key>/`
- `blueprint.json`
- `blueprint.yaml`
- overlay templates in `templates/`

Registry note:
- new planner history is keyed by stronger `planner_identity_hash` semantics rather than raw `source_hash` alone
- legacy source-hash-keyed registry entries remain readable for backward compatibility

### Runtime plan service
Transforms approved blueprint data into executable runtime tasks.

Main files:
- `engine/runtime_plan_service.py`
- `engine/runtime_campaign_state.py`
- `engine/runtime_task_schema.py`
- `engine/planer/planner_intent_contract.py`
- `reports/state/public_targets_plan.json`
- `reports/.runtime_plan.meta.json`

Responsibilities:
- selected campaign resolution
- runtime-plan generation and regeneration
- runtime-plan metadata persistence
- planner UI state synchronization
- preservation of planner semantic intent (`runtime_task_contract`, `planning_ladder`, `planner_rationale`, target-surface rationale) into runtime-plan entries
- canonical normalization of planner/runtime bridge fields before orchestration consumes them

### Orchestrator / auto-campaign runtime
Runs long-lived campaign loops, prioritizes work, tracks host state, and persists findings.

Main files:
- `engine/auto_campaign_runner.py`
- `engine/auto_campaign.py`
- `engine/runtime_loop_control.py`
- `engine/runtime_session_flow.py`
- `engine/runtime_task_execution.py`
- `engine/runtime_execution_gate.py`
- `engine/auto_campaign_precheck.py`
- `engine/auto_campaign_*.py`

Responsibilities:
- queue and loop management
- host/family prioritization
- precheck/execution admission and runtime-control honoring
- post-run followup decisions
- qualification and finding lifecycle
- campaign state persistence
- planner reconsult triggers
- bounded planner-governed runtime enforcement for activation/gating/depth/cluster/surface-role semantics

### Single-task governed pipeline
Runs one task through role-separated reasoning and controlled execution.

Main files:
- `engine/run_pipeline.py`
- `engine/pipeline_context.py`
- `engine/pipeline_planning.py`
- `engine/pipeline_governance.py`
- `engine/pipeline_execution.py`
- `engine/pipeline_postprocess.py`
- `engine/contracts.py`
- `engine/runtime_signal_eval.py`
- `engine/status_utils.py`

Pipeline stages:
1. load config + recent context
2. load planner hints
3. BRAIN proposes one `ActionSpec`
4. local contract validation
5. policy gate evaluates scope/auth/tool constraints
6. AUDITOR approves / rejects / requests owner approval
7. deterministic scope correction safeguards auditor drift
8. EXECUTION ENGINE builds argv and executes or dry-runs
9. ANALYSIS interprets artifacts/signals
10. LIGHT formats concise operator summary
11. context + telemetry persisted

### Policy and governance layer
Runtime enforcement primitives and tool/scope/auth rules.

Main files:
- `engine/security_policy_gateway.py`
- `engine/campaign_utils.py`
- `engine/security_policy_core.py`
- `engine/security_tool_registry.py`
- `engine/security_action_compiler.py`
- `engine/security_action_validators.py`
- `engine/security_capability_recipes.py`
- `engine/security_semantic_loss_policy.py`
- `policy.yaml`
- `whitelist.yaml`
- `campaign.md`
- `budgets.yaml`
- `proxy.yaml`

Responsibilities:
- executor allowlist
- BRAIN planning-safe tool subset
- banned pattern checks
- auth and credential policy
- scope gating
- aggression bounds and owner override semantics

### Execution engine
The only layer allowed to build final command argv.

Main file:
- `engine/executor.py`

Responsibilities:
- load policy + whitelist
- normalize tool invocation
- prepare output paths
- enforce scope before execution
- run command in dry-run or live mode
- record stdout/stderr/returncode

### Evidence / qualification layer
Turns raw output into structured findings and governs escalation.

Main files:
- `engine/analysis.py`
- `engine/security_signal_contract.py`
- `engine/security_analysis_contract.py`
- `engine/security_evidence_policy.py`
- `engine/vuln_qualification.py`
- `engine/proof_protocols.py`
- `engine/auto_campaign_qualification.py`

### Evaluation / replay layer
Phase-5 evaluation consumes canonical runtime artifacts and produces deterministic replay outputs, fixture-based checks, and governance-aware effectiveness metrics.

Main files:
- `engine/evaluation_bundle.py`
- `engine/evaluation_replay.py`
- `engine/evaluation_metrics.py`
- `engine/evaluation_variants.py`
- `engine/evaluation_fixtures.py`

Responsibilities:
- bounded replay bundle/dataset construction
- decision-only and dataset replay without live execution by default
- metric aggregation that separates yield from governance friction
- offline variant comparison
- machine-readable evaluation exports for archived campaign outputs

### Operator control plane (Logdash)
Flask + SQLite dashboard that exposes runtime state, control actions, planning flow, logs, and evaluation-aware operator truth surfaces.

Main files:
- `logdash/app.py`
- `logdash/services.py`
- `logdash/state.py`
- `logdash/db.py`
- `logdash/log_event.py`
- `logdash/api_runtime.py`
- `logdash/api_supplemental.py`
- `logdash/api_planner.py`
- `logdash/templates/*`
- `logdash/static/styles.css`

Responsibilities:
- campaign setup and selection
- planner approval and candidate review
- runtime plan generation / validation / view
- owner actions and override surfaces
- system settings / pipeline flags
- real runtime start / pause / stop control
- runtime log browsing
- exploit-ladder / evidence-truth visibility from canonical runtime artifacts
- planner/runtime trace visibility for latest run state
- evaluation/governance summary visibility from replay outputs
- state synchronization with orchestrator files through shared service/state helper paths rather than ad hoc API-local file logic where possible

---

## 3. Repository map

### Core runtime and policy
- `engine/` — execution, planning, orchestration, policy, contracts, qualification
- `logdash/` — operator UI/control plane
- `tests/`, `engine/tests/`, `engine/planer/tests/` — unit/integration coverage

### Configuration and governance
- `campaign.md` — active campaign/scope description
- `policy.yaml` — runtime policy configuration
- `whitelist.yaml` — tool allowlist and BRAIN subset
- `budgets.yaml` — token/cost/budget controls
- `proxy.yaml` — proxy/anonymization policy

### Persisted runtime artifacts
- `reports/` — mixed runtime artifact area: local control-plane state, generated snapshots, generated history, and the durable `campaign_registry/` planner history
- `logs/` — execution logs
- `memory/` — long-term memory and historical notes
- `scope/` — source scope text files

Operational note:
- `reports/campaign_registry/` is the durable planning history / blueprint registry.
- most `reports/.*.json` dotfiles are live local runtime/control-plane state, not durable repo artifacts.
- canonical generated runtime artifacts live under `reports/state/` and `reports/cache/` and are defined in `engine/paths.py`.
- `engine/public_targets_plan.json` and `engine/context_summary.json` remain legacy compatibility mirrors during the transition.
- `references/runtime-artifact-ownership.md` is the short operator/developer reference for canonical-versus-legacy runtime artifact ownership.

### Auxiliary areas
- `auth-harness/` — auth-related execution harness
- `playbooks/` — operator/research playbooks
- `workspace-brain/` — collected outputs/artifacts from probing runs

---

## 4. Handoff contracts

The live runtime relies on a few core data shapes.

### `ActionSpec`
Produced by BRAIN and validated before execution.

Expected fields:
- `intent`
- `target`
- `tool`
- `args`
- `constraints.aggression`

### Planner/runtime semantic contract
The planner/runtime bridge now carries a canonical semantic subset that is intentionally preserved instead of repeatedly re-derived from weaker hints.

Primary references:
- `engine/runtime_task_schema.py`
- `engine/planer/planner_intent_contract.py`
- `references/runtime-task-contract-v2.md`
- `references/planner-runtime-contract-map.md`
- `references/evaluation-replay-contract.md`
- `references/effectiveness-metrics-contract.md`

Planner-owned / planner-originated semantics:
- target identity and task intent
- `capability_candidates`
- `recommended_action_types`
- `evidence_goal`
- `exploit_ladder`
- `actor_requirements`
- `session_requirements`
- `promotion_policy`
- `contamination_policy`
- `approval_sensitivity`
- `planning_ladder`
- `planner_rationale.target_profile_summary`
- `planner_rationale.target_surface_rationale`

Runtime-owned / runtime-derived semantics:
- normalized `action_type`, `capability`, `experiment_shape`
- queue placement / semantic multiplier / effective blockers
- host-state learning summaries
- regeneration / reconsult decisions
- execution-specific tool/compiler choices

Compatibility rule:
- family-first heuristics may still exist as backward-compatible fallbacks,
  but the preferred path is explicit ladder + rationale semantics end-to-end.

### Lineage guarantees
The current runtime preserves semantic intent across these seams:
1. planner experiment intent emission
2. blueprint schema validation
3. runtime-plan generation / regeneration
4. queued followup / precision payloads
5. runtime decision / queue scoring / host-state learning
6. executor-facing runtime payload serialization
7. aggregate learning and planner feedback summaries

This means later stages should consume or forward canonical planner/runtime semantics rather than lossy family-only reconstructions whenever the richer contract is available.

### `AuditorDecision`
Produced by AUDITOR.

Expected fields:
- `decision` = `approve | reject | owner_approval_required`
- `reason_code`
- `reason`
- `risk_band`
- `owner_gate`
- `constraints.aggression`

### `ExecutionResult`
Produced by EXECUTION ENGINE.

Expected fields include:
- `status`
- `command`
- `argv`
- `returncode`
- `stdout`
- `stderr`

### `AnalysisPayload`
Produced by ANALYSIS.

Expected fields include:
- `observations`
- `evidence_artifacts`
- `security_signals`
- `findings`
- `risk`
- `confidence`
- `next_family_hint`
- `success_criteria_eval`

### `LightSummary`
Produced by LIGHT.

Expected fields:
- `summary`
- `next_step`

### `RuntimeTask`
Used by planner/runtime plan/orchestrator.

Common fields include:
- `objective`
- `target`
- `task_family`
- `acceptance_checks`
- `evidence_required`
- `recommended_tools`
- `priority_score`
- `cost_band`
- `expected_depth`
- `activation_phase`
- `activation_mode`
- `conditional_gate`
- `surface_role`
- `target_cluster`

Current truth note:
- these planner/runtime fields are not merely decorative; bounded runtime enforcement now exists in the orchestration/admission path for phase/mode/gate/depth/cluster/surface-role semantics.

---

## 5. State files and ownership

See `STATE_FILES.md` for a fuller catalog. The most important live files are:

- `reports/.planner.ui.state.json` — planner/control-plane UI selections
- `reports/.campaign.settings.json` — persisted runtime campaign settings
- `reports/.orchestrator.state.json` — selected campaign/orchestrator state
- `reports/.auto_campaign.state.json` — runner live status (`paused`, `stopped`, overrides)
- `reports/.runtime_plan.meta.json` — metadata for current runtime plan
- `reports/state/public_targets_plan.json` — executable runtime task list
- `reports/.host_state.json` — per-host learned runtime state
- `reports/findings-history.jsonl` — append-only finding/event history
- `reports/cache/context_summary.json` — compact recent pipeline context

Design rule:
- UI reads/writes state through service/helper layers where possible.
- Runtime and UI should not silently invent incompatible shapes for shared files.
- selected-campaign snapshot filtering/projection should be centralized in shared helpers rather than duplicated separately across API endpoints.

---

## 6. Control and approval flow

### Planning and activation
1. operator selects scope input
2. planner generates or reuses blueprint
3. blueprint is reviewed/approved
4. candidate targets may be promoted or rejected
5. runtime plan is generated from approved blueprint
6. runtime plan is validated
7. campaign key is activated

### Single-task execution
1. orchestrator selects next task
2. pipeline requests BRAIN proposal
3. local validation + policy gate check
4. AUDITOR decision
5. executor builds final argv
6. execution result stored and analyzed
7. followup/qualification logic decides next runtime actions

### Elevated/owner-gated paths
Examples:
- credentials/auth-like execution
- out-of-scope or policy-ambiguous activity
- risky actions requiring explicit owner acknowledgment

These should surface through owner-approval files/UI rather than being silently executed.

---

## 7. Maturity overview

This repository is a live research platform, not a sealed appliance.

Rough current maturity:
- Planner / blueprint registry — advanced
- Policy core / whitelist / scope gates — advanced
- Governed single-task pipeline — advanced
- Planner→runtime contract and runtime-plan shaping — advanced experimental
- Evaluation / replay / effectiveness exports — advanced experimental
- Logdash control plane — advanced experimental
- Auto-campaign adaptation logic — experimental
- Qualification and confirmation semantics — experimental
- State-file contracts and replayability — improving, partially formalized

---

## 8. Recommended reading order

If you are new to the codebase, read in this order:

1. `README.md`
2. `ARCHITECTURE.md`
3. `STATE_FILES.md`
4. `engine/RUNTIME_MANIFEST.md`
5. `whitelist.yaml`
6. `policy.yaml`
7. `engine/run_pipeline.py`
8. `engine/executor.py`
9. `engine/runtime_plan_service.py`
10. `engine/auto_campaign_runner.py`
11. `logdash/app.py`

---

## 9. Design intent in one sentence

RAVENCLAW is a policy-bound security orchestration system where planning may be adaptive, but authorization, execution, evidence handling, and operator control remain explicit and inspectable.
