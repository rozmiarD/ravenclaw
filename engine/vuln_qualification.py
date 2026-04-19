from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Tuple

try:
    from proof_protocols import protocol_for  # type: ignore
except Exception:  # pragma: no cover
    from engine.proof_protocols import protocol_for  # type: ignore


VERDICT_ORDER = {"none": 0, "weak_signal": 1, "probable": 2, "confirmed": 3}


@dataclass
class QualificationResult:
    vuln_class: str
    probe_id: str
    request_fingerprint: str
    expected_success_criteria: List[str]
    observed_artifacts: Dict[str, Any]
    false_positive_guards_passed: bool
    verdict: str
    confidence: float
    reason_code: str
    disposition: str = "standard"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "vuln_class": self.vuln_class,
            "probe_id": self.probe_id,
            "request_fingerprint": self.request_fingerprint,
            "expected_success_criteria": self.expected_success_criteria,
            "observed_artifacts": self.observed_artifacts,
            "false_positive_guards_passed": self.false_positive_guards_passed,
            "verdict": self.verdict,
            "confidence": round(float(self.confidence), 3),
            "reason_code": self.reason_code,
            "disposition": self.disposition,
        }


def infer_vuln_class(objective: str, reason_code: str, signal_codes: List[str]) -> str:
    text = f"{objective} {reason_code} {' '.join(signal_codes)}".lower()
    checks = [
        ("xss", ["xss", "script", "onerror", "onload"]),
        ("idor", ["idor", "bola", "authz_boundary", "object id", "owner_id"]),
        ("sqli", ["sqli", "sql", "injection", "sql syntax"]),
        ("csrf", ["csrf"]),
        ("ssrf", ["ssrf", "metadata", "169.254"]),
        ("business_logic", ["business", "idempotency", "replay", "state transition"]),
        ("auth_bypass", ["bypass", "unauthorized", "forbidden", "auth"]),
    ]
    for label, toks in checks:
        if any(tok in text for tok in toks):
            return label
    return "generic"


def _criteria_for(vuln_class: str) -> List[str]:
    mapping = {
        "idor": [
            "cross-object access behavior observed",
            "unauthorized object fields visible",
            "control comparison differs from baseline",
        ],
        "xss": [
            "canary reflection observed",
            "unsafe sink/context detected",
            "control payload does not trigger same behavior",
        ],
        "sqli": [
            "stable diff between probe and control",
            "database-error/time/boolean behavior pattern",
            "repeated probe consistency",
        ],
        "auth_bypass": [
            "access succeeds without expected auth boundary",
            "control request remains denied",
        ],
        "ssrf": [
            "server-side fetch indicator observed",
            "control target does not produce same side effect",
        ],
        "business_logic": [
            "state anomaly observed",
            "idempotency/control comparison confirms inconsistency",
        ],
    }
    return mapping.get(vuln_class, ["high-signal anomaly observed", "control comparison available"])


