#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'engine'
LOGDASH = ROOT / 'logdash'
FEATURE_FLAGS_PATH = ENGINE / 'feature_flags.py'
MANIFEST_PATH = ENGINE / 'feature_flags_manifest.json'
UI_PATH = LOGDASH / 'templates' / 'system_settings.html'
CAMPAIGN_UI_PATH = LOGDASH / 'templates' / 'campaign_setup.html'
DOC_PATH = LOGDASH / 'PIPELINE_FLAGS.md'

SYSTEM_UI_KEYS = {
    'enable_analysis', 'enable_light', 'verbose_commands', 'experimental_payloads',
    'analysis_min_bytes', 'context_history', 'json_contract_retries', 'prompt_token_budget', 'auditor_prompt_token_budget',
    'execution_mode', 'qualification_mode', 'qualification_threshold',
    'plan_adaptation_mode', 'planner_reconsult_mode', 'workflow_escalation_profile', 'confirm_jobs_profile', 'family_decay_mode',
    'enable_followups', 'planner_reconsult_on_high_signal', 'dynamic_plan_adaptation', 'freeze_plan_revision', 'aggressive_adaptation',
    'max_followups_per_target', 'planner_reconsult_min_interval_runs', 'planner_reconsult_signal_threshold',
    'family_decay_enabled', 'family_decay_window_runs', 'family_decay_penalty',
    'family_lane_boost', 'family_lane_suppress', 'host_family_lane_boost', 'host_family_lane_suppress',
    'enable_confirm_jobs', 'strict_deterministic', 'qualification_shadow_workflow_bridge', 'candidate_partial_followup_bridge',
    'weak_signal_positive_bridge', 'evidence_bearing_followup_bridge', 'early_precision_for_high_leverage_families',
    'high_leverage_precision_families', 'max_confirm_jobs_per_target', 'confirm_job_cooldown_sec', 'max_confirm_jobs_total', 'max_confirm_jobs_per_class',
    'autodiscover_deep_skip', 'policy_diag_logging', 'force_auth_like_weak_on_http_controls', 'queue_preemption_in_curated_loop',
    'code000_streak_threshold', 'code000_session_cap', 'code000_cooldown_sec',
    'qualification_promising_threshold', 'qualification_followup_threshold',
    'out_of_scope_aggression_cap',
}

CAMPAIGN_UI_KEYS = {
    'credentials_required', 'allow_auth_header', 'allow_cookie_header', 'allow_basic_auth',
    'bug_bounty_username', 'test_account_email', 'request_decoration',
    'max_runs', 'target_load_limit', 'time_budget_min', 'retry_policy',
}

HIDDEN_COMPAT_KEYS = {
    'safe_dual_action_enabled', 'dual_action_allowed_families',
    'followup_cooldown_sec', 'host_health_cooldown_sec', 'deep_budget_cap_per_host_family',
    'precheck_burst_cooldown_threshold', 'precheck_burst_cooldown_sec',
    'host_fail_streak_backoff_step_sec', 'host_fail_streak_backoff_cap_sec',
    'transport_observation_cooldown_sec', 'http_403_streak_threshold', 'http_403_cooldown_sec', 'code000_session_cooldown_sec',
    'out_of_scope_max_aggression', 'out_of_scope_allowed_aggression',
}

LEGACY_REMOVED_KEYS = {'enable_contextual_reeval'}


def load_defaults() -> dict[str, object]:
    spec = importlib.util.spec_from_file_location('feature_flags_verify', FEATURE_FLAGS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    defaults = getattr(module, 'PIPELINE_FLAG_DEFAULTS', None)
    if not isinstance(defaults, dict):
        raise RuntimeError('PIPELINE_FLAG_DEFAULTS not found')
    return dict(defaults)


def main() -> None:
    defaults = load_defaults()
    manifest_raw = json.loads(MANIFEST_PATH.read_text())
    manifest = manifest_raw.get('flags') if isinstance(manifest_raw, dict) and isinstance(manifest_raw.get('flags'), dict) else manifest_raw
    ui_text = UI_PATH.read_text()
    campaign_ui_text = CAMPAIGN_UI_PATH.read_text()
    docs_text = DOC_PATH.read_text()

    default_keys = set(defaults)
    manifest_keys = set(manifest)
    if default_keys != manifest_keys:
        missing_manifest = sorted(default_keys - manifest_keys)
        extra_manifest = sorted(manifest_keys - default_keys)
        raise SystemExit(f'manifest mismatch: missing={missing_manifest} extra={extra_manifest}')

    for key in LEGACY_REMOVED_KEYS:
        if key in default_keys or key in manifest_keys or key in ui_text or key in campaign_ui_text:
            raise SystemExit(f'legacy key still present: {key}')

    unknown_system = sorted(SYSTEM_UI_KEYS - default_keys)
    unknown_campaign = sorted(CAMPAIGN_UI_KEYS - ({*default_keys} | CAMPAIGN_UI_KEYS))
    unknown_hidden = sorted(HIDDEN_COMPAT_KEYS - default_keys)
    if unknown_system or unknown_campaign or unknown_hidden:
        raise SystemExit(f'classification mismatch: system={unknown_system} campaign={unknown_campaign} hidden={unknown_hidden}')

    missing_ui = sorted(key for key in SYSTEM_UI_KEYS if key not in ui_text)
    if missing_ui:
        raise SystemExit(f'system settings missing keys: {missing_ui}')

    missing_campaign_ui = sorted(key for key in CAMPAIGN_UI_KEYS if key not in campaign_ui_text)
    if missing_campaign_ui:
        raise SystemExit(f'campaign setup missing keys: {missing_campaign_ui}')

    docs_required = sorted(default_keys | CAMPAIGN_UI_KEYS)
    missing_docs = sorted(key for key in docs_required if key not in docs_text)
    if missing_docs:
        raise SystemExit(f'docs missing keys: {missing_docs}')

    print('feature flag verification: OK')
    print(f'defaults={len(default_keys)} system_ui={len(SYSTEM_UI_KEYS)} campaign_ui={len(CAMPAIGN_UI_KEYS)} hidden={len(HIDDEN_COMPAT_KEYS)}')


if __name__ == '__main__':
    main()
