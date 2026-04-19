from __future__ import annotations

import sys
import time
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_precheck import evaluate_runtime_task_admission, family_allowed_for_host_stage, host_health_blocked, precheck_and_prepare_task  # type: ignore


def test_evaluate_runtime_task_admission_returns_canonical_reason_code() -> None:
    allowed, reason_code = evaluate_runtime_task_admission(
        runtime_task={'expected_depth': 'light'},
        host_state={'hosts': {'api.example.com': {}}},
        host='api.example.com',
        mode='followup',
    )
    assert allowed is False
    assert reason_code == 'planner_expected_depth_skip'



def test_family_allowed_for_sensitive_host_allows_warmup_families() -> None:
    allow = family_allowed_for_host_stage(
        {'hosts': {}},
        'https://auth.example.com/',
        'recon',
        is_sensitive_host=lambda _t: True,
        host_warmup_complete=lambda _state, _target: False,
    )
    assert allow is True


def test_family_allowed_for_sensitive_host_blocks_heavy_family_before_warmup() -> None:
    allow = family_allowed_for_host_stage(
        {'hosts': {}},
        'https://auth.example.com/',
        'authz',
        is_sensitive_host=lambda _t: True,
        host_warmup_complete=lambda _state, _target: False,
    )
    assert allow is False



def test_family_allowed_for_sensitive_host_uses_stage_and_surface_learning() -> None:
    allow = family_allowed_for_host_stage(
        {'hosts': {'auth.example.com': {'preferred_stages': ['control_boundary_confirmation'], 'target_types_seen': ['auth'], 'target_surface_rationale': ['authenticated_or_boundary_mapping']}}},
        'https://auth.example.com/',
        'authz',
        is_sensitive_host=lambda _t: True,
        host_warmup_complete=lambda _state, _target: False,
    )
    assert allow is True


def test_host_health_blocked_only_for_deep_or_followup_and_high_fail_rate() -> None:
    success = {'a.example.com': 1}
    fail = {'a.example.com': 6}
    assert host_health_blocked('a.example.com', 'deep', success, fail) is True
    assert host_health_blocked('a.example.com', 'followup', success, fail) is True
    assert host_health_blocked('a.example.com', 'fast', success, fail) is False


def test_host_health_blocked_requires_enough_history() -> None:
    success = {'a.example.com': 0}
    fail = {'a.example.com': 4}
    assert host_health_blocked('a.example.com', 'deep', success, fail) is False


def test_precheck_returns_allowed_gate_payload_for_ready_task() -> None:
    result = precheck_and_prepare_task(
        objective='Recon',
        target='https://api.example.com/',
        mode='fast',
        task_family='recon',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'api.example.com': True},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
    )
    assert result['allowed'] is True
    assert result['reason_code'] == 'allowed'
    assert result['gate']['reason_code'] == 'allowed'
    assert result['gate']['family'] == 'recon'


def test_precheck_returns_blocked_gate_payload_for_cooldown() -> None:
    result = precheck_and_prepare_task(
        objective='Recon',
        target='https://api.example.com/',
        mode='fast',
        task_family='recon',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'api.example.com': True},
        host_cooldown_until={'api.example.com': 9999999999.0},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
    )
    assert result['allowed'] is False
    assert result['reason_code'] == 'host_cooldown'
    assert result['gate']['reason_code'] == 'host_cooldown'
    assert 'cooldown_active' in (result['gate'].get('blockers') or [])


def test_precheck_records_generic_execution_gate_skip_counts() -> None:
    gate_skip_count = {}
    gate_skip_examples = {}
    result = precheck_and_prepare_task(
        objective='Authz probe',
        target='https://auth.example.com/',
        mode='deep',
        task_family='authz',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'auth.example.com': True},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {'auth.example.com': {'state_band': 'warmup'}}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: False,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        gate_skip_count=gate_skip_count,
        gate_skip_examples=gate_skip_examples,
    )
    assert result['allowed'] is False
    assert result['reason_code'] == 'warmup_gate_skip'
    assert gate_skip_count['warmup_gate_skip'] == 1
    assert gate_skip_examples['warmup_gate_skip']


