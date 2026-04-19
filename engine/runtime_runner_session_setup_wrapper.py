from __future__ import annotations

from typing import Callable


def build_main_session_base_fields(*, build_main_session_base_fields_fn: Callable[..., object], state) -> object:
    return build_main_session_base_fields_fn(state)


def build_main_session_alias_fields(*, build_main_session_alias_fields_fn: Callable[..., object], state_aliases, queue_coordinator) -> object:
    return build_main_session_alias_fields_fn(
        state_aliases=state_aliases,
        queue_coordinator=queue_coordinator,
    )


def build_main_session_setup(*, build_main_session_setup_fn: Callable[..., object], state, build_main_runtime_controls_fn: Callable[..., object], build_main_state_aliases_fn: Callable[..., object], build_queue_coordinator_fn: Callable[..., object], build_main_session_alias_fields_fn: Callable[..., object]) -> object:
    return build_main_session_setup_fn(
        state=state,
        build_main_runtime_controls_fn=build_main_runtime_controls_fn,
        build_main_state_aliases_fn=build_main_state_aliases_fn,
        build_queue_coordinator_fn=build_queue_coordinator_fn,
        build_main_session_alias_fields_fn=build_main_session_alias_fields_fn,
    )
