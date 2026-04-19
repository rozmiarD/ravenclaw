from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_session_setup_wrapper as rrssw  # type: ignore


def test_build_main_session_base_fields_delegates() -> None:
    marker = object()
    out = rrssw.build_main_session_base_fields(
        build_main_session_base_fields_fn=lambda state: marker,
        state=object(),
    )
    assert out is marker


def test_build_main_session_alias_fields_delegates() -> None:
    captured = {}

    def fake_build_main_session_alias_fields(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return 'ok'

    out = rrssw.build_main_session_alias_fields(
        build_main_session_alias_fields_fn=fake_build_main_session_alias_fields,
        state_aliases=object(),
        queue_coordinator=object(),
    )
    assert out == 'ok'
    assert 'state_aliases' in captured


def test_build_main_session_setup_delegates() -> None:
    captured = {}

    def fake_build_main_session_setup(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return 'setup'

    out = rrssw.build_main_session_setup(
        build_main_session_setup_fn=fake_build_main_session_setup,
        state=object(),
        build_main_runtime_controls_fn=lambda state: object(),
        build_main_state_aliases_fn=lambda state: object(),
        build_queue_coordinator_fn=lambda runs, followup_queue, precision_queue: object(),
        build_main_session_alias_fields_fn=lambda state_aliases, queue_coordinator: object(),
    )
    assert out == 'setup'
    assert callable(captured['build_main_runtime_controls_fn'])