def test_precheck_uses_configured_burst_cooldown_after_repeated_dedup() -> None:
    host_cooldown_until = {}
    host_precheck_burst = {'api.example.com': 2}
    executed_keys = {('k', 'Recon', 'https://api.example.com/')}
    skip_count = {'count': 0}

    result = precheck_and_prepare_task(
        objective='Recon',
        target='https://api.example.com/',
        mode='fast',
        task_family='recon',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'api.example.com': True},
        host_cooldown_until=host_cooldown_until,
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=executed_keys,
        precheck_skip_examples=[],
        host_precheck_burst=host_precheck_burst,
        host_state={'hosts': {}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: skip_count.__setitem__('count', skip_count['count'] + 1),
        on_executed_key=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
        precheck_burst_cooldown_threshold=3,
        precheck_burst_cooldown_sec=120,
    )
    assert result['allowed'] is False
    assert result['reason_code'] == 'dedup_skip'
    assert skip_count['count'] == 1
    assert host_precheck_burst['api.example.com'] == 3
    assert 'api.example.com' in host_cooldown_until
    assert 100 <= (host_cooldown_until['api.example.com'] - time.time()) <= 120.5


def test_precheck_uses_configured_host_fail_streak_backoff(monkeypatch) -> None:
    slept = {'seconds': None}

    def fake_sleep(seconds: float) -> None:
        slept['seconds'] = seconds

    monkeypatch.setattr('auto_campaign_precheck.time.sleep', fake_sleep)
    result = precheck_and_prepare_task(
        objective='Recon',
        target='https://api.example.com/',
        mode='fast',
        task_family='recon',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'api.example.com': True},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {}},
        deep_budget={},
        host_fail_streak={'api.example.com': 5},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
        host_fail_streak_backoff_step_sec=0.3,
        host_fail_streak_backoff_cap_sec=1.0,
    )
    assert result['allowed'] is True
    assert slept['seconds'] == 1.0


def test_precheck_blocks_phase_gated_task_without_primary_signal() -> None:
    result = precheck_and_prepare_task(
        objective='Workflow probe',
        target='https://api.example.com/',
        mode='followup',
        task_family='workflow',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'api.example.com': True},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {'api.example.com': {'state_band': 'warmup'}}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
        runtime_task={'activation_phase': 2, 'activation_mode': 'if_signal', 'conditional_gate': 'stateful_or_boundary_signal', 'surface_role': 'primary'},
    )
    assert result['allowed'] is False
    assert result['reason_code'] == 'planner_activation_phase_skip'
    assert result['gate']['activation_phase'] == 2
    assert result['gate']['activation_mode'] == 'if_signal'


def test_precheck_allows_phase_gated_task_after_primary_signal() -> None:
    result = precheck_and_prepare_task(
        objective='Workflow probe',
        target='https://api.example.com/',
        mode='followup',
        task_family='workflow',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        host_dns_cache={'api.example.com': True},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {'api.example.com': {'state_band': 'promising'}}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={'api.example.com': 1},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
        runtime_task={'activation_phase': 2, 'activation_mode': 'if_signal', 'conditional_gate': 'surface_mapping_after_primary_signal', 'surface_role': 'primary'},
    )
    assert result['allowed'] is True
    assert result['gate']['activation_phase'] == 2
    assert result['gate']['conditional_gate'] == 'surface_mapping_after_primary_signal'


def test_precheck_exposes_synthesis_explainability_for_reporting_payloads() -> None:
    result = precheck_and_prepare_task(
        objective='Exploit branch followup',
        target='https://api.example.com/',
        mode='followup',
        task_family='authz',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'api.example.com': True},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {'api.example.com': {}}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
        runtime_task={
            'task_family': 'recon',
            'expected_depth': 'deep',
            'planning_ladder': {'next_stage': 'validation'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'marketing'}, 'target_surface_rationale': []},
        },
        planner_feedback={'branch_quality_rate_recent': 0.1, 'dead_end_pressure_recent': 0.2},
    )
    assert result['allowed'] is False
    assert result['reason_code'] == 'planner_synthesis_skip'
    assert result['gate']['synthesis_recommended_action'] == 'abandon'
    assert result['gate']['synthesis_reason'] == 'weak_validation_signal'
    assert result['gate']['synthesis_next_stage'] == 'validation'
    assert result['gate']['synthesis_gate_family'] == 'recon'


def test_precheck_blocks_background_only_gate_on_primary_surface() -> None:
    result = precheck_and_prepare_task(
        objective='Background mapping',
        target='https://cdn.example.com/',
        mode='fast',
        task_family='content_discovery',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'cdn.example.com': True},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('k', objective, target),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda *_args, **_kwargs: None,
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
        runtime_task={'activation_phase': 1, 'activation_mode': 'immediate', 'conditional_gate': 'background_surface_only', 'surface_role': 'primary'},
    )
    assert result['allowed'] is False
    assert result['reason_code'] == 'planner_conditional_gate_skip'
    assert 'planner_conditional_gate' in (result['gate'].get('blockers') or [])
