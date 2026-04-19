from __future__ import annotations

from status_utils import normalize_auditor_decision, normalize_engine_status  # type: ignore
import auto_campaign_signals as acs  # type: ignore


def classify(result: dict) -> str:
    engine = result.get("engine") or {}
    stdout = (engine.get("stdout") or "").lower()
    if "method not allowed" in stdout:
        return "method_enforced"
    if "forbidden" in stdout or "unauthorized" in stdout:
        return "authz_enforced"
    if "not found" in stdout:
        return "not_found_enforced"
    if "invalid" in stdout and "parameter" in stdout:
        return "input_validated"
    if "results" in stdout and "[]" in stdout:
        return "empty_response"
    if "health" in stdout and "ok" in stdout:
        return "healthy_endpoint"
    return "unknown"


def summarize_result(result: dict) -> tuple[str, str, str, str, bool]:
    classification = "failed"
    auditor = "unknown"
    engine_status = "unknown"
    summary_text = "No output — engine returned empty stdout/stderr."
    error_flag = False
    if isinstance(result, dict):
        classification = classify(result) if "engine" in result else "failed"
        auditor = normalize_auditor_decision((result.get("auditor") or {}).get("decision"))
        engine_status = normalize_engine_status((result.get("engine") or {}).get("status"))
        eng = (result.get("engine") or {}) if isinstance(result.get("engine"), dict) else {}
        stdout_preview = str(eng.get("stdout") or "")[:300]
        stderr_preview = str(eng.get("stderr") or "")[:220]
        engine_reason = str(eng.get("reason") or "").strip()
        if stdout_preview:
            summary_text = stdout_preview
        elif stderr_preview:
            summary_text = f"Engine stderr: {stderr_preview}"
        elif engine_reason:
            summary_text = f"Engine error: {engine_reason}"
        elif result.get("error"):
            summary_text = str(result.get("error"))

        metrics = acs.parse_rc_metrics(str(eng.get("stdout") or "") + "\n" + str(eng.get("stderr") or ""))
        code = str(metrics.get("code") or "").strip()
        if code == "000":
            summary_text = "Request failed before HTTP response (code=000): likely DNS/connect/TLS/network path issue."
            classification = "failed"
        elif code == "403":
            summary_text = "Blocked by origin/WAF policy (HTTP 403)."
            classification = "blocked"
        elif code.isdigit() and int(code) >= 500 and classification == "unknown":
            classification = "mid"
        elif code.isdigit() and int(code) in {401, 403, 429} and classification == "unknown":
            classification = "blocked"

        error_flag = bool(result.get("error"))
    return classification, auditor, engine_status, summary_text, error_flag
