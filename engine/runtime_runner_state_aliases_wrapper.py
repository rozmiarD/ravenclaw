from __future__ import annotations

from typing import Callable


def build_main_state_aliases(*, build_main_state_aliases_fn: Callable[..., object], state) -> object:
    return build_main_state_aliases_fn(state)
