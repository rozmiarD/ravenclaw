from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import verify_request_decoration_contract as vrdc  # type: ignore


def test_verify_request_decoration_contract_passes() -> None:
    assert vrdc.main() == 0
