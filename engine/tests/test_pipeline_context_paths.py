from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import pipeline_context as pc  # type: ignore


def test_append_context_entry_writes_canonical_and_legacy_paths(tmp_path: Path, monkeypatch) -> None:
    canonical = tmp_path / 'reports' / 'cache' / 'context_summary.json'
    legacy = tmp_path / 'engine' / 'context_summary.json'
    monkeypatch.setattr(pc, 'CONTEXT_SUMMARY_PATH', canonical)
    monkeypatch.setattr(pc, 'LEGACY_CONTEXT_SUMMARY_PATH', legacy)

    pc.append_context_entry({'objective': 'Probe', 'target': 'https://example.com'}, limit=10)

    assert canonical.exists()
    assert legacy.exists()
    assert json.loads(canonical.read_text(encoding='utf-8')) == json.loads(legacy.read_text(encoding='utf-8'))


def test_load_context_history_migrates_from_legacy_when_canonical_missing(tmp_path: Path, monkeypatch) -> None:
    canonical = tmp_path / 'reports' / 'cache' / 'context_summary.json'
    legacy = tmp_path / 'engine' / 'context_summary.json'
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(json.dumps([{'objective': 'Legacy', 'target': 'https://legacy.example'}]), encoding='utf-8')
    monkeypatch.setattr(pc, 'CONTEXT_SUMMARY_PATH', canonical)
    monkeypatch.setattr(pc, 'LEGACY_CONTEXT_SUMMARY_PATH', legacy)

    rows = pc.load_context_history(limit=5)

    assert len(rows) == 1
    assert rows[0]['objective'] == 'Legacy'
    assert canonical.exists()
    assert json.loads(canonical.read_text(encoding='utf-8')) == json.loads(legacy.read_text(encoding='utf-8'))
