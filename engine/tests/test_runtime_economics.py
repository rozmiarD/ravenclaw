from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_decision_engine import build_runtime_decision  # type: ignore
from runtime_economics import compute_runtime_economics  # type: ignore


def test_runtime_economics_rewards_probable_partial_more_than_none_failed() -> None:
    good = compute_runtime_economics(
        verdict='probable',
        confidence=0.7,
        engine_status='ok',
        success_eval_status='partial',
        mode='fast',
        blocked=False,
    )
    bad = compute_runtime_economics(
        verdict='none',
        confidence=0.0,
        engine_status='failed',
        success_eval_status='failed',
        mode='deep',
        blocked=False,
    )
    assert good['priority_score'] > bad['priority_score']
    assert good['value_estimate'] > bad['value_estimate']


def test_runtime_decision_includes_economics_and_compact_summary() -> None:
    rec = build_runtime_decision(
        qual={'verdict': 'probable', 'confidence': 0.8},
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        toggles={
            'enable_confirm_jobs': True,
            'enable_followups': True,
            'qualification_followup_threshold': 'probable',
        },
        mode='fast',
    )
    assert 'priority_score' in rec.economics
    assert 'summary' in rec.explain
    assert rec.explain['decision']['confirm'] is True
