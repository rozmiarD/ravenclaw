from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import evaluation_metrics  # type: ignore
import learning_store  # type: ignore


def test_aggregate_replay_metrics_includes_branch_thread_summary(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(learning_store, 'LEARNING_PATH', tmp_path / 'learning_store.json')
    learning_store.update_learning(
        'api.example.com',
        'authz',
        'medium',
        True,
        'ok',
        next_stage='bounded_exploit_proof',
        branch_state='branch_candidate',
        branch_action='deepen',
        branch_reason='proof_path_ready',
        branch_outcome='productive',
        branch_lifecycle_status='productive',
        branch_lifecycle_reason='promotion_or_partial_success',
        branch_thread_key='authz::bounded_exploit_proof::deepen::proof_path_ready',
        branch_thread_label='authz:bounded_exploit_proof:deepen',
    )
    metrics = evaluation_metrics.aggregate_replay_metrics([])
    assert metrics['branch_thread_summary']
    assert metrics['branch_thread_summary'][0]['branch_thread_key'] == 'authz::bounded_exploit_proof::deepen::proof_path_ready'


def test_aggregate_replay_metrics_reports_synthesis_quality_rates() -> None:
    metrics = evaluation_metrics.aggregate_replay_metrics([
        {
            'synthesis_alignment': True,
            'synthesis_positive': True,
            'synthesis_recommended_action': 'pivot',
            'synthesis_pivot_avoidance': True,
        },
        {
            'synthesis_alignment': False,
            'synthesis_positive': False,
            'synthesis_recommended_action': 'deepen',
            'synthesis_pivot_avoidance': False,
        },
    ])
    assert metrics['synthesis_quality_metrics']['synthesis_alignment_rate']['count'] == 1
    assert metrics['synthesis_quality_metrics']['synthesis_positive_rate']['count'] == 1
    assert metrics['synthesis_quality_metrics']['synthesis_pivot_avoidance_rate']['count'] == 1
