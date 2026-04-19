from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_session_state import RuntimeSessionState  # type: ignore


def test_runtime_session_state_defaults_include_quality_and_counters() -> None:
    state = RuntimeSessionState(
        runs=[],
        history=[],
        host_state={},
        curated_plan=[],
        runtime_plan_meta={},
        host_dns_cache={},
        toggles={},
        planner_hints_cache={},
    )
    assert state.quality_telemetry['confirm_queued'] == 0
    assert state.confirm_total == 0
    assert state.scheduled_keys == set()
