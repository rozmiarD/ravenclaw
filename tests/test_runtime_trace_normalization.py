from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime_trace_normalization import resolve_trace_decision, resolve_trace_ladder  # type: ignore


def test_resolve_trace_ladder_reports_source_precedence() -> None:
    ladder, sources = resolve_trace_ladder(
        lineage_summary={'current_stage': 'validation'},
        planning_ladder={'next_stage': 'bounded_exploit_proof', 'recommended_progression': ['confirm']},
        planner_rationale={'target_surface_rationale': ['auth edge']},
        runtime_task={'recommended_progression': ['followup']},
    )

    assert ladder['current_stage'] == 'validation'
    assert ladder['next_stage'] == 'bounded_exploit_proof'
    assert ladder['recommended_progression'] == ['confirm']
    assert ladder['target_surface_rationale'] == ['auth edge']
    assert sources['current_stage'] == 'semantic_lineage_summary'
    assert sources['next_stage'] == 'planning_ladder'
    assert sources['recommended_progression'] == 'planning_ladder'
    assert sources['target_surface_rationale'] == 'planner_rationale'


def test_resolve_trace_decision_prefers_replay_then_runtime_decision_then_row() -> None:
    decision, sources = resolve_trace_decision(
        row={
            'decision_effective_status': 'applied',
            'decision_effective_summary': 'row summary',
            'decision_effective_reasons': {'why': ['row reason']},
            'decision_economics': {'priority_score': 0.7},
        },
        runtime_decision={
            'requested_reason': 'runtime pick',
            'requested_action': 'followup',
            'effective_action': 'confirm',
            'effective_blockers': {'gate': ['owner approval']},
            'economics': {'priority_score': 0.6},
        },
        replay_result={'requested_action': 'confirm', 'effective_action': 'confirm'},
        runtime_task={'capability_lane': 'web', 'action_type': 'single_probe', 'capability': 'http_probe'},
        lineage_summary={},
    )

    assert decision['requested_reason'] == 'runtime pick'
    assert decision['requested_action'] == 'confirm'
    assert decision['effective_action'] == 'confirm'
    assert decision['effective_status'] == 'applied'
    assert decision['effective_summary'] == 'row summary'
    assert decision['reasons'] == ['why: row reason']
    assert decision['blockers'] == ['gate: owner approval']
    assert decision['priority_score'] == 0.7
    assert decision['capability_lane'] == 'web'
    assert decision['action_type'] == 'single_probe'
    assert decision['capability'] == 'http_probe'
    assert sources['requested_reason'] == 'runtime_decision'
    assert sources['requested_action'] == 'replay'
    assert sources['effective_action'] == 'replay'
    assert sources['effective_status'] == 'row'
    assert sources['reasons'] == 'row'
    assert sources['blockers'] == 'runtime_decision'
    assert sources['priority_score'] == 'row'
    assert sources['action_type'] == 'runtime_task'
