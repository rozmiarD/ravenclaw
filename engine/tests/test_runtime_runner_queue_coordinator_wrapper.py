from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_queue_coordinator_wrapper as rrqcw  # type: ignore


def test_build_queue_coordinator_delegates() -> None:
    captured = {}

    def fake_build_queue_coordinator(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    out = rrqcw.build_queue_coordinator(
        build_queue_coordinator_fn=fake_build_queue_coordinator,
        queue_coordinator_cls=object,
        followup_queue=[],
        precision_queue=[],
        host_rr={},
        host_success_count={},
        host_fail_count={},
    )
    assert out is not None
    assert captured['followup_queue'] == []
