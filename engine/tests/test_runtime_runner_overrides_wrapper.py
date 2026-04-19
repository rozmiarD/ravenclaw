from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_overrides_wrapper as rrow  # type: ignore


def test_refresh_main_runtime_overrides_delegates() -> None:
    captured = {}

    def fake_refresh_main_runtime_overrides(*args, **kwargs):  # type: ignore[no-untyped-def]
        captured['args'] = args
        captured['kwargs'] = kwargs
        return True, False, 5, 4

    out = rrow.refresh_main_runtime_overrides(
        refresh_main_runtime_overrides_fn=fake_refresh_main_runtime_overrides,
        owner_override_global=False,
        last_override_state=False,
        aggression_override_global=None,
        last_aggression_override=None,
        apply_runtime_overrides_fn=lambda *args, **kwargs: True,
        read_runtime_owner_override_fn=lambda: False,
        read_runtime_aggression_override_fn=lambda: None,
        log_event_fn=lambda *args, **kwargs: None,
    )
    assert out == (True, False, 5, 4)
    assert callable(captured['kwargs']['log_event_fn'])
