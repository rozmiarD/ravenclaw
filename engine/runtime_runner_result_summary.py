from __future__ import annotations

from status_utils import normalize_auditor_decision, normalize_engine_status  # type: ignore


def build_auditor_block_summary(result: dict, auditor: str) -> str:
    aud = (result.get("auditor") or {}) if isinstance(result.get("auditor"), dict) else {}
    auditor_reason = str(aud.get("reason") or "").strip()
    reason_code = str(aud.get("reason_code") or "").strip()
    if auditor_reason:
        prefix = f"[{reason_code}] " if reason_code else ""
        return f"Blocked by auditor/policy: {prefix}{auditor_reason[:180]}"
    return f"No output — blocked by auditor/policy ({auditor})."



def returncode_hint(rc: object) -> str | None:
    if not (isinstance(rc, int) or (isinstance(rc, str) and str(rc).isdigit())):
        return None
    return {
        6: "Could not resolve host (DNS resolution failure).",
        7: "Failed to connect to host (connection refused/timeout/network path issue).",
        22: "HTTP response >= 400 with --fail semantics.",
        28: "Operation timeout reached.",
        35: "TLS/SSL connect error.",
        47: "Too many redirects.",
        56: "Failure in receiving network data.",
    }.get(int(rc))



def build_failed_engine_summary(engine_status: str, eng: dict, stderr_preview: str, engine_reason: str) -> str:
    rc = eng.get("returncode")
    rc_hint = returncode_hint(rc)
    if stderr_preview:
        return f"Failed — {rc_hint + ' ' if rc_hint else ''}stderr: {stderr_preview}"
    if engine_reason:
        return f"Failed — {rc_hint + ' ' if rc_hint else ''}reason: {engine_reason[:160]}"
    if rc_hint:
        return f"Failed — {rc_hint}"
    return f"Failed — engine ended with status '{engine_status}' (rc={rc})."



def build_summary_text(result: dict, auditor: str, engine_status: str) -> tuple[str, dict]:
    eng = (result.get("engine") or {}) if isinstance(result.get("engine"), dict) else {}
    stdout_preview = str(eng.get("stdout") or "")[:300]
    stderr_preview = str(eng.get("stderr") or "")[:220]
    engine_reason = str(eng.get("reason") or "").strip()
    cmd_text = str(eng.get("command") or "")
    if engine_status in {"success", "ok"}:
        if " -o " in cmd_text or " --output" in cmd_text:
            return "Success — request completed and response was saved to output file (-o).", eng
        if stdout_preview:
            return f"Success — command finished with exit code 0 and returned {len(stdout_preview)}+ chars of output.", eng
        return "Success — command finished with exit code 0 and no errors were reported.", eng
    if stdout_preview:
        return stdout_preview, eng
    if stderr_preview:
        return f"Engine stderr: {stderr_preview}", eng
    if engine_reason:
        return f"Engine error: {engine_reason}", eng
    if result.get("error"):
        return str(result.get("error")), eng
    if auditor in {"blocked", "deny", "reject", "owner_approval_required"}:
        return build_auditor_block_summary(result, auditor), eng
    if engine_status in {"timeout"}:
        return "No output — tool timed out before producing results.", eng
    if engine_status in {"failed", "error", "blocked"}:
        return build_failed_engine_summary(engine_status, eng, stderr_preview, engine_reason), eng
    if engine_status in {"success", "ok"} and (" -o " in cmd_text or " --output" in cmd_text):
        return "No stdout (expected): curl saved response to output file via -o.", eng
    return "No output — empty response from execution tool.", eng



def apply_summary_metric_overrides(classification: str, summary_text: str, eng: dict, parse_rc_metrics_fn) -> tuple[str, str]:
    metrics = parse_rc_metrics_fn(str(eng.get("stdout") or "") + "\n" + str(eng.get("stderr") or ""))
    code = str(metrics.get("code") or "").strip()
    if code == "000":
        summary_text = "Request failed before HTTP response (code=000): likely DNS/connect/TLS/network path issue."
        classification = "failed"
    if 'invalid port' in (summary_text or '').lower() and code == '000':
        summary_text = "Request failed before HTTP response (code=000): transport-layer failure (not an HTTP app response)."
    elif code == "403":
        summary_text = "Blocked by origin/WAF policy (HTTP 403)."
        classification = "blocked"
    elif code.isdigit() and int(code) >= 500:
        summary_text = f"Target server error surfaced (HTTP {code})."
        if classification == "unknown":
            classification = "mid"
    elif code.isdigit() and int(code) in {401, 403, 429} and classification == "unknown":
        classification = "blocked"
    return classification, summary_text



def summarize_result(result: dict, *, classify_fn, parse_rc_metrics_fn) -> tuple[str, str, str, str, bool]:
    classification = "failed"
    auditor = "unknown"
    engine_status = "unknown"
    summary_text = "No output — engine returned empty stdout/stderr."
    error_flag = False
    if isinstance(result, dict):
        classification = classify_fn(result) if "engine" in result else "failed"
        auditor = normalize_auditor_decision((result.get("auditor") or {}).get("decision"))
        engine_status = normalize_engine_status((result.get("engine") or {}).get("status"))
        summary_text, eng = build_summary_text(result, auditor, engine_status)
        classification, summary_text = apply_summary_metric_overrides(classification, summary_text, eng, parse_rc_metrics_fn)
        error_flag = bool(result.get("error"))
    return classification, auditor, engine_status, summary_text, error_flag
