from __future__ import annotations

"""Compatibility wrapper for the GovEngine policy core seam."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from govengine.policy.core import *  # noqa: F401,F403
