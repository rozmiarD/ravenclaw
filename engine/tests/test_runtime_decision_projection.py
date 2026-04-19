from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_decision_projection import project_runtime_decision_to_run_info  # type: ignore


def test_projection_preserves_intent_and_threads_effective_fields() -> None:
    run_info = {
        'runtime_decision': {
            'intent_flags': {'retry': False, 'confirm': True, 'followup': False, 'precision': False},
            'action_flags': {'retry': False, 'confirm': True, 'followup': False, 'precision': False},
            'requested_action': 'confirm',
            'requested_reason': 'strong_candidate_signal',
            'selected_secondary_action': 'followup',
        },
        'decision_explain': {},
    }
    effective = {
        'effective_status': 'blocked',
        'effective_action': 'confirm',
        'effective_secondary_action': 'followup',
        'effective_flags': {'retry': False, 'confirm': False, 'followup': False, 'precision': False},
        'effective_reasons': {},
        'effective_blockers': {'confirm': ['confirm_duplicate_suppressed']},
        'effective_summary': 'selected=none;attempted=confirm;blockers=confirm:confirm_duplicate_suppressed',
    }

    out = project_runtime_decision_to_run_info(run_info=run_info, effective_decision=effective)

    assert out['runtime_decision']['intent_flags']['confirm'] is True
    assert out['runtime_decision']['action_flags']['confirm'] is True
    assert out['runtime_decision']['intent_flags_source'] == 'selected_actions'
    assert out['runtime_decision']['action_flags_source'] == 'selected_actions'
    assert out['runtime_decision']['effective_status'] == 'blocked'
    assert out['decision_requested_action'] == 'confirm'
    assert out['decision_requested_reason'] == 'strong_candidate_signal'
    assert out['decision_intent_flags']['confirm'] is True
    assert out['decision_flags']['confirm'] is False
    assert out['decision_effective_status'] == 'blocked'
    assert out['decision_effective_action'] == 'confirm'
    assert out['decision_effective_secondary_action'] == 'followup'
    assert out['decision_effective_blockers']['confirm'] == ['confirm_duplicate_suppressed']
    assert out['decision_explain']['requested_reason'] == 'strong_candidate_signal'
    assert out['decision_explain']['effective_action'] == 'confirm'
    assert out['decision_explain']['effective_summary'] == effective['effective_summary']
