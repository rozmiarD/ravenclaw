from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_state_aliases_wrapper as rrsaw  # type: ignore


def test_build_main_state_aliases_delegates() -> None:
    marker = object()
    out = rrsaw.build_main_state_aliases(
        build_main_state_aliases_fn=lambda state: marker,
        state=object(),
    )
    assert out is marker
