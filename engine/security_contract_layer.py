from __future__ import annotations

import sys
from pathlib import Path

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[1]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from govengine.context import ravenclaw_context

_CONTEXT = ravenclaw_context(Path(__file__))
ROOT = _CONTEXT.repo_root

from sclite.artifacts import *  # noqa: F401,F403
from sclite.redaction import sanitize_public_artifact  # noqa: F401
from sclite.scope_fidelity import (  # noqa: F401
    build_scope_fidelity_report,
    build_scope_fidelity_report_from_approved_spec,
    summarize_scope_fidelity,
    validate_scope_fidelity_report as _sclite_validate_scope_fidelity_report,
)
from scl_ravenclaw_adapter import (  # noqa: F401
    LIFECYCLE_TRACE_FILES_V02,
    build_evidence_contract_v02,
    build_execution_contract_v02,
    build_execution_receipt_v02,
    build_execution_ticket_v02,
    build_intent_contract_v02,
    build_lifecycle_artifacts_v02,
    build_policy_decision_artifact,
    build_policy_decision_artifact_v02,
    build_proof_trace_artifacts,
    redact_prepared_execution_spec as redact_prepared_spec,
)


def repo_root() -> Path:
    """Return the Ravenclaw compatibility repo root through GovEngine context."""
    return _CONTEXT.repo_root

def validate_scope_fidelity_report(report, root: Path | None = None) -> None:
    """Compatibility wrapper for pre-SCLite Ravenclaw callers."""
    _sclite_validate_scope_fidelity_report(report)

