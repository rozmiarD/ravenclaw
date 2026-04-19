from __future__ import annotations

from typing import Callable


def refresh_main_runtime_overrides(*, refresh_main_runtime_overrides_fn: Callable[..., tuple[bool, bool, int | None, int | None]], owner_override_global: bool, last_override_state: bool, aggression_override_global: int | None, last_aggression_override: int | None, apply_runtime_overrides_fn: Callable[..., bool], read_runtime_owner_override_fn: Callable[[], bool], read_runtime_aggression_override_fn: Callable[[], int | None], log_event_fn: Callable[..., None]) -> tuple[bool, bool, int | None, int | None]:
    return refresh_main_runtime_overrides_fn(
        owner_override_global,
        last_override_state,
        aggression_override_global,
        last_aggression_override,
        apply_runtime_overrides_fn=apply_runtime_overrides_fn,
        read_runtime_owner_override_fn=read_runtime_owner_override_fn,
        read_runtime_aggression_override_fn=read_runtime_aggression_override_fn,
        log_event_fn=log_event_fn,
    )
