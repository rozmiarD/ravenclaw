from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_skip_flusher_wrapper as rrsfw  # type: ignore


def test_make_skip_summary_flusher_delegates() -> None:
    captured = {}

    def fake_make_skip_summary_flusher(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return lambda force=False: None

    out = rrsfw.make_skip_summary_flusher(
        make_skip_summary_flusher_fn=fake_make_skip_summary_flusher,
        flush_skip_summaries_fn=lambda **kwargs: None,
        log_event_fn=lambda *args, **kwargs: None,
        precheck_skip_count_ref=[0],
        precheck_skip_examples_ref=[],
        dns_skip_count_ref={},
        host_cooldown_skip_count_ref={},
        execution_gate_skip_count_ref={},
        execution_gate_skip_examples_ref={},
    )
    assert callable(out)
    assert callable(captured['flush_skip_summaries_fn'])
