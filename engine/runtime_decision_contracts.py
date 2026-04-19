from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


CONFIDENCE_BANDS = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.85,
}
ACTION_KEYS = ("retry", "confirm", "followup", "precision")


def selected_action_flags(selected_action: Any, selected_secondary_action: Any = '') -> Dict[str, bool]:
    selected = str(selected_action or '').strip().lower()
    secondary = str(selected_secondary_action or '').strip().lower()
    out = {k: False for k in ACTION_KEYS}
    if selected in ACTION_KEYS:
        out[selected] = True
    if secondary in ACTION_KEYS and secondary != selected:
        out[secondary] = True
    return out


def canonical_action_flags_from_mapping(value: Any, fallback: Any = None) -> tuple[Dict[str, bool], str]:
    src = value if isinstance(value, dict) else {}
    selected = str(src.get('requested_action') or src.get('selected_primary_action') or '').strip().lower()
    secondary = str(src.get('selected_secondary_action') or '').strip().lower()
    if selected in ACTION_KEYS:
        return selected_action_flags(selected, secondary), 'selected_actions'
    legacy = src.get('intent_flags') or src.get('action_flags')
    if isinstance(legacy, dict):
        return normalize_action_flags(legacy), 'legacy_flags'
    return normalize_action_flags(fallback), 'fallback'


def normalize_confidence(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip().lower()
    if text in CONFIDENCE_BANDS:
        return CONFIDENCE_BANDS[text]
    try:
        return float(text)
    except Exception:
        return 0.0


def normalize_action_flags(value: Any) -> Dict[str, bool]:
    out = {k: False for k in ACTION_KEYS}
    if isinstance(value, dict):
        for key in ACTION_KEYS:
            out[key] = bool(value.get(key, False))
    return out


@dataclass
class QualificationSummary:
    verdict: str = "none"
    confidence: float = 0.0
    reason_code: str = ""
    guards_passed: bool = False

    @classmethod
    def from_qual(cls, qual: Dict[str, Any] | None) -> "QualificationSummary":
        q = qual if isinstance(qual, dict) else {}
        return cls(
            verdict=str(q.get("verdict") or "none"),
            confidence=normalize_confidence(q.get("confidence")),
            reason_code=str(q.get("reason_code") or ""),
            guards_passed=bool(q.get("false_positive_guards_passed", False)),
        )


@dataclass
class DecisionOutcome:
    allowed: bool = False
    reason_code: str = "not_applicable"
    score: float = 0.0
    threshold: str = ""
    blockers: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _selected_action_for_record(record: "RuntimeDecisionRecord") -> tuple[str, str]:
    for name, outcome in (
        ('retry', record.retry),
        ('confirm', record.confirm),
        ('followup', record.followup),
        ('precision', record.precision),
    ):
        if outcome.allowed:
            return name, str(outcome.reason_code or '')
    if record.blocked:
        return '', str(record.blocked_reason or 'auditor_block')
    return '', 'no_action_selected'


@dataclass
class RuntimeDecisionRecord:
    retry: DecisionOutcome
    confirm: DecisionOutcome
    followup: DecisionOutcome
    precision: DecisionOutcome
    blocked: bool = False
    blocked_reason: str = ""
    mode: str = ""
    verdict: str = "none"
    engine_status: str = "unknown"
    auditor_decision: str = "unknown"
    success_eval_status: str = "unknown"
    requested_action: str = ""
    requested_reason: str = ""
    selected_primary_action: str = ""
    selection_reason: str = ""
    selected_secondary_action: str = ""
    secondary_selection_reason: str = ""
    economics: Dict[str, Any] = field(default_factory=dict)
    explain: Dict[str, Any] = field(default_factory=dict)
    effective_status: str = "pending"
    effective_action: str = ""
    effective_secondary_action: str = ""
    effective_flags: Dict[str, bool] = field(default_factory=lambda: normalize_action_flags({}))
    effective_reasons: Dict[str, str] = field(default_factory=dict)
    effective_blockers: Dict[str, List[str]] = field(default_factory=dict)
    effective_summary: str = ""

    def action_flags(self) -> Dict[str, bool]:
        primary, _reason = _selected_action_for_record(self)
        return selected_action_flags(primary, self.selected_secondary_action)

    def effective_action_flags(self) -> Dict[str, bool]:
        return normalize_action_flags(self.effective_flags)

    def eligibility(self) -> Dict[str, Dict[str, Any]]:
        return {
            'retry': self.retry.as_dict(),
            'confirm': self.confirm.as_dict(),
            'followup': self.followup.as_dict(),
            'precision': self.precision.as_dict(),
        }

    def blocking_factors(self) -> Dict[str, List[str]]:
        return {
            key: list(value.get('blockers') or [])
            for key, value in self.eligibility().items()
            if list(value.get('blockers') or [])
        }

    def as_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        requested_action = str(self.requested_action or self.selected_primary_action or '')
        requested_reason = str(self.requested_reason or self.selection_reason or '')
        canonical_flags = self.action_flags()
        out["action_flags"] = canonical_flags
        out["intent_flags"] = canonical_flags
        out["action_flags_source"] = 'selected_actions'
        out["intent_flags_source"] = 'selected_actions'
        out["eligibility"] = self.eligibility()
        out["blocking_factors"] = self.blocking_factors()
        out["requested_action"] = requested_action
        out["requested_reason"] = requested_reason
        out["selected_primary_action"] = requested_action
        out["selection_reason"] = requested_reason
        out["selected_secondary_action"] = str(self.selected_secondary_action or '')
        out["secondary_selection_reason"] = str(self.secondary_selection_reason or '')
        out["effective_flags"] = self.effective_action_flags()
        out["effective_secondary_action"] = str(self.effective_secondary_action or '')
        out["intent_explain"] = dict(self.explain or {})
        return out
