from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_precheck_hooks_wrapper as rrphw  # type: ignore


def test_build_main_precheck_hooks_delegates() -> None:
    captured = {}

    def fake_build_main_precheck_hooks(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return {'inc_precheck_skip': lambda: None}

    out = rrphw.build_main_precheck_hooks(
        build_main_precheck_hooks_fn=fake_build_main_precheck_hooks,
        precheck_skip_count_ref=[0],
        flush_precheck_summary_fn=lambda: None,
        flush_dns_skip_summary_fn=lambda: None,
        flush_host_cooldown_summary_fn=lambda: None,
        flush_execution_gate_summary_fn=lambda: None,
    )
    assert 'inc_precheck_skip' in out
    assert captured['precheck_skip_count_ref'] == [0]
