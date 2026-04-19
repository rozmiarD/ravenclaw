from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import run_pipeline as rp  # type: ignore


def test_load_exploit_motif_hints_filters_by_task_family(tmp_path: Path, monkeypatch) -> None:
    state_path = tmp_path / 'exploit-motif-memory.json'
    state_path.write_text(json.dumps({
        'schema_version': 'exploit-motif-memory-v1',
        'count': 2,
        'items': [
            {'task_family': 'authz', 'current_stage': 'bounded_exploit_proof', 'capability': 'http_probe', 'workflow_status': 'promotable', 'occurrences': 2, 'max_persistence_score': 0.9, 'example_hypotheses': ['boundary motif']},
            {'task_family': 'logic', 'current_stage': 'state_transition_confirmation', 'capability': 'state_transition', 'workflow_status': 'candidate', 'occurrences': 1, 'max_persistence_score': 0.7, 'example_hypotheses': ['logic motif']},
        ],
    }), encoding='utf-8')
    monkeypatch.setattr(rp, 'rsp', lambda *parts: state_path)

    hints = rp._load_exploit_motif_hints('authz', limit=3)

    assert len(hints) == 1
    assert hints[0]['task_family'] == 'authz'
    assert hints[0]['example_hypotheses'] == ['boundary motif']
