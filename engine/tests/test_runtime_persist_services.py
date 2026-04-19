from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_persist_services import RuntimePersistServices, record_and_persist_runtime_run, apply_runtime_adaptation  # type: ignore


def test_record_and_persist_runtime_run_delegates_with_services() -> None:
    seen = {}
    services = RuntimePersistServices(
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: seen.update(kwargs) or 12.5,
        maybe_trigger_plan_regeneration_fn=lambda reason: None,
    )
    out = record_and_persist_runtime_run(
        services=services,
        runs=[],
        history=[],
        run_info={'target': 'https://a.example.com/'},
        host_state={},
        last_persist_ts=1.0,
        record_run_fn=lambda *args, **kwargs: None,
        persist_live_summary_fn=lambda: None,
        update_learning_fn=lambda *args, **kwargs: None,
        save_host_state_fn=lambda *args, **kwargs: None,
        attack_family_fn=lambda *args, **kwargs: 'recon',
    )
    assert out == 12.5
    assert seen['last_persist_ts'] == 1.0
    assert seen['run_info']['target'] == 'https://a.example.com/'


def test_apply_runtime_adaptation_triggers_regeneration_only_when_requested() -> None:
    seen = []
    services = RuntimePersistServices(
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        maybe_trigger_plan_regeneration_fn=lambda reason: seen.append(reason),
    )
    reason = apply_runtime_adaptation(
        services=services,
        run_info={'adaptation_signal': {'should_regenerate': True, 'reason': 'host_stage_shift'}},
    )
    assert reason == 'host_stage_shift'
    assert seen == ['host_stage_shift']
