from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_adaptation_engine import build_adaptation_signal  # type: ignore


def test_build_adaptation_signal_prefers_host_update_reason() -> None:
    signal = build_adaptation_signal(host_update={'regeneration_reason': 'promising_host_shift'}, runs_count=7)
    assert signal['should_regenerate'] is True
    assert signal['reason'] == 'promising_host_shift'
    assert signal['source'] == 'host_update'


def test_build_adaptation_signal_triggers_periodic_regen_every_12_runs() -> None:
    signal = build_adaptation_signal(host_update={}, runs_count=12)
    assert signal['should_regenerate'] is True
    assert signal['reason'] == 'periodic_runtime_regen'
    assert signal['source'] == 'periodic'


def test_build_adaptation_signal_detects_stalled_capability_lane() -> None:
    signal = build_adaptation_signal(
        host_update={},
        runs_count=7,
        run_info={'brain': {'capability': 'http_probe'}},
        recent_runs=[
            {'brain': {'capability': 'http_probe'}, 'workflow_promotable': False, 'success_criteria_eval': 'not_met'},
            {'brain': {'capability': 'http_probe'}, 'workflow_promotable': False, 'success_criteria_eval': 'not_met'},
            {'brain': {'capability': 'http_probe'}, 'workflow_promotable': False, 'success_criteria_eval': 'partial'},
        ],
    )
    assert signal['should_regenerate'] is True
    assert signal['source'] == 'capability_lane'
    assert signal['reason'] == 'capability_lane_stalled:http_probe'
    assert signal['capability_summary']['capability'] == 'http_probe'
