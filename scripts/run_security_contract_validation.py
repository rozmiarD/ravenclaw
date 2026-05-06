#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
for path in (ROOT, ENGINE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scl_validation_runner import *  # noqa: F401,F403
from scl_validation_runner import _build_receipt, _print_markdown, validation_receipt_main as main  # noqa: F401


if __name__ == '__main__':
    raise SystemExit(main())
