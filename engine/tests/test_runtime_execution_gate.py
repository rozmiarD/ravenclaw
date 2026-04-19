from __future__ import annotations

import sys
import time
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_execution_gate import evaluate_host_execution_gate  # type: ignore


def test_execution_gate_blocks_unresolved_host() -> None:
    gate = evaluate_host_execution_gate(
        objective='Recon',
        target='https://a.example.com/',
        mode='fast',
        task_family='recon',
        unresolved_hosts={'a.example.com'},
        host_dns_cache={},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {}},
        deep_budget={},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
    )
    assert gate.allowed is False
    assert gate.reason_code == 'unresolved_host'


def test_execution_gate_blocks_cooldown() -> None:
    gate = evaluate_host_execution_gate(
        objective='Recon',
        target='https://a.example.com/',
        mode='fast',
        task_family='recon',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={'a.example.com': 9999999999.0},
        autodiscover_deep_skip=False,
        host_state={'hosts': {}},
        deep_budget={},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
    )
    assert gate.allowed is False
    assert gate.reason_code == 'host_cooldown'


def test_execution_gate_blocks_deep_budget() -> None:
    gate = evaluate_host_execution_gate(
        objective='Authz probe',
        target='https://a.example.com/',
        mode='deep',
        task_family='authz',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {}},
        deep_budget={('a.example.com', 'authz'): 2},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'expected_depth': 'deep'},
    )
    assert gate.allowed is False
    assert gate.reason_code == 'deep_budget_skip'


def test_execution_gate_uses_configured_deep_budget_cap() -> None:
    gate = evaluate_host_execution_gate(
        objective='Workflow probe',
        target='https://a.example.com/',
        mode='followup',
        task_family='workflow',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {}},
        deep_budget={('a.example.com', 'workflow'): 3},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        deep_budget_cap_per_host_family=3,
    )
    assert gate.allowed is False
    assert gate.reason_code == 'deep_budget_skip'
    assert 'budget=3' in gate.detail


def test_execution_gate_uses_configured_host_health_cooldown() -> None:
    host_cooldown_until = {}
    gate = evaluate_host_execution_gate(
        objective='Workflow probe',
        target='https://a.example.com/',
        mode='followup',
        task_family='workflow',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until=host_cooldown_until,
        autodiscover_deep_skip=False,
        host_state={'hosts': {}},
        deep_budget={},
        host_success_count={'a.example.com': 1},
        host_fail_count={'a.example.com': 5},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        host_health_cooldown_sec=180,
    )
    assert gate.allowed is False
    assert gate.reason_code == 'host_health_skip'
    assert gate.cooldown_until is not None
    remaining = float(gate.cooldown_until or 0.0) - host_cooldown_until['a.example.com']
    assert abs(remaining) < 0.01
    assert 150 <= (host_cooldown_until['a.example.com'] - time.time()) <= 180.5


def test_execution_gate_accepts_semantic_activation_phase_strings() -> None:
    gate = evaluate_host_execution_gate(
        objective='Exploit proof',
        target='https://a.example.com/',
        mode='followup',
        task_family='authz',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {'state_band': 'exploitation'}}},
        deep_budget={},
        host_success_count={'a.example.com': 2},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'activation_phase': 'bounded_exploit_proof'},
    )
    assert gate.activation_phase == 3


def test_execution_gate_blocks_mode_deeper_than_expected_depth() -> None:
    gate = evaluate_host_execution_gate(
        objective='Content discovery pivot',
        target='https://a.example.com/',
        mode='followup',
        task_family='content_discovery',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {}}},
        deep_budget={},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'expected_depth': 'light'},
    )
    assert gate.allowed is False
    assert gate.reason_code == 'planner_expected_depth_skip'
    assert gate.expected_depth == 'light'