def _score_artifacts(vuln_class: str, artifacts: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []
    status_code = str(artifacts.get("http_code") or "")
    findings = [str(x).lower() for x in (artifacts.get("findings") or [])]
    reason_code = str(artifacts.get("reason_code") or "").lower()
    text = str(artifacts.get("summary_text") or "").lower()

    if any(code in reason_code for code in ["owner_approval_required", "policy_gate", "out_of_scope"]):
        return 0.0, ["policy_block"]

    if status_code and status_code.isdigit() and int(status_code) >= 500:
        score += 0.25
        reasons.append("http_5xx")
    if status_code in {"401", "403", "429"}:
        score += 0.05
        reasons.append("access_control_signal")

    if any(k in text for k in ["traceback", "exception", "sql syntax", "unauthorized", "forbidden", "bypass"]):
        score += 0.2
        reasons.append("diagnostic_text_signal")

    if findings:
        score += min(0.35, 0.12 * len(findings))
        reasons.append("structured_findings")

    if vuln_class == "idor" and any(k in text for k in ["owner_id", "account_id", "tenant_id", "permissions"]):
        score += 0.2
        reasons.append("idor_field_signal")
    if vuln_class == "xss" and any(k in text for k in ["<script", "onerror", "onload", "javascript:"]):
        score += 0.25
        reasons.append("xss_sink_signal")
    if vuln_class == "sqli" and any(k in text for k in ["sql syntax", "database error", "mysql", "postgres", "sqlite"]):
        score += 0.25
        reasons.append("sqli_engine_signal")

    return min(1.0, score), reasons


def _resolved_http_code(observed: Dict[str, Any]) -> str:
    code = str(observed.get("http_code") or "").strip()
    if code:
        return code
    txt = f"{observed.get('summary_text') or ''} {observed.get('reason_code') or ''}".lower()
    m = re.search(r"code\s*=\s*(\d{3})", txt)
    if m:
        return m.group(1)
    m2 = re.search(r"http\s*(\d{3})", txt)
    if m2:
        return m2.group(1)
    return ""



def _boundary_context_signal(evidence: Dict[str, Any], observed: Dict[str, Any], signal_codes: List[str]) -> bool:
    task_family = str(evidence.get('task_family') or '').strip().lower()
    text = f"{observed.get('summary_text') or ''} {observed.get('reason_code') or ''}".lower()
    signals = {str(x or '').strip().lower() for x in (signal_codes or []) if str(x or '').strip()}
    actor_or_session_prerequisites = [str(x or '').strip().lower() for x in (evidence.get('actor_or_session_prerequisites') or []) if str(x or '').strip()]
    acceptance_checks = [str(x or '').strip().lower() for x in (evidence.get('acceptance_checks') or []) if str(x or '').strip()]
    family_match = task_family in {'authz', 'idor', 'auth_flow', 'workflow', 'logic', 'state_transition'}
    token_match = any(tok in text for tok in ['owner_id', 'account_id', 'tenant_id', 'profile', 'order', 'session', 'workflow', 'transition', 'boundary', 'actor'])
    signal_match = bool(signals & {'authz_boundary_signal', 'state_transition_signal', 'control_delta_signal', 'boundary_context_signal'})
    prerequisite_match = any(tok in ' '.join(actor_or_session_prerequisites) for tok in ['actor', 'session', 'account', 'tenant', 'profile', 'order'])
    acceptance_match = any(tok in ' '.join(acceptance_checks) for tok in ['cross-actor', 'cross actor', 'state transition', 'workflow', 'boundary', 'session'])
    return bool(family_match or token_match or signal_match or prerequisite_match or acceptance_match)



def _qualification_disposition(reason_code: str, auditor_decision: str, in_scope: bool) -> str:
    rc = str(reason_code or '').strip().lower()
    auditor = str(auditor_decision or '').strip().lower()
    if not bool(in_scope):
        return 'out_of_scope'
    if auditor in {'owner_approval_required', 'reject', 'deny', 'blocked'}:
        return 'governance_blocked'
    if any(code in rc for code in ['owner_approval_required', 'policy_gate', 'out_of_scope']):
        return 'governance_blocked' if 'out_of_scope' not in rc else 'out_of_scope'
    return 'standard'


def qualify(evidence: Dict[str, Any]) -> QualificationResult:
    objective = str(evidence.get("objective") or "")
    reason_code = str(evidence.get("reason_code") or "")
    signal_codes = [str(x) for x in (evidence.get("signal_codes") or [])]
    vuln_class = infer_vuln_class(objective, reason_code, signal_codes)
    criteria = _criteria_for(vuln_class)

    observed = {
        "http_code": evidence.get("http_code"),
        "findings": signal_codes,
        "reason_code": reason_code,
        "summary_text": str(evidence.get("summary_text") or ""),
        "engine_status": evidence.get("engine_status"),
        "auditor_decision": evidence.get("auditor_decision"),
        "control_comparison_performed": bool(evidence.get("control_comparison_performed", False)),
        "control_delta_observed": bool(evidence.get("control_delta_observed", False)),
        "repeated_consistency": bool(evidence.get("repeated_consistency", False)),
    }

    base_score, reasons = _score_artifacts(vuln_class, observed)

    disposition = _qualification_disposition(
        reason_code,
        str(observed.get("auditor_decision") or ""),
        bool(evidence.get("in_scope", True)),
    )
    guards_passed = bool(evidence.get("in_scope", True)) and str(observed.get("auditor_decision") or "") not in {
        "blocked", "reject", "owner_approval_required", "deny"
    }

    confidence = base_score
    if not guards_passed:
        confidence = min(confidence, 0.29)

    control_cmp = bool(observed.get("control_comparison_performed"))
    control_delta = bool(observed.get("control_delta_observed"))

    # Weak-signal floor for auth-like probes with meaningful HTTP control-path responses.
    # This helps queue escalation when status stays mostly 302/401/403 but checks are actually executed.
    http_code = _resolved_http_code(observed)
    task_family = str(evidence.get('task_family') or '').strip().lower()
    auth_like = vuln_class in {"auth_bypass", "xss", "idor", "csrf", "generic"} or task_family in {'authz', 'idor', 'auth_flow', 'workflow', 'logic', 'state_transition'}
    repeated_consistency = bool(observed.get("repeated_consistency"))
    if (
        guards_passed
        and auth_like
        and (control_cmp or repeated_consistency)
        and http_code in {"302", "307", "308", "401", "403"}
        and confidence < 0.30
    ):
        confidence = 0.31
        reasons.append("http_control_path_weak_signal")

    # Optional hard floor: force weak-signal on auth-like HTTP control paths.
    force_weak_http = bool(observed.get("force_auth_like_weak_on_http_controls", False))
    status_4xx = bool(http_code) and str(http_code).startswith("4")
    strong_http_gate = http_code in {"301", "302", "307", "308", "401", "403"}
    allow_404_context = (http_code == "404") and (control_delta or repeated_consistency)
    boundary_context_signal = _boundary_context_signal(evidence, observed, signal_codes)
    early_boundary_context_promotable = bool(
        guards_passed
        and auth_like
        and control_cmp
        and boundary_context_signal
        and str(observed.get('engine_status') or '').lower() in {'success', 'ok'}
        and (strong_http_gate or status_4xx or http_code == '404')
    )
    boundary_context_promotable = bool(
        early_boundary_context_promotable
        and repeated_consistency
    )
    if early_boundary_context_promotable and not repeated_consistency and confidence < 0.45:
        confidence = 0.45
        reasons.append('early_boundary_context_promoted')
    if boundary_context_promotable and not control_delta and confidence < 0.60:
        confidence = 0.60
        reasons.append('boundary_context_promoted')

    if (
        force_weak_http
        and not early_boundary_context_promotable
        and guards_passed
        and auth_like
        and str(observed.get("engine_status") or "").lower() in {"success", "ok"}
        and (strong_http_gate or allow_404_context or (status_4xx and control_cmp and (control_delta or repeated_consistency)))
        and confidence < 0.30
    ):
        confidence = 0.31
        reasons.append("forced_weak_signal_http_gate")

    proto = protocol_for(vuln_class, {
        "summary_text": observed.get("summary_text"),
        "signal_codes": signal_codes,
        "control_comparison_performed": control_cmp,
        "control_delta_observed": control_delta,
        "repeated_consistency": bool(observed.get("repeated_consistency", False)),
    }).as_dict()

    if confidence >= 0.85 and guards_passed and control_cmp and control_delta and bool(proto.get("repro_pass", False)):
        verdict = "confirmed"
    elif confidence >= 0.6 and guards_passed:
        verdict = "probable"
    elif confidence >= 0.3:
        verdict = "weak_signal"
    else:
        verdict = "none"

    # Escalation bridge: promote weak -> probable when control delta is observed on guarded in-scope runs.
    if (
        verdict == "weak_signal"
        and guards_passed
        and control_cmp
        and control_delta
        and str(observed.get("engine_status") or "").lower() in {"success", "ok"}
    ):
        verdict = "probable"
        confidence = max(confidence, 0.61)
        reasons.append("control_delta_promoted")

    # Negative-control gate: no confirmed without control comparison.
    if verdict == "confirmed" and not (control_cmp and control_delta):
        verdict = "probable"

    reason = "|".join(reasons[:4]) if reasons else "low_signal"
    observed["protocol"] = proto

    return QualificationResult(
        vuln_class=vuln_class,
        probe_id=str(evidence.get("probe_id") or "probe-unknown"),
        request_fingerprint=str(evidence.get("request_fingerprint") or ""),
        expected_success_criteria=criteria,
        observed_artifacts=observed,
        false_positive_guards_passed=guards_passed,
        verdict=verdict,
        confidence=confidence,
        reason_code=f"qualification:{vuln_class}:{verdict}:{reason}",
        disposition=disposition,
    )


def verdict_at_least(verdict: str, threshold: str) -> bool:
    return VERDICT_ORDER.get(str(verdict or "none"), 0) >= VERDICT_ORDER.get(str(threshold or "none"), 0)
