from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_persist_callbacks as rrpc  # type: ignore


def test_build_runtime_persist_services_delegates_fields() -> None:
    reprioritize = lambda: None
    persist = lambda **kwargs: 0.0
    regen = lambda reason: None

    out = rrpc.build_runtime_persist_services(
        reprioritize_queues_fn=reprioritize,
        persist_recorded_run_fn=persist,
        maybe_trigger_plan_regeneration_fn=regen,
    )

    assert out.reprioritize_queues_fn is reprioritize
    assert out.persist_recorded_run_fn is persist
    assert out.maybe_trigger_plan_regeneration_fn is regen


def test_build_record_and_persist_run_inputs_shapes_expected_payload() -> None:
    state = SimpleNamespace(
        runs=[{'objective': 'Probe'}],
        history=[{'event': 'old'}],
        host_state={'api.example.com': {'ok': True}},
    )

    out = rrpc.build_record_and_persist_run_inputs(
        services=rrpc.RuntimePersistServices(
            reprioritize_queues_fn=lambda: None,
            persist_recorded_run_fn=lambda **kwargs: 0.0,
            maybe_trigger_plan_regeneration_fn=lambda reason: None,
        ),
        state=state,
        run_info={'objective': 'Probe', 'target': 'https://api.example.com/'},
        last_persist_ts=12.5,
        persist_live_summary_fn=lambda: None,
        update_learning_fn=lambda **kwargs: None,
        save_host_state_fn=lambda **kwargs: None,
        attack_family_fn=lambda classification, objective, target: 'authz',
        record_run_fn=lambda **kwargs: None,
    )

    assert out.runs == state.runs
    assert out.history == state.history
    assert out.host_state == state.host_state
    assert out.last_persist_ts == 12.5
    assert out.run_info['objective'] == 'Probe'


def test_build_main_persist_callbacks_update_timestamp_and_delegate() -> None:
    persist_calls = {}
    adapt_calls = {}
    last_persist_ts_ref = [12.5]
    state = SimpleNamespace(runs=[], history=[], host_state={})
    services = rrpc.RuntimePersistServices(
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        maybe_trigger_plan_regeneration_fn=lambda reason: None,
    )

    def fake_run_record_and_persist_stage(**kwargs):  # type: ignore[no-untyped-def]
        persist_calls.update(kwargs)
        return 55.5

    def fake_apply_runtime_adaptation(**kwargs):  # type: ignore[no-untyped-def]
        adapt_calls.update(kwargs)

    callbacks = rrpc.build_main_persist_callbacks(
        persist_services=services,
        state=state,
        last_persist_ts_ref=last_persist_ts_ref,
        persist_live_summary_fn=lambda: None,
        run_record_and_persist_stage_fn=fake_run_record_and_persist_stage,
        apply_runtime_adaptation_fn=fake_apply_runtime_adaptation,
    )

    callbacks['record_and_persist_run']({'objective': 'Probe'})
    callbacks['apply_recorded_runtime_adaptation']({'objective': 'Probe'})

    assert last_persist_ts_ref == [55.5]
    assert persist_calls['services'] == services
    assert persist_calls['state'] == state
    assert persist_calls['run_info'] == {'objective': 'Probe'}
    assert persist_calls['last_persist_ts'] == 12.5
    assert callable(persist_calls['persist_live_summary_fn'])
    assert adapt_calls == {'services': services, 'run_info': {'objective': 'Probe'}}