def test_execution_gate_blocks_shallow_cluster_followup_without_primary_signal() -> None:
    gate = evaluate_host_execution_gate(
        objective='Infra edge followup',
        target='https://a.example.com/',
        mode='followup',
        task_family='content_discovery',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {}}},
        deep_budget={},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'target_cluster': 'infra_edge', 'expected_depth': 'medium'},
    )
    assert gate.allowed is False
    assert gate.reason_code == 'planner_target_cluster_skip'
    assert gate.target_cluster == 'infra_edge'


def test_execution_gate_allows_shallow_cluster_followup_after_primary_signal() -> None:
    gate = evaluate_host_execution_gate(
        objective='Infra edge followup',
        target='https://a.example.com/',
        mode='followup',
        task_family='content_discovery',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {'state_band': 'promising'}}},
        deep_budget={},
        host_success_count={'a.example.com': 1},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'target_cluster': 'infra_edge', 'expected_depth': 'medium'},
    )
    assert gate.allowed is True


def test_execution_gate_blocks_on_synthesis_pivot_for_precision_without_primary_signal() -> None:
    gate = evaluate_host_execution_gate(
        objective='Exploit proof',
        target='https://a.example.com/',
        mode='precision',
        task_family='authz',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {}}},
        deep_budget={},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={
            'task_family': 'recon',
            'expected_depth': 'deep',
            'planning_ladder': {'next_stage': 'bounded_exploit_proof'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'api'}, 'target_surface_rationale': ['authenticated_or_boundary_mapping']},
        },
        planner_feedback={'dead_end_pressure_recent': 0.9, 'branch_quality_rate_recent': 0.1},
    )
    assert gate.allowed is False
    assert gate.reason_code == 'planner_synthesis_skip'


def test_execution_gate_blocks_if_signal_without_primary_signal() -> None:
    gate = evaluate_host_execution_gate(
        objective='Auth flow mapping',
        target='https://a.example.com/',
        mode='followup',
        task_family='auth_flow',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {}}},
        deep_budget={},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'activation_mode': 'if_signal', 'expected_depth': 'medium'},
    )
    assert gate.allowed is False
    assert gate.reason_code == 'planner_activation_mode_skip'


def test_execution_gate_blocks_if_confirmed_without_confirmed_signal() -> None:
    gate = evaluate_host_execution_gate(
        objective='Exploit proof',
        target='https://a.example.com/',
        mode='deep',
        task_family='authz',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {'state_band': 'promising'}}},
        deep_budget={},
        host_success_count={'a.example.com': 1},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'activation_mode': 'if_confirmed', 'expected_depth': 'deep'},
    )
    assert gate.allowed is False
    assert gate.reason_code == 'planner_activation_mode_skip'


def test_execution_gate_blocks_background_followup_without_confirmed_signal() -> None:
    gate = evaluate_host_execution_gate(
        objective='Background enrichment',
        target='https://a.example.com/',
        mode='followup',
        task_family='content_discovery',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {'surface_promoted': True, 'state_band': 'promising'}}},
        deep_budget={},
        host_success_count={'a.example.com': 1},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'activation_mode': 'background', 'surface_role': 'background', 'expected_depth': 'medium'},
    )
    assert gate.allowed is False
    assert gate.reason_code == 'planner_activation_mode_skip'


def test_execution_gate_allows_background_fast_mode_with_background_surface() -> None:
    gate = evaluate_host_execution_gate(
        objective='Background enrichment',
        target='https://a.example.com/',
        mode='fast',
        task_family='content_discovery',
        unresolved_hosts=set(),
        host_dns_cache={'a.example.com': True},
        host_cooldown_until={},
        autodiscover_deep_skip=False,
        host_state={'hosts': {'a.example.com': {}}},
        deep_budget={},
        host_success_count={},
        host_fail_count={},
        family_allowed_fn=lambda *_args, **_kwargs: True,
        runtime_task={'activation_mode': 'background', 'surface_role': 'background', 'expected_depth': 'light'},
    )
    assert gate.allowed is True
