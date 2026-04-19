from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_precheck_context import RuntimePrecheckContext  # type: ignore


def test_runtime_precheck_context_delegates_to_precheck_module(monkeypatch) -> None:
    import runtime_precheck_context as mod  # type: ignore

    called = {}

    def fake_precheck_and_prepare_task(**kwargs):
        called.update(kwargs)
        return {'allowed': True}

    monkeypatch.setattr('auto_campaign_precheck.precheck_and_prepare_task', fake_precheck_and_prepare_task)
    ctx = RuntimePrecheckContext(
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
        dedup_key_fn=lambda *args: ('k',),
        family_allowed_for_host_stage_fn=lambda *args: True,
        log_skip_fn=lambda *args, **kwargs: None,
        increment_precheck_skip_fn=lambda: None,
        on_executed_key_fn=lambda: None,
        gate_skip_count={},
        gate_skip_examples={},
    )
    out = ctx.prepare_task_precheck(objective='Recon', target='https://a.example.com/', mode='fast', task_family='recon', dedup_mode_suffix=False)
    assert out['allowed'] is True
    assert called['task_family'] == 'recon'
    assert called['host_fail_streak_backoff_step_sec'] == 0.4
    assert called['host_fail_streak_backoff_cap_sec'] == 2.0
