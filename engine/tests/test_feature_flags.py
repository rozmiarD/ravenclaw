from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from feature_flags import normalize_pipeline_flags  # type: ignore


def test_normalize_pipeline_flags_drops_dead_contextual_reeval_and_unifies_oos_cap() -> None:
    out = normalize_pipeline_flags({
        'enable_contextual_reeval': True,
        'out_of_scope_max_aggression': 4,
        'out_of_scope_allowed_aggression': 2,
    })
    assert 'enable_contextual_reeval' not in out
    assert out['out_of_scope_aggression_cap'] == 2
    assert out['out_of_scope_max_aggression'] == 2
    assert out['out_of_scope_allowed_aggression'] == 2


def test_normalize_pipeline_flags_profiles_drive_runtime_knobs() -> None:
    out = normalize_pipeline_flags({
        'plan_adaptation_mode': 'frozen',
        'planner_reconsult_mode': 'aggressive',
        'family_decay_mode': 'strong',
        'workflow_escalation_profile': 'balanced',
        'confirm_jobs_profile': 'conservative',
        'qualification_threshold': 'confirmed',
    })
    assert out['freeze_plan_revision'] is True
    assert out['dynamic_plan_adaptation'] is True
    assert out['aggressive_adaptation'] is False
    assert out['planner_reconsult_on_high_signal'] is True
    assert out['planner_reconsult_min_interval_runs'] == 6
    assert out['planner_reconsult_signal_threshold'] == 8
    assert out['family_decay_enabled'] is True
    assert out['family_decay_window_runs'] == 12
    assert out['family_decay_penalty'] == 0.18
    assert out['enable_followups'] is True
    assert out['weak_signal_positive_bridge'] is False
    assert out['safe_dual_action_enabled'] is True
    assert out['enable_confirm_jobs'] is True
    assert out['confirm_job_cooldown_sec'] == 1800
    assert out['max_confirm_jobs_total'] == 10
    assert out['qualification_promising_threshold'] == 'confirmed'
    assert out['qualification_followup_threshold'] == 'confirmed'


def test_normalize_pipeline_flags_derives_profiles_from_legacy_knobs() -> None:
    out = normalize_pipeline_flags({
        'planner_reconsult_on_high_signal': True,
        'planner_reconsult_min_interval_runs': 6,
        'planner_reconsult_signal_threshold': 8,
        'dynamic_plan_adaptation': True,
        'freeze_plan_revision': True,
        'family_decay_enabled': True,
        'family_decay_window_runs': 36,
        'family_decay_penalty': 0.08,
        'enable_confirm_jobs': False,
        'qualification_promising_threshold': 'weak_signal',
        'qualification_followup_threshold': 'probable',
    })
    assert out['planner_reconsult_mode'] == 'aggressive'
    assert out['plan_adaptation_mode'] == 'frozen'
    assert out['family_decay_mode'] == 'light'
    assert out['confirm_jobs_profile'] == 'off'
    assert out['qualification_threshold'] == 'custom'


def test_normalize_pipeline_flags_aggressive_confirm_profile_expands_caps() -> None:
    out = normalize_pipeline_flags({'confirm_jobs_profile': 'aggressive'})
    assert out['enable_confirm_jobs'] is True
    assert out['max_confirm_jobs_per_target'] == 2
    assert out['confirm_job_cooldown_sec'] == 300
    assert out['max_confirm_jobs_total'] == 40
    assert out['max_confirm_jobs_per_class'] == 12


def test_normalize_pipeline_flags_aggressive_workflow_profile_expands_followup_caps() -> None:
    out = normalize_pipeline_flags({'workflow_escalation_profile': 'aggressive'})
    assert out['enable_followups'] is True
    assert out['max_followups_per_target'] == 4
    assert out['followup_cooldown_sec'] == 180
    assert out['qualification_shadow_workflow_bridge'] is True
    assert out['candidate_partial_followup_bridge'] is True
    assert out['weak_signal_positive_bridge'] is True


def test_normalize_pipeline_flags_clamps_hidden_host_health_cooldown() -> None:
    out = normalize_pipeline_flags({'host_health_cooldown_sec': 30})
    assert out['host_health_cooldown_sec'] == 60
    out = normalize_pipeline_flags({'host_health_cooldown_sec': 9000})
    assert out['host_health_cooldown_sec'] == 7200


def test_normalize_pipeline_flags_clamps_hidden_deep_budget_cap() -> None:
    out = normalize_pipeline_flags({'deep_budget_cap_per_host_family': 0})
    assert out['deep_budget_cap_per_host_family'] == 1
    out = normalize_pipeline_flags({'deep_budget_cap_per_host_family': 99})
    assert out['deep_budget_cap_per_host_family'] == 8


def test_normalize_pipeline_flags_clamps_precheck_burst_controls() -> None:
    out = normalize_pipeline_flags({'precheck_burst_cooldown_threshold': 1, 'precheck_burst_cooldown_sec': 10})
    assert out['precheck_burst_cooldown_threshold'] == 2
    assert out['precheck_burst_cooldown_sec'] == 60
    out = normalize_pipeline_flags({'precheck_burst_cooldown_threshold': 999, 'precheck_burst_cooldown_sec': 99999})
    assert out['precheck_burst_cooldown_threshold'] == 50
    assert out['precheck_burst_cooldown_sec'] == 3600


def test_normalize_pipeline_flags_clamps_host_fail_streak_backoff_controls() -> None:
    out = normalize_pipeline_flags({'host_fail_streak_backoff_step_sec': -1, 'host_fail_streak_backoff_cap_sec': -5})
    assert out['host_fail_streak_backoff_step_sec'] == 0.0
    assert out['host_fail_streak_backoff_cap_sec'] == 0.0
    out = normalize_pipeline_flags({'host_fail_streak_backoff_step_sec': 9, 'host_fail_streak_backoff_cap_sec': 99})
    assert out['host_fail_streak_backoff_step_sec'] == 5.0
    assert out['host_fail_streak_backoff_cap_sec'] == 10.0
    out = normalize_pipeline_flags({'host_fail_streak_backoff_step_sec': 1.5, 'host_fail_streak_backoff_cap_sec': 0.5})
    assert out['host_fail_streak_backoff_step_sec'] == 1.5
    assert out['host_fail_streak_backoff_cap_sec'] == 1.5


def test_normalize_pipeline_flags_clamps_transport_cooldown_controls() -> None:
    out = normalize_pipeline_flags({
        'transport_observation_cooldown_sec': 10,
        'http_403_streak_threshold': 0,
        'http_403_cooldown_sec': 10,
        'code000_session_cooldown_sec': 10,
    })
    assert out['transport_observation_cooldown_sec'] == 60
    assert out['http_403_streak_threshold'] == 1
    assert out['http_403_cooldown_sec'] == 60
    assert out['code000_session_cooldown_sec'] == 300
    out = normalize_pipeline_flags({
        'transport_observation_cooldown_sec': 99999,
        'http_403_streak_threshold': 999,
        'http_403_cooldown_sec': 999999,
        'code000_session_cooldown_sec': 999999,
    })
    assert out['transport_observation_cooldown_sec'] == 3600
    assert out['http_403_streak_threshold'] == 20
    assert out['http_403_cooldown_sec'] == 86400
    assert out['code000_session_cooldown_sec'] == 172800
