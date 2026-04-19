from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_downstream import post_run_decision  # type: ignore


BASE_TASK = {'task_family': 'authz', 'runtime_task': {}}
BASE_RESULT = {}
BASE_QUAL = {'verdict': 'probable', 'confidence': 0.75}
BASE_TOGGLES = {
    'enable_confirm_jobs': True,
    'enable_followups': True,
    'qualification_followup_threshold': 'probable',
}


def test_post_run_decision_prefers_canonical_selected_action_truth() -> None:
    out = post_run_decision(
        BASE_TASK,
        {
            'signal_contract': {
                'workflow_promotion': {'status': 'confirmable'},
                'success_outcome': {'status': 'partial'},
                'finding_signal': {'status': 'moderate', 'evidence_bearing': True},
            }
        },
        {**BASE_QUAL, 'false_positive_guards_passed': True},
        'medium',
        'approve',
        'ok',
        'partial',
        BASE_TOGGLES,
        mode='fast',
    )
    assert out == {'retry': False, 'confirm': True, 'followup': True, 'precision': False}


def test_post_run_decision_keeps_legacy_flag_compatibility_when_needed() -> None:
    flags = {'retry': False, 'confirm': False, 'followup': True, 'precision': False}
    assert out_from_legacy(flags) == flags


def out_from_legacy(flags: dict[str, bool]) -> dict[str, bool]:
    from runtime_decision_contracts import canonical_action_flags_from_mapping  # type: ignore

    out, source = canonical_action_flags_from_mapping({'intent_flags': flags})
    assert source == 'legacy_flags'
    return out
