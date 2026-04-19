from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ProtocolResult:
    vuln_class: str
    required_steps: List[str]
    passed_steps: List[str]
    failed_steps: List[str]
    repro_pass: bool
    reason: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "vuln_class": self.vuln_class,
            "required_steps": self.required_steps,
            "passed_steps": self.passed_steps,
            "failed_steps": self.failed_steps,
            "repro_pass": self.repro_pass,
            "reason": self.reason,
        }


def _has_any(text: str, toks: List[str]) -> bool:
    t = (text or "").lower()
    return any(k in t for k in toks)


def protocol_for(vuln_class: str, evidence: Dict[str, Any]) -> ProtocolResult:
    vc = str(vuln_class or "generic").lower()
    summary = str(evidence.get("summary_text") or "")
    findings = [str(x).lower() for x in (evidence.get("signal_codes") or [])]
    control_performed = bool(evidence.get("control_comparison_performed", False))
    control_delta = bool(evidence.get("control_delta_observed", False))
    repeated_consistency = bool(evidence.get("repeated_consistency", False))

    if vc == "idor":
        required = [
            "control_comparison_performed",
            "control_delta_observed",
            "authz_boundary_artifact",
            "repeated_consistency",
        ]
        passed = []
        failed = []
        if control_performed:
            passed.append("control_comparison_performed")
        else:
            failed.append("control_comparison_performed")
        if control_delta:
            passed.append("control_delta_observed")
        else:
            failed.append("control_delta_observed")
        if ("authz_boundary_signal" in findings) or _has_any(summary, ["owner_id", "account_id", "tenant_id", "permissions"]):
            passed.append("authz_boundary_artifact")
        else:
            failed.append("authz_boundary_artifact")
        if repeated_consistency:
            passed.append("repeated_consistency")
        else:
            failed.append("repeated_consistency")
        return ProtocolResult(vc, required, passed, failed, repro_pass=len(failed) == 0, reason="idor_protocol")

    if vc == "xss":
        required = [
            "control_comparison_performed",
            "control_delta_observed",
            "sink_or_reflection_artifact",
            "repeated_consistency",
        ]
        passed = []
        failed = []
        if control_performed:
            passed.append("control_comparison_performed")
        else:
            failed.append("control_comparison_performed")
        if control_delta:
            passed.append("control_delta_observed")
        else:
            failed.append("control_delta_observed")
        if _has_any(summary, ["<script", "onerror", "onload", "javascript:", "xss"]):
            passed.append("sink_or_reflection_artifact")
        else:
            failed.append("sink_or_reflection_artifact")
        if repeated_consistency:
            passed.append("repeated_consistency")
        else:
            failed.append("repeated_consistency")
        return ProtocolResult(vc, required, passed, failed, repro_pass=len(failed) == 0, reason="xss_protocol")

    # generic fallback protocol
    required = ["control_comparison_performed", "control_delta_observed"]
    passed = []
    failed = []
    if control_performed:
        passed.append("control_comparison_performed")
    else:
        failed.append("control_comparison_performed")
    if control_delta:
        passed.append("control_delta_observed")
    else:
        failed.append("control_delta_observed")
    return ProtocolResult(vc, required, passed, failed, repro_pass=len(failed) == 0, reason="generic_protocol")
