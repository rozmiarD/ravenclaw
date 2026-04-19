# Logdash System Settings – Pipeline Flags

Source of truth:
- `engine/feature_flags.py`
- `engine/feature_flags_manifest.json`

This document reflects the **rationalized operator surface**:
- **System Settings** = global runtime / pipeline behavior
- **Campaign Setup** = campaign-scoped limits, credentials, request decoration
- some raw knobs remain for compatibility / expert tuning, but the main operator surface now prefers **profiles** over clusters of independent toggles

## Core operator-facing controls (System Settings)

### Presets
System Settings also exposes named multi-field presets for fast operator posture changes:
- `exploratory-efficient` — creative/signal-efficient search posture
- `exploratory-max` — higher-pressure exploratory posture with stronger follow-up + confirm fanout
- `confirmation-heavy` — tighter proof-oriented posture for validating already-promising paths
- `custom` — current config no longer exactly matches a named preset

Presets are a UI convenience layered on top of the canonical normalized pipeline config. They reuse the same `/api/pipeline-config` save path rather than introducing a separate preset persistence API.

System Settings also reflects effective posture metadata from `/api/pipeline-config/meta` so the operator can distinguish the current draft posture from the persisted normalized posture.

### Profiles
- `plan_adaptation_mode` — `off` | `balanced` | `aggressive` | `frozen`
- `planner_reconsult_mode` — `off` | `conservative` | `balanced` | `aggressive`
- `workflow_escalation_profile` — `off` | `conservative` | `balanced` | `aggressive`
- `confirm_jobs_profile` — `off` | `conservative` | `standard` | `aggressive`
- `family_decay_mode` — `off` | `light` | `standard` | `strong`

### Core execution / qualification
- `enable_analysis` — enable ANALYSIS stage
- `enable_light` — enable LIGHT summary stage
- `execution_mode` — `normalized` | `faithful`
- `qualification_mode` — `shadow` | `enforce`
- `qualification_threshold` — `none` | `weak_signal` | `probable` | `confirmed` | `custom`
- `out_of_scope_aggression_cap` — canonical out-of-scope aggression ceiling (1–10)

## Expert runtime controls still available in System Settings

### Debug / prompt / deterministic behavior
- `verbose_commands`
- `experimental_payloads`
- `analysis_min_bytes` (0–2048)
- `context_history` (1–20)
- `json_contract_retries` (0–3)
- `prompt_token_budget` (0–1250)
- `auditor_prompt_token_budget` (0–2000)
- `strict_deterministic`
- `policy_diag_logging`
- `force_auth_like_weak_on_http_controls`
- `queue_preemption_in_curated_loop`
- `autodiscover_deep_skip`

### Workflow / planner / adaptation raw overrides
These remain available as expert overrides even though the preferred operator surface is profile-driven.
- `enable_followups`
- `max_followups_per_target` (0–20)
- `planner_reconsult_on_high_signal`
- `planner_reconsult_min_interval_runs` (1–200)
- `planner_reconsult_signal_threshold` (1–20)
- `dynamic_plan_adaptation`
- `freeze_plan_revision`
- `aggressive_adaptation`

### Qualification / bridge / escalation raw overrides
- `qualification_shadow_workflow_bridge`
- `candidate_partial_followup_bridge`
- `weak_signal_positive_bridge`
- `evidence_bearing_followup_bridge`
- `early_precision_for_high_leverage_families`
- `qualification_promising_threshold` — `none` | `weak_signal` | `probable` | `confirmed`
- `qualification_followup_threshold` — `none` | `weak_signal` | `probable` | `confirmed`
- `high_leverage_precision_families`

### Confirm-job raw overrides
- `enable_confirm_jobs`
- `max_confirm_jobs_per_target` (0–5)
- `confirm_job_cooldown_sec` (60–7200)
- `max_confirm_jobs_total` (1–200)
- `max_confirm_jobs_per_class` (1–50)

### Family steering / decay raw overrides
- `family_lane_boost`
- `family_lane_suppress`
- `host_family_lane_boost`
- `host_family_lane_suppress`
- `family_decay_enabled`
- `family_decay_window_runs` (6–120)
- `family_decay_penalty` (0.0–0.5)

### Failure / cooldown guardrails
- `code000_streak_threshold` (1–10)
- `code000_session_cap` (1–20)
- `code000_cooldown_sec` (60–86400)

## Hidden compatibility flags (runtime only)
These are intentionally **not** first-class UI controls, but still exist in the normalized runtime config.
- `safe_dual_action_enabled`
- `dual_action_allowed_families`
- `followup_cooldown_sec` (60–7200) — raw runtime override kept behind the workflow escalation profile instead of becoming a first-class slider
- `host_health_cooldown_sec` (60–7200) — execution-gate cooldown for host-health suppression without promoting another UI control
- `deep_budget_cap_per_host_family` (1–8) — bounded cap for deep/followup attempts per host-family pair without promoting another UI control
- `precheck_burst_cooldown_threshold` (2–50) — dedup-burst count before precheck temporarily cools down a noisy host
- `precheck_burst_cooldown_sec` (60–3600) — cooldown applied after the dedup-burst threshold is hit
- `host_fail_streak_backoff_step_sec` (0.0–5.0) — per-streak sleep step for precheck throttling on repeated host failures
- `host_fail_streak_backoff_cap_sec` (0.0–10.0) — cap for that precheck sleep backoff
- `transport_observation_cooldown_sec` (60–3600) — initial cooldown when transport-layer 403/code000 observations first appear
- `http_403_streak_threshold` (1–20) — 403 streak count before escalating to a longer cooldown
- `http_403_cooldown_sec` (60–86400) — longer cooldown for persistent 403 streaks
- `code000_session_cooldown_sec` (300–172800) — cooldown when code000 session-cap suppression triggers
- `out_of_scope_max_aggression` — legacy alias retained for compatibility; derived from `out_of_scope_aggression_cap`
- `out_of_scope_allowed_aggression` — legacy alias retained for compatibility; derived from `out_of_scope_aggression_cap`

## Campaign-scoped controls (Campaign Setup)
These no longer belong in System Settings.
- `credentials_required`
- `allow_auth_header`
- `allow_cookie_header`
- `allow_basic_auth`
- `bug_bounty_username`
- `test_account_email`
- `request_decoration`
- `max_runs`
- `target_load_limit`
- `time_budget_min`
- `retry_policy` — `strict` | `balanced` | `aggressive`

## Removed / deprecated from operator surface
- `enable_contextual_reeval` — removed as dead/no-op operator control

## Maintenance rule
If `feature_flags.py`, `feature_flags_manifest.json`, the System Settings UI, Campaign Setup UI, and this file disagree, update them together and run `engine/verify_feature_flags.py`.
