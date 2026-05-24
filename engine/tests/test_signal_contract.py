from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from security_signal_contract import build_signal_contract, signal_contract_signal_positive  # type: ignore


def test_weak_actionable_signal_bridge_marks_signal_positive_but_not_high_signal() -> None:
    contract = build_signal_contract(
        engine_status='success',
        auditor_decision='approve',
        success_eval_status='partial',
        qual={'verdict': 'none', 'confidence': 0.0, 'false_positive_guards_passed': True},
        signal_assessment={
            'canonical_promising': False,
            'qualification_promising': False,
            'heuristic_promising': False,
            'signal_positive': True,
            'workflow_promotable': False,
            'adaptation_positive': False,
            'host_promise_positive': False,
            'qualification_mode': 'shadow',
            'qualification_threshold': 'probable',
            'source': 'qualification',
        },
        runtime_decision={'requested_action': '', 'selected_primary_action': ''},
        summary_text='Redirect baseline',
        reason_code='engine_success',
        control_cmp={'performed': False, 'control_delta_observed': False, 'reason': 'tool_not_supported'},
        metrics_obj={'code': 307},
        success_semantics={},
        weak_signal_positive_bridge_enabled=True,
    )
    assert contract['finding_signal']['status'] == 'weak'
    assert contract['legacy_bridges']['weak_actionable_signal'] is True
    assert contract['legacy_bridges']['signal_positive'] is True
    assert contract['legacy_bridges']['high_signal'] is False
    assert signal_contract_signal_positive(contract) is True
    assert contract['adaptation_feedback']['status'] == 'positive'
    assert contract['adaptation_feedback']['planner_reconsult_worthy'] is True
    assert 'weak_actionable_signal_bridge' in contract['adaptation_feedback']['reasons']


def test_weak_actionable_signal_bridge_can_be_disabled() -> None:
    contract = build_signal_contract(
        engine_status='success',
        auditor_decision='approve',
        success_eval_status='partial',
        qual={'verdict': 'none', 'confidence': 0.0, 'false_positive_guards_passed': True},
        signal_assessment={
            'canonical_promising': False,
            'qualification_promising': False,
            'heuristic_promising': False,
            'signal_positive': True,
            'workflow_promotable': False,
            'adaptation_positive': False,
            'host_promise_positive': False,
            'qualification_mode': 'shadow',
            'qualification_threshold': 'probable',
            'source': 'qualification',
        },
        runtime_decision={'requested_action': '', 'selected_primary_action': ''},
        summary_text='Redirect baseline',
        reason_code='engine_success',
        control_cmp={'performed': False, 'control_delta_observed': False, 'reason': 'tool_not_supported'},
        metrics_obj={'code': 307},
        success_semantics={},
        weak_signal_positive_bridge_enabled=False,
    )
    assert contract['legacy_bridges']['weak_actionable_signal'] is False
    assert contract['legacy_bridges']['signal_positive'] is False
    assert contract['adaptation_feedback']['planner_reconsult_worthy'] is False
