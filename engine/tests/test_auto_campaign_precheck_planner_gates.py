from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_precheck import evaluate_runtime_task_admission, precheck_and_prepare_task  # type: ignore


def test_evaluate_runtime_task_admission_blocks_late_phase_without_stage_signal() -> None:
    allowed, reason = evaluate_runtime_task_admission(
        runtime_task={'activation_phase': 'bounded_exploit_proof'},
        host_state={'hosts': {'a.example.com': {}}},
        host='a.example.com',
        mode='followup',
    )
    assert allowed is False
    assert reason == 'planner_activation_phase_skip'


def test_evaluate_runtime_task_admission_allows_late_phase_with_stage_signal() -> None:
    allowed, reason = evaluate_runtime_task_admission(
        runtime_task={'activation_phase': 'bounded_exploit_proof'},
        host_state={'hosts': {'a.example.com': {'max_ladder_stage': 'bounded_exploit_proof'}}},
        host='a.example.com',
        mode='followup',
    )
    assert allowed is True
    assert reason == 'allowed'


def test_evaluate_runtime_task_admission_blocks_conditional_gate_without_boundary_or_auth() -> None:
    allowed, reason = evaluate_runtime_task_admission(
        runtime_task={'conditional_gate': 'authenticated_or_boundary_mapping'},
        host_state={'hosts': {'a.example.com': {}}},
        host='a.example.com',
        mode='followup',
    )
    assert allowed is False
    assert reason == 'planner_conditional_gate_skip'


def test_evaluate_runtime_task_admission_blocks_background_surface_for_deep_mode_without_promotion() -> None:
    allowed, reason = evaluate_runtime_task_admission(
        runtime_task={'surface_role': 'background', 'expected_depth': 'deep'},
        host_state={'hosts': {'a.example.com': {}}},
        host='a.example.com',
        mode='precision',
    )
    assert allowed is False
    assert reason == 'planner_surface_role_skip'


def test_evaluate_runtime_task_admission_blocks_on_synthesis_abandon_for_deeper_mode() -> None:
    allowed, reason = evaluate_runtime_task_admission(
        runtime_task={
            'task_family': 'recon',
            'planning_ladder': {'next_stage': 'validation'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'marketing'}, 'target_surface_rationale': []},
        },
        host_state={'hosts': {'a.example.com': {}}},
        host='a.example.com',
        mode='followup',
        planner_feedback={'branch_quality_rate_recent': 0.1, 'dead_end_pressure_recent': 0.2},
    )
    assert allowed is False
    assert reason == 'planner_synthesis_skip'


def test_precheck_and_prepare_task_records_planner_gate_skip() -> None:
    gate_skip_count = {}
    gate_skip_examples = {}
    logged = []
    prepared = precheck_and_prepare_task(
        objective='Validate exploit path',
        target='https://a.example.com/',
        mode='followup',
        task_family='authz',
        dedup_mode_suffix=False,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=True,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={'hosts': {'a.example.com': {}}},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        dedup_key_fn=lambda objective, target: ('a.example.com', 'authz', 'sig'),
        family_allowed_fn=lambda *_args, **_kwargs: True,
        log_skip=lambda reason, host, detail: logged.append((reason, host, detail)),
        increment_precheck_skip=lambda: None,
        on_executed_key=lambda: None,
        runtime_task={'activation_phase': 'bounded_exploit_proof'},
        gate_skip_count=gate_skip_count,
        gate_skip_examples=gate_skip_examples,
    )
    assert prepared['allowed'] is False
    assert prepared['reason_code'] == 'planner_activation_phase_skip'
    assert gate_skip_count['planner_activation_phase_skip'] == 1
    assert gate_skip_examples['planner_activation_phase_skip'][0].startswith('https://a.example.com/')
    assert logged and logged[0][0] == 'planner_activation_phase_skip'
