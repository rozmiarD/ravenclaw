from __future__ import annotations

from typing import Any, Dict


def can_be_confirmed(qualification: Dict[str, Any], *, require_repro_pass: bool = True) -> bool:
    if not isinstance(qualification, dict):
        return False
    if str(qualification.get("verdict") or "") != "confirmed":
        return False
    if not bool(qualification.get("false_positive_guards_passed", False)):
        return False
    obs = qualification.get("observed_artifacts") or {}
    if not isinstance(obs, dict):
        return False
    if not bool(obs.get("control_comparison_performed", False)):
        return False
    if not bool(obs.get("control_delta_observed", False)):
        return False
    proto = obs.get("protocol") or {}
    if not isinstance(proto, dict):
        proto = {}
    if require_repro_pass and not bool(proto.get("repro_pass", False)):
        return False
    return True
