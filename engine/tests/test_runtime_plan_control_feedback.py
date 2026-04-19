from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_plan_control import adaptive_quality_context, recon_to_exploit_synthesis, summarize_planner_feedback, refresh_planner_hints_and_reprioritize, maybe_trigger_plan_regeneration  # type: ignore


def test_summarize_planner_feedback_counts_alignment_override_and_signals() -> None:
    feedback = summarize_planner_feedback(
        runs=[
            {
                'brain': {'planner_alignment': 'aligned', 'redundancy_risk': 'low'},
                'signal_contract': {
                    'success_outcome': {'status': 'partial'},
                    'adaptation_feedback': {'status': 'positive', 'planner_reconsult_worthy': True},
                    'finding_signal': {'status': 'strong'},
                },
                'analysis': {'next_family_hint': 'logic', 'next_stage_hint': 'bounded_exploit_proof'},
                'runtime_task': {
                    'planner_rationale': {'target_surface_rationale': ['authenticated_or_boundary_mapping']},
                    'planning_ladder': {'current_stage': 'discovery', 'next_stage': 'bounded_exploit_proof'},
                    'branch_state': 'branch_candidate',
                    'branch_action': 'confirm',
                    'branch_evidence_score': 0.42,
                    'task_family': 'recon',
                },
                'runtime_decision': {'effective_action': 'confirm'},
            },
            {
                'brain': {'planner_alignment': 'override', 'planner_override_reason': 'recent authz dead-end', 'redundancy_risk': 'high'},
                'signal_contract': {'success_outcome': {'status': 'not_met'}, 'adaptation_feedback': {'status': 'negative'}},
                'analysis': {},
                'runtime_task': {'branch_state': 'branch_candidate', 'branch_action': 'pivot', 'branch_evidence_score': 0.2},
            },
        ],
        host_state={'hosts': {'api.example.com': {'state': 'degraded'}, 'auth.example.com': {'state_band': 'exploitation', 'state': 'promising'}}},
    )
    assert feedback['planner_aligned_recent'] == 1
    assert feedback['planner_override_recent'] == 1
    assert feedback['high_redundancy_recent'] == 1
    assert feedback['partial_recent'] == 1
    assert feedback['not_met_recent'] == 1
    assert feedback['adaptation_positive_recent'] == 1
    assert feedback['reconsult_worthy_recent'] == 1
    assert feedback['degraded_hosts'] == 1
    assert feedback['exploitation_hosts'] == 1
    assert feedback['recent_next_family_hints'] == ['logic']
    assert feedback['recent_next_stage_hints'] == ['bounded_exploit_proof']
    assert feedback['recent_target_surface_rationale'] == ['authenticated_or_boundary_mapping']
    assert feedback['branch_candidate_recent'] == 2
    assert feedback['branch_quality_positive_recent'] == 1
    assert feedback['dead_end_branch_recent'] == 1
    assert feedback['recon_to_exploit_candidate_recent'] == 1
    assert feedback['recon_to_exploit_success_recent'] == 1
    assert feedback['signal_bearing_recent'] == 1
    assert feedback['confirmation_reached_recent'] == 1
    assert feedback['branch_quality_rate_recent'] == 0.5
    assert feedback['dead_end_pressure_recent'] == 0.5
    assert feedback['recon_conversion_rate_recent'] == 1.0
    assert feedback['signal_to_confirmation_efficiency_recent'] == 1.0


def test_adaptive_quality_context_normalizes_feedback_and_derives_flags() -> None:
    quality = adaptive_quality_context(
        {
            'branch_candidate_recent': 4,
            'branch_quality_positive_recent': 3,
            'dead_end_branch_recent': 1,
            'recon_to_exploit_candidate_recent': 2,
            'recon_to_exploit_success_recent': 1,
            'signal_bearing_recent': 3,
            'confirmation_reached_recent': 2,
            'branch_quality_rate_recent': 0.751,
            'dead_end_pressure_recent': 0.551,
            'recon_conversion_rate_recent': 0.5,
            'signal_to_confirmation_efficiency_recent': 0.667,
        }
    )
    assert quality['branch_quality_rate_recent'] == 0.751
    assert quality['dead_end_pressure_recent'] == 0.551
    assert quality['recon_conversion_rate_recent'] == 0.5
    assert quality['signal_to_confirmation_efficiency_recent'] == 0.667
    assert quality['dead_end_heavy'] is True
    assert quality['quality_structural'] is True
    assert quality['quality_strong'] is True
    assert quality['quality_positive_balance'] is True


