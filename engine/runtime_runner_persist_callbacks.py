from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class RuntimePersistServices:
    reprioritize_queues_fn: Callable[[], None]
    persist_recorded_run_fn: Callable[..., float]
    maybe_trigger_plan_regeneration_fn: Callable[[str], None]


@dataclass
class RecordAndPersistRunInputs:
    services: RuntimePersistServices
    runs: list[dict]
    history: list[dict]
    run_info: dict
    host_state: dict
    last_persist_ts: float
    record_run_fn: Callable[..., None]
    persist_live_summary_fn: Callable[[], None]
    update_learning_fn: Callable[..., None]
    save_host_state_fn: Callable[..., None]
    attack_family_fn: Callable[[str, str, str], str]


def build_runtime_persist_services(*, reprioritize_queues_fn: Callable[[], None], persist_recorded_run_fn: Callable[..., float], maybe_trigger_plan_regeneration_fn: Callable[[str], None]) -> RuntimePersistServices:
    return RuntimePersistServices(
        reprioritize_queues_fn=reprioritize_queues_fn,
        persist_recorded_run_fn=persist_recorded_run_fn,
        maybe_trigger_plan_regeneration_fn=maybe_trigger_plan_regeneration_fn,
    )


def build_record_and_persist_run_inputs(*, services: RuntimePersistServices, state: Any, run_info: dict, last_persist_ts: float, persist_live_summary_fn: Callable[[], None], update_learning_fn: Callable[..., None], save_host_state_fn: Callable[..., None], attack_family_fn: Callable[[str, str, str], str], record_run_fn: Callable[..., None]) -> RecordAndPersistRunInputs:
    return RecordAndPersistRunInputs(
        services=services,
        runs=state.runs,
        history=state.history,
        run_info=run_info,
        host_state=state.host_state,
        last_persist_ts=float(last_persist_ts),
        record_run_fn=record_run_fn,
        persist_live_summary_fn=persist_live_summary_fn,
        update_learning_fn=update_learning_fn,
        save_host_state_fn=save_host_state_fn,
        attack_family_fn=attack_family_fn,
    )


def build_main_persist_callbacks(*, persist_services: RuntimePersistServices, state: Any, last_persist_ts_ref: list[float], persist_live_summary_fn: Callable[[], None], run_record_and_persist_stage_fn: Callable[..., float], apply_runtime_adaptation_fn: Callable[..., None]) -> dict:
    def record_and_persist_run(run_info: dict) -> None:
        last_persist_ts_ref[0] = run_record_and_persist_stage_fn(
            services=persist_services,
            state=state,
            run_info=run_info,
            last_persist_ts=last_persist_ts_ref[0],
            persist_live_summary_fn=persist_live_summary_fn,
        )

    def apply_recorded_runtime_adaptation(run_info: dict) -> None:
        apply_runtime_adaptation_fn(services=persist_services, run_info=run_info)

    return {
        'record_and_persist_run': record_and_persist_run,
        'apply_recorded_runtime_adaptation': apply_recorded_runtime_adaptation,
    }
