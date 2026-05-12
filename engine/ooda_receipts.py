from __future__ import annotations

"""Public-safe OODA control-decision projection helpers.

Ravenclaw owns where runtime receipts/evidence are persisted. GovEngine owns the
OODA decision contract. This module is the thin host-side projection layer that
turns GovEngine decision objects/dicts into compact public-safe receipt fields.
"""

from collections.abc import Mapping
from typing import Any

from sclite.redaction import sanitize_public_artifact

_ORIENTATION_KEYS = (
    'scope_ok',
    'policy_ok',
    'ticket_ok',
    'spec_ok',
    'host_health',
    'output_shape',
    'operator_control',
    'budget_state',
)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _safe_string(value: Any) -> str:
    sanitized = sanitize_public_artifact(str(value or ''))
    return str(sanitized or '')


def _step_index(observations: list[Any]) -> int | None:
    for observation in observations:
        obs = _mapping(observation)
        facts = _mapping(obs.get('facts'))
        raw = facts.get('step_index')
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str) and raw.isdigit():
            return int(raw)
    return None


def compact_ooda_control_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact public-safe OODA control-decision summary.

    The input may be a GovEngine ``GovOodaDecision.as_dict()`` payload or an
    already compact host summary. Raw observation details, facts, and telemetry
    are deliberately dropped.
    """

    raw = _mapping(decision)
    observations = _list(raw.get('observations'))
    orientation = _mapping(raw.get('orientation') or raw.get('orientation_summary'))
    summary: dict[str, Any] = {
        'decision': _safe_string(raw.get('decision')),
        'reason_code': _safe_string(raw.get('reason_code')),
        'interrupting': bool(raw.get('interrupting', False)),
        'observation_kinds': [_safe_string(_mapping(item).get('kind')) for item in observations if _mapping(item).get('kind')],
        'observation_severities': [_safe_string(_mapping(item).get('severity')) for item in observations if _mapping(item).get('severity')],
        'orientation_summary': {key: sanitize_public_artifact(orientation.get(key)) for key in _ORIENTATION_KEYS if key in orientation},
    }
    step_index = raw.get('step_index') if isinstance(raw.get('step_index'), int) else _step_index(observations)
    if step_index is not None:
        summary['step_index'] = step_index
    cooldown_subject = raw.get('cooldown_subject')
    if cooldown_subject:
        summary['cooldown_subject'] = _safe_string(cooldown_subject)
    return sanitize_public_artifact(summary)


def compact_ooda_control_decisions(pipeline_data: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract compact OODA summaries from known Ravenclaw/GovEngine receipt slots."""

    raw = _mapping(pipeline_data)
    engine = _mapping(raw.get('engine'))
    runner_receipt = _mapping(raw.get('runner_receipt'))
    candidates = (
        engine.get('control_decisions'),
        raw.get('control_decisions'),
        runner_receipt.get('control_decisions'),
    )
    for candidate in candidates:
        if isinstance(candidate, list | tuple):
            return [compact_ooda_control_decision(_mapping(item)) for item in candidate if isinstance(item, Mapping)]
    return []


def add_ooda_to_execution_receipt(receipt: Mapping[str, Any], pipeline_data: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(receipt)
    decisions = compact_ooda_control_decisions(pipeline_data)
    if decisions:
        out['control_decisions'] = decisions
        out['control_decision_count'] = len(decisions)
    return sanitize_public_artifact(out)


def add_ooda_to_evidence_bundle(bundle: Mapping[str, Any], pipeline_data: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(bundle)
    decisions = compact_ooda_control_decisions(pipeline_data)
    if not decisions:
        return sanitize_public_artifact(out)
    out['governance_evidence'] = {
        'ooda_control_evaluated': True,
        'control_decision_count': len(decisions),
        'interrupting_decision_count': sum(1 for decision in decisions if decision.get('interrupting') is True),
        'control_decisions': decisions,
        'source': 'execution_receipt.json',
        'non_claim': 'OODA control decisions are governance evidence, not live vulnerability evidence.',
    }
    return sanitize_public_artifact(out)


def append_ooda_to_evidence_summary(markdown: str, pipeline_data: Mapping[str, Any]) -> str:
    decisions = compact_ooda_control_decisions(pipeline_data)
    if not decisions:
        return markdown
    lines = [markdown.rstrip(), '', '## OODA control decisions', '']
    for decision in decisions:
        step = decision.get('step_index', 'n/a')
        lines.append(
            f"- `{decision.get('decision', '')}` — {decision.get('reason_code', '')}; "
            f"interrupting: `{bool(decision.get('interrupting', False))}`; step: `{step}`."
        )
    lines.extend([
        '',
        'These entries are governance/control evidence only. They do not include raw telemetry and do not claim live vulnerability evidence.',
    ])
    return '\n'.join(lines) + '\n'
