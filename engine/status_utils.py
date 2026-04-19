from __future__ import annotations

from typing import Optional

VALID_ENGINE_STATUSES = {
    "success",
    "completed",
    "failed",
    "error",
    "timeout",
    "dry-run",
    "pending",
    "skipped",
    "rejected",
}
_ENGINE_STATUS_ALIASES = {
    "succeeded": "success",
    "ok": "success",
}


def normalize_engine_status(value: Optional[str]) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    text = _ENGINE_STATUS_ALIASES.get(text, text)
    if text in VALID_ENGINE_STATUSES:
        return text
    return "unknown"


def normalize_auditor_decision(value: Optional[str]) -> str:
    allowed = {"approve", "owner_approval_required", "reject", "deny", "blocked"}
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    if text in allowed:
        return text
    if text.startswith("owner_author") or "owner approval" in text:
        return "owner_approval_required"
    return "blocked"


def normalize_pipeline_status(engine_status: Optional[str], auditor_decision: Optional[str], error_flag: bool) -> str:
    status = normalize_engine_status(engine_status)
    decision = normalize_auditor_decision(auditor_decision)
    if status in {"success", "completed"}:
        return "success"
    if decision in {"owner_approval_required", "reject", "deny", "blocked"}:
        return "blocked"
    if status in {"failed", "error", "timeout", "rejected"} or error_flag:
        return "failed"
    if status in {"dry-run", "skipped", "pending", "unknown"}:
        return "warning"
    return status
