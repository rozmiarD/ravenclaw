from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sclite.artifacts import *  # noqa: F401,F403
from sclite.redaction import sanitize_public_artifact  # noqa: F401
from scl_ravenclaw_adapter import (  # noqa: F401
    build_policy_decision_artifact,
    build_proof_trace_artifacts,
    redact_prepared_execution_spec as redact_prepared_spec,
)


def repo_root() -> Path:
    """Return Ravenclaw's repository root, not the installed SCLite package root."""
    return ROOT
