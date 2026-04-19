from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from status_utils import normalize_engine_status, normalize_pipeline_status  # type: ignore


def test_normalize_engine_status_maps_succeeded_to_success() -> None:
    assert normalize_engine_status('succeeded') == 'success'


def test_normalize_pipeline_status_treats_succeeded_as_success() -> None:
    assert normalize_pipeline_status('succeeded', 'approve', False) == 'success'
