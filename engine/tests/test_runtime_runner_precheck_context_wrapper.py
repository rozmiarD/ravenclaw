from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_precheck_context_wrapper as rrpcw  # type: ignore


def test_build_runtime_precheck_context_inputs_delegates() -> None:
    captured = {}

    def fake_build_runtime_precheck_context_inputs(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    out = rrpcw.build_runtime_precheck_context_inputs(
        build_runtime_precheck_context_inputs_fn=fake_build_runtime_precheck_context_inputs,
        runtime_precheck_context_cls=object,
        unresolved_hosts=set(),
        dns_skip_count={},
        host_dns_cache={},
        host_cooldown_until={},
        host_cooldown_skip_count={},
        autodiscover_deep_skip=False,
        executed_keys=set(),
        precheck_skip_examples=[],
        host_precheck_burst={},
        host_state={},
        deep_budget={},
        host_fail_streak={},
        host_success_count={},
        host_fail_count={},
        gate_skip_count={},
        gate_skip_examples={},
        increment_precheck_skip_fn=lambda: None,
        on_executed_key_fn=lambda: None,
        dedup_key_fn=lambda *args, **kwargs: 'k',
        family_allowed_for_host_stage_fn=lambda *args, **kwargs: True,
        log_skip_fn=lambda *args, **kwargs: None,
        host_health_cooldown_sec=900,
        deep_budget_cap_per_host_family=2,
        precheck_burst_cooldown_threshold=10,
        precheck_burst_cooldown_sec=300,
        host_fail_streak_backoff_step_sec=0.4,
        host_fail_streak_backoff_cap_sec=2.0,
    )
    assert out is not None
    assert callable(captured['dedup_key_fn'])
