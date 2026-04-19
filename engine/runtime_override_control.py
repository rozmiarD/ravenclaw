from __future__ import annotations

from typing import Callable


def refresh_runtime_overrides(
    *,
    owner_override_global: bool,
    last_override_state: bool,
    aggression_override_global: int | None,
    last_aggression_override: int | None,
    read_runtime_owner_override_fn: Callable[..., bool],
    read_runtime_aggression_override_fn: Callable[[], int | None],
    log_event_fn: Callable[..., None],
) -> tuple[bool, bool, int | None, int | None]:
    owner_override_global = read_runtime_owner_override_fn(default=owner_override_global)
    if owner_override_global != last_override_state:
        log_event_fn(
            'AUTO_CAMPAIGN',
            'owner_override_runtime',
            'warning',
            f'owner_override_changed:{owner_override_global}',
            actor='auto_campaign',
            row_type='service',
        )
        last_override_state = owner_override_global

    aggression_override_global = read_runtime_aggression_override_fn()
    if aggression_override_global != last_aggression_override:
        log_event_fn(
            'AUTO_CAMPAIGN',
            'aggression_override_runtime',
            'warning',
            f'aggression_override_changed:{last_aggression_override}->{aggression_override_global}',
            actor='auto_campaign',
            row_type='service',
        )
        last_aggression_override = aggression_override_global
    return owner_override_global, last_override_state, aggression_override_global, last_aggression_override
