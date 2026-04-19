from __future__ import annotations

from aggression_policy import clamp_aggression  # type: ignore

LOW_SIGNAL_CLASSES = {
    "method_enforced",
    "authz_enforced",
    "not_found_enforced",
    "input_validated",
    "empty_response",
    "healthy_endpoint",
    "failed",
}

PROMISING_KEYWORDS = (
    "xss", "idor", "sqli", "sql injection", "csrf", "ssrf", "rce", "lfi",
    "shell", "credential", "token", "leak", "expos", "vuln", "finding",
    "override", "bypass", "interesting", "potential",
)


def maybe_reconsult_planner(toggles: dict, runs: list[dict], promising_count: int) -> bool:
    if not bool(toggles.get("planner_reconsult_on_high_signal", False)):
        return False
    min_interval = max(1, int(toggles.get("planner_reconsult_min_interval_runs", 10) or 10))
    threshold = max(1, int(toggles.get("planner_reconsult_signal_threshold", 2) or 2))
    if promising_count < threshold:
        return False
    if len(runs) % min_interval != 0:
        return False
    return True


def is_promising(summary: str | None, classification: str | None = None) -> bool:
    summary_text = (summary or "").lower()
    cls = (classification or "").lower()
    if cls and cls not in LOW_SIGNAL_CLASSES:
        return True
    low_signal_phrases = (
        'request completed and response was saved', 'could not resolve host',
        'tls/ssl connect error', 'engine ended with status', '__rc_metrics__',
        'no output', 'dns_unresolvable',
    )
    if any(p in summary_text for p in low_signal_phrases):
        return False
    return any(keyword in summary_text for keyword in PROMISING_KEYWORDS)


def is_strong_security_signal(classification: str | None, reason_code: str | None, summary: str | None = None) -> bool:
    cls = (classification or '').lower()
    rc = (reason_code or '').lower()
    s = (summary or '').lower()
    if cls in {'high', 'critical'}:
        return True
    security_reason_tokens = (
        'idor', 'bola', 'xss', 'sqli', 'ssrf', 'rce', 'csrf', 'bypass', 'authz', 'auth', 'token_leak', 'exposure',
    )
    if any(tok in rc for tok in security_reason_tokens):
        return True
    return any(tok in s for tok in security_reason_tokens)


def adaptive_aggression(base: int, classification: str, reason_code: str, owner_override: bool = False) -> int:
    b = clamp_aggression(int(base or 1))
    cls = str(classification or '').lower()
    rc = str(reason_code or '').lower()
    if cls == 'critical':
        return clamp_aggression(8 if owner_override else 6)
    if cls == 'high':
        return clamp_aggression(6 if owner_override else 5)
    if cls in {'mid', 'medium'} or any(k in rc for k in ['idor', 'bola', 'authz', 'business_logic_signal', 'secret_leak_signal']):
        return clamp_aggression(max(b, 4 if owner_override else 3))
    return clamp_aggression(max(1, min(3, b)))
