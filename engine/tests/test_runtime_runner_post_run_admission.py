from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_post_run_admission as rrpra  # type: ignore


def test_quality_aware_followup_admission_hint_suppresses_followup_for_dead_end_pressure() -> None:
    out = rrpra.quality_aware_followup_admission_hint(
        {'task_family': 'authz'},
        {'planner_feedback': {'dead_end_pressure_recent': 0.8}},
        {'intent_flags': {'followup': True, 'confirm': False}},
        adaptive_quality_context_fn=lambda feedback: dict(feedback),
    )
    assert out == {'suppress_followup': True, 'force_high_priority': False, 'reason': 'dead_end_pressure'}


def test_apply_post_run_admission_hint_mutates_runtime_decision_flags() -> None:
    out = rrpra.apply_post_run_admission_hint(
        {'intent_flags': {'followup': True, 'confirm': False}},
        {'suppress_followup': True, 'force_high_priority': True, 'reason': 'quality_strength'},
    )
    assert out['intent_flags']['followup'] is False
    assert out['high_priority'] is True
