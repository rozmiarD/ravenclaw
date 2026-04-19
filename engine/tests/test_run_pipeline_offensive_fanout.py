from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import run_pipeline as rp  # type: ignore


def test_generate_vector_family_motifs_for_authz() -> None:
    motifs = rp.generate_vector_family_motifs(task_family='authz', capability='http_probe', action_type='single_probe')
    assert len(motifs) == 2
    assert any(item['action_type'] == 'state_transition_probe' for item in motifs)
    assert any('boundary' in item['hypothesis'] or 'state-transition' in item['hypothesis'] or 'state' in item['hypothesis'] for item in motifs)


def test_generate_vector_family_motifs_for_redirect_trust() -> None:
    motifs = rp.generate_vector_family_motifs(task_family='redirect_trust', capability='http_probe', action_type='variant_probe')
    assert len(motifs) == 2
    assert all(item['action_type'] == 'variant_probe' for item in motifs)


def test_merge_hypothesis_fanout_keeps_explicit_precedence_and_clips() -> None:
    merged = rp._merge_hypothesis_fanout(
        'primary',
        [
            {'hypothesis': 'explicit-a', 'action_type': 'variant_probe', 'capability': 'http_probe'},
            {'hypothesis': 'explicit-b', 'action_type': 'variant_probe', 'capability': 'http_probe'},
        ],
        [
            {'hypothesis': 'motif-a', 'action_type': 'variant_probe', 'capability': 'http_probe'},
        ],
        limit=2,
    )
    assert len(merged) == 2
    assert merged[0]['hypothesis'] == 'explicit-a'
    assert merged[1]['hypothesis'] == 'explicit-b'
