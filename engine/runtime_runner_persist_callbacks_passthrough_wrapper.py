from __future__ import annotations

from typing import Callable


def build_main_persist_callbacks(*, build_main_persist_callbacks_fn: Callable[..., dict], persist_services, state, last_persist_ts_ref: list[float], persist_live_summary_fn: Callable[[], None], run_record_and_persist_stage_fn: Callable[..., float], apply_runtime_adaptation_fn: Callable[[dict], None]) -> dict:
    return build_main_persist_callbacks_fn(
        persist_services=persist_services,
        state=state,
        last_persist_ts_ref=last_persist_ts_ref,
        persist_live_summary_fn=persist_live_summary_fn,
        run_record_and_persist_stage_fn=run_record_and_persist_stage_fn,
        apply_runtime_adaptation_fn=apply_runtime_adaptation_fn,
    )