def test_recon_to_exploit_synthesis_emits_bounded_branch_actions() -> None:
    deepen = recon_to_exploit_synthesis(
        planner_feedback={'branch_quality_rate_recent': 0.8, 'recon_conversion_rate_recent': 0.6},
        next_stage='bounded_exploit_proof',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping'],
        current_family='recon',
    )
    pivot = recon_to_exploit_synthesis(
        planner_feedback={'dead_end_pressure_recent': 0.8, 'branch_quality_rate_recent': 0.2},
        next_stage='bounded_exploit_proof',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping'],
        current_family='recon',
    )
    confirm = recon_to_exploit_synthesis(
        planner_feedback={},
        next_stage='control_boundary_confirmation',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping'],
        current_family='recon',
    )
    assert deepen['recommended_branch_action'] == 'deepen'
    assert pivot['recommended_branch_action'] == 'pivot'
    assert confirm['recommended_branch_action'] == 'confirm'


def test_refresh_and_regeneration_include_feedback_without_breaking() -> None:
    events = []
    hints = refresh_planner_hints_and_reprioritize(
        reason='high_signal_threshold',
        tier='light',
        load_planner_hints_fn=lambda: {'suggested_attack_vectors': ['idor']},
        reprioritize_queues_fn=lambda: None,
        log_event_fn=lambda *args, **kwargs: events.append(args),
        followup_queue_len=1,
        precision_queue_len=0,
        planner_feedback={'planner_aligned_recent': 2, 'planner_override_recent': 1, 'partial_recent': 1, 'not_met_recent': 0, 'exploitation_hosts': 1},
    )
    assert hints['suggested_attack_vectors'] == ['idor']
    out = maybe_trigger_plan_regeneration(
        reason='periodic_runtime_regen',
        force=True,
        toggles={'dynamic_plan_adaptation': True},
        runs_count=10,
        last_regen_run_index=0,
        regenerate_runtime_plan_fn=lambda reason: {'ok': True, 'skipped': False, 'plan_revision': 2, 'added_tasks': 1, 'deprecated_tasks': 0},
        log_event_fn=lambda *args, **kwargs: events.append(args),
        planner_feedback={'planner_override_recent': 2, 'partial_recent': 3, 'exploitation_hosts': 1},
    )
    assert out == 10
    assert events


def test_regeneration_gap_shortens_for_exploitation_feedback() -> None:
    events = []
    out = maybe_trigger_plan_regeneration(
        reason='promising_exploitation_host_shift',
        force=False,
        toggles={'dynamic_plan_adaptation': True, 'aggressive_adaptation': False},
        runs_count=9,
        last_regen_run_index=6,
        regenerate_runtime_plan_fn=lambda reason: {'ok': True, 'skipped': False, 'plan_revision': 3, 'added_tasks': 2, 'deprecated_tasks': 0},
        log_event_fn=lambda *args, **kwargs: events.append(args),
        planner_feedback={'exploitation_hosts': 1, 'branch_quality_rate_recent': 0.8},
    )
    assert out == 9
    assert any(args[1] == 'plan_regenerated' for args in events)


def test_regeneration_gap_slows_under_dead_end_pressure() -> None:
    events = []
    out = maybe_trigger_plan_regeneration(
        reason='periodic_runtime_regen',
        force=False,
        toggles={'dynamic_plan_adaptation': True, 'aggressive_adaptation': True},
        runs_count=8,
        last_regen_run_index=4,
        regenerate_runtime_plan_fn=lambda reason: {'ok': True, 'skipped': False, 'plan_revision': 3, 'added_tasks': 1, 'deprecated_tasks': 0},
        log_event_fn=lambda *args, **kwargs: events.append(args),
        planner_feedback={'dead_end_pressure_recent': 0.75},
    )
    assert out == 4
    assert events == []


def test_regeneration_occurs_under_aggressive_adaptation_defaults() -> None:
    called = []
    out = maybe_trigger_plan_regeneration(
        reason='high_signal_authz',
        force=False,
        toggles={'dynamic_plan_adaptation': True, 'aggressive_adaptation': True, 'freeze_plan_revision': False, 'plan_adaptation_mode': 'aggressive'},
        runs_count=8,
        last_regen_run_index=6,
        regenerate_runtime_plan_fn=lambda reason: called.append(reason) or {'ok': True, 'skipped': False, 'plan_revision': 5, 'added_tasks': 2, 'deprecated_tasks': 1},
        log_event_fn=lambda *args, **kwargs: None,
        planner_feedback={'recent_next_stage_hints': ['bounded_exploit_proof'], 'exploitation_hosts': 1},
    )
    assert out == 8
    assert called == ['high_signal_authz']


def test_regeneration_remains_blocked_when_frozen() -> None:
    called = []
    out = maybe_trigger_plan_regeneration(
        reason='high_signal_authz',
        force=False,
        toggles={'dynamic_plan_adaptation': True, 'aggressive_adaptation': True, 'freeze_plan_revision': True, 'plan_adaptation_mode': 'frozen'},
        runs_count=8,
        last_regen_run_index=6,
        regenerate_runtime_plan_fn=lambda reason: called.append(reason) or {'ok': True},
        log_event_fn=lambda *args, **kwargs: None,
        planner_feedback={'recent_next_stage_hints': ['bounded_exploit_proof'], 'exploitation_hosts': 1},
    )
    assert out == 6
    assert called == []
