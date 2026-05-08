from __future__ import annotations

"""Compatibility module alias for the GovEngine policy core seam."""

from pathlib import Path
import importlib
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_impl = importlib.import_module('govengine.policy.core')
sys.modules[__name__] = _impl
