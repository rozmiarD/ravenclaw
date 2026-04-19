from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_override_control import refresh_runtime_overrides  # type: ignore


def test_refresh_runtime_overrides_updates_values_and_logs_changes() -> None:
    events = []
    owner, last_owner, aggression, last_aggr = refresh_runtime_overrides(
        owner_override_global=False,
        last_override_state=False,
        aggression_override_global=None,
        last_aggression_override=None,
        read_runtime_owner_override_fn=lambda default=False: True,
        read_runtime_aggression_override_fn=lambda: 7,
        log_event_fn=lambda *args, **kwargs: events.append((args, kwargs)),
    )
    assert owner is True
    assert last_owner is True
    assert aggression == 7
    assert last_aggr == 7
    assert any(args[1] == 'owner_override_runtime' for args, _kwargs in events)
    assert any(args[1] == 'aggression_override_runtime' for args, _kwargs in events)
