from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from json_state_io import atomic_write_json, safe_load_json_object  # type: ignore
from runtime_state_schemas import normalize_runtime_campaign_state  # type: ignore


def test_atomic_write_and_safe_load_json_object_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / 'state.json'
    atomic_write_json(path, {'paused': 1, 'owner_override': 0})
    data, meta = safe_load_json_object(path, {'paused': False, 'owner_override': False}, normalizer=normalize_runtime_campaign_state)
    assert meta['status'] == 'ok'
    assert data['paused'] is True
    assert data['owner_override'] is False


def test_safe_load_json_object_returns_default_on_invalid_shape(tmp_path: Path) -> None:
    path = tmp_path / 'state.json'
    path.write_text('[]', encoding='utf-8')
    data, meta = safe_load_json_object(path, {'paused': False}, normalizer=normalize_runtime_campaign_state)
    assert meta['status'] == 'invalid_shape'
    assert data == {'paused': False}
