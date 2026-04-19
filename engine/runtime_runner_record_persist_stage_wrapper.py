from __future__ import annotations

from typing import Callable


def run_record_and_persist_stage(*, run_record_and_persist_stage_fn: Callable[..., float], build_record_and_persist_run_inputs_fn: Callable[..., object], record_and_persist_runtime_run_fn: Callable[..., float], services, state, run_info: dict, last_persist_ts: float, persist_live_summary_fn: Callable[[], None], update_learning_fn: Callable[..., None], save_host_state_fn: Callable[..., None], attack_family_fn: Callable[[str, str, str], str]) -> float:
    return run_record_and_persist_stage_fn(
        build_record_and_persist_run_inputs_fn=build_record_and_persist_run_inputs_fn,
        record_and_persist_runtime_run_fn=record_and_persist_runtime_run_fn,
        services=services,
        state=state,
        run_info=run_info,
        last_persist_ts=last_persist_ts,
        persist_live_summary_fn=persist_live_summary_fn,
        update_learning_fn=update_learning_fn,
        save_host_state_fn=save_host_state_fn,
        attack_family_fn=attack_family_fn,
    )
