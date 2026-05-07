from __future__ import annotations

"""Compatibility wrapper for the GovEngine SCLite adapter seam."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
_ENGINE = Path(__file__).resolve().parent
for _path in (_ROOT, _ENGINE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from govengine.sclite_adapter import *  # noqa: F401,F403
