from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class RuntimePersistServices:
    reprioritize_queues_fn: Callable[[], None]
    persist_recorded_run_fn: Callable[..., float]
    maybe_trigger_plan_regeneration_fn: Callable[[str], None]


def record_and_persist_runtime_run(
    *,
    services: RuntimePersistServices,
    runs: list[dict],
    history: list[dict],
    run_info: dict,
    host_state: dict,
    last_persist_ts: float,
    record_run_fn,
    persist_live_summary_fn,
    update_learning_fn,
    save_host_state_fn,
    attack_family_fn,
) -> float:
    return services.persist_recorded_run_fn(
        runs=runs,
        history=history,
        run_info=run_info,
        host_state=host_state,
        last_persist_ts=last_persist_ts,
        record_run_fn=record_run_fn,
        persist_live_summary_fn=persist_live_summary_fn,
        update_learning_fn=update_learning_fn,
        save_host_state_fn=save_host_state_fn,
        reprioritize_queues_fn=services.reprioritize_queues_fn,
        attack_family_fn=attack_family_fn,
    )


def apply_runtime_adaptation(*, services: RuntimePersistServices, run_info: dict) -> str:
    adaptation_signal = run_info.get('adaptation_signal') if isinstance(run_info.get('adaptation_signal'), dict) else {}
    if bool(adaptation_signal.get('should_regenerate')):
        reason = str(adaptation_signal.get('reason') or '')
        services.maybe_trigger_plan_regeneration_fn(reason)
        return reason
    return ''
