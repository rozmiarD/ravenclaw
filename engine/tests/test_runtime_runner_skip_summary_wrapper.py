from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_skip_summary_wrapper as rrssw  # type: ignore


def test_build_main_skip_summary_flushers_delegates() -> None:
    captured = {}

    def fake_build_main_skip_summary_flushers(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'flush_precheck_summary': lambda force=False: None}

    out = rrssw.build_main_skip_summary_flushers(
        build_main_skip_summary_flushers_fn=fake_build_main_skip_summary_flushers,
        make_skip_summary_flusher_fn=lambda **kwargs: (lambda force=False: None),
        precheck_skip_count_ref=[0],
        precheck_skip_examples=[],
        dns_skip_count={},
        host_cooldown_skip_count={},
        execution_gate_skip_count={},
        execution_gate_skip_examples={},
    )
    assert 'flush_precheck_summary' in out
    assert callable(captured['make_skip_summary_flusher_fn'])
