from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_qualification import compute_promising, compute_signal_assessment, finding_lifecycle  # type: ignore


def test_compute_promising_uses_qualification_threshold_in_strict_mode() -> None:
    qual = {'verdict': 'probable'}
    assert compute_promising(qual, 'boring output', 'low', 'strict', 'probable') is True
    assert compute_promising(qual, 'boring output', 'low', 'strict', 'confirmed') is False


def test_compute_promising_no_longer_uses_heuristic_as_workflow_truth_in_shadow_mode() -> None:
    qual = {'verdict': 'none', 'false_positive_guards_passed': True}
    assert compute_promising(qual, 'Potential XSS finding surfaced', 'low', 'shadow', 'confirmed') is False


def test_compute_signal_assessment_uses_bounded_shadow_bridge_for_workflow_only() -> None:
    qual = {'verdict': 'none', 'false_positive_guards_passed': True}
    assessment = compute_signal_assessment(qual, 'Potential XSS finding surfaced', 'low', 'shadow', 'confirmed')
    assert assessment['heuristic_promising'] is True
    assert assessment['qualification_promising'] is False
    assert assessment['canonical_promising'] is False
    assert assessment['workflow_promotable'] is True
    assert assessment['adaptation_positive'] is True
    assert assessment['host_promise_positive'] is True
    assert assessment['shadow_bridge_active'] is True
    assert assessment['source'] == 'hybrid_shadow'


def test_compute_signal_assessment_shadow_bridge_respects_guards_and_toggle() -> None:
    qual = {'verdict': 'none', 'false_positive_guards_passed': False}
    assessment = compute_signal_assessment(qual, 'Potential XSS finding surfaced', 'low', 'shadow', 'confirmed')
    assert assessment['workflow_promotable'] is False
    assert assessment['shadow_bridge_active'] is False

    qual_ok = {'verdict': 'none', 'false_positive_guards_passed': True}
    disabled = compute_signal_assessment(
        qual_ok,
        'Potential XSS finding surfaced',
        'low',
        'shadow',
        'confirmed',
        shadow_workflow_bridge_enabled=False,
    )
    assert disabled['workflow_promotable'] is False
    assert disabled['shadow_bridge_active'] is False
    assert disabled['source'] == 'qualification'


def test_finding_lifecycle_respects_confirm_mode_and_verdicts() -> None:
    assert finding_lifecycle('confirm', {'verdict': 'probable'}) == 'confirm_running'
    assert finding_lifecycle('fast', {'verdict': 'confirmed'}) == 'confirmed'
    assert finding_lifecycle('fast', {'verdict': 'probable'}) == 'probable'
    assert finding_lifecycle('fast', {'verdict': 'none'}) == 'signal'
