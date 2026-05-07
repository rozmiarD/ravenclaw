from __future__ import annotations

"""Compatibility module alias for the GovEngine SCLite adapter seam."""

from pathlib import Path
import importlib
import sys

_ROOT = Path(__file__).resolve().parents[1]
_ENGINE = Path(__file__).resolve().parent
for _path in (_ROOT, _ENGINE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

_impl = importlib.import_module('govengine.sclite_adapter')
sys.modules[__name__] = _impl
