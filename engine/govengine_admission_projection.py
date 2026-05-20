from __future__ import annotations

from dataclasses import asdict, is_dataclass
from hashlib import sha256
from typing import Any, Mapping

from govengine.admission import (
    validate_admission_decision,
    validate_approval_request,
    validate_audit_record,
    validate_policy_decision,
)


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, 'as_dict') and callable(value.as_dict):
        try:
            out = value.as_dict()
            return dict(out) if isinstance(out, Mapping) else {}
        except Exception:
            return {}
    return {}


def _text(value: Any, default: str = '') -> str:
    out = str(value if value is not None else '').strip()
    return out if out else default


def _tuple(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        return (values,)
    try:
        return tuple(str(value) for value in values)
    except Exception:
        return ()


def _subject_ref(value: Any) -> tuple[str, bool]:
    raw = _text(value)
    if not raw:
        return 'sha256:' + sha256(b'ravenclaw-admission').hexdigest()[:24], False
    return 'sha256:' + sha256(raw.encode('utf-8')).hexdigest()[:24], True


def _redact_detail(detail: Any, *raw_values: Any) -> str:
    out = _text(detail)
    for value in raw_values:
        raw = _text(value)
        if raw:
            out = out.replace(raw, '[redacted]')
    return out


def _context_from_gate(data: Mapping[str, Any]) -> dict[str, Any]:
    context = _mapping(data.get('context'))
    for key in (
        'activation_phase',
        'activation_mode',
        'conditional_gate',
        'surface_role',
        'expected_depth',
        'state_band',
    ):
        if key in data and key not in context:
            context[key] = data.get(key)
    cluster = _text(data.get('target_cluster') or context.pop('target_cluster', ''))
    if cluster and cluster != 'general':
        context['target_cluster_ref'] = _subject_ref(cluster)[0]
        context['target_cluster_redacted'] = True
    elif cluster:
        context['target_cluster'] = 'general'
    return context


def _signal_from_gate(data: Mapping[str, Any]) -> dict[str, Any]:
    signal = _mapping(data.get('signal'))
    if 'cooldown_until' in data and data.get('cooldown_until') is not None:
        signal['cooldown_until_present'] = True
    return signal


def build_gov_admission_decision_projection(
    value: Any,
    *,
    subject: Any = '',
    decision_id: str = '',
) -> dict[str, Any]:
    """Project Ravenclaw runtime gate output into GovEngine 0.5 shape.

    Ravenclaw owns the admission policy. GovEngine receives only a redacted,
    neutral decision record for validation and downstream audit surfaces.
    """

    data = _mapping(value)
    raw_subject = subject or data.get('host') or data.get('target') or data.get('subject_ref') or data.get('family') or 'ravenclaw-task'
    subject_ref, redacted = _subject_ref(raw_subject)
    allowed = bool(data.get('allowed', False))
    reason = _text(data.get('reason_code'), 'allowed' if allowed else 'blocked')
    detail = _redact_detail(data.get('detail'), data.get('host'), data.get('target'), raw_subject)
    decision = validate_admission_decision({
        'decision_id': decision_id or f'{subject_ref}:{reason}',
        'subject_ref': subject_ref,
        'subject_kind': 'task',
        'outcome': 'allowed' if allowed else 'denied',
        'allowed': allowed,
        'reason_code': reason,
        'detail': detail,
        'blockers': list(_tuple(data.get('blockers') or ())),
        'context': _context_from_gate(data),
        'signal': _signal_from_gate(data),
        'explainability': _mapping(data.get('explainability')),
        'metadata': {
            'source': 'ravenclaw_admission_projection',
            'projection_kind': data.get('__projection_kind') or value.__class__.__name__,
            'subject_redacted': redacted,
        },
    })
    return decision.as_dict()


def build_gov_policy_decision_projection(value: Any, *, subject: Any = '', policy_id: str = '') -> dict[str, Any]:
    data = _mapping(value)
    raw_subject = subject or data.get('host') or data.get('target') or data.get('subject_ref') or data.get('family') or 'ravenclaw-task'
    subject_ref, redacted = _subject_ref(raw_subject)
    allowed = bool(data.get('allowed', False))
    reason = _text(data.get('reason_code'), 'allowed' if allowed else 'blocked')
    policy = validate_policy_decision({
        'policy_id': policy_id or f'{subject_ref}:policy:{reason}',
        'subject_ref': subject_ref,
        'subject_kind': 'task',
        'decision': 'allow' if allowed else 'deny',
        'reason_code': reason,
        'controls': ['ravenclaw_runtime_admission_policy'],
        'blockers': list(_tuple(data.get('blockers') or ())),
        'metadata': {
            'source': 'ravenclaw_admission_projection',
            'subject_redacted': redacted,
        },
    })
    return policy.as_dict()


def build_gov_approval_request_projection(
    *,
    subject: Any,
    request_id: str,
    policy_refs: Any = (),
    state: str = 'requested',
    reason_code: str = 'operator_approval_required',
) -> dict[str, Any]:
    subject_ref, redacted = _subject_ref(subject)
    approval = validate_approval_request({
        'request_id': request_id,
        'subject_ref': subject_ref,
        'subject_kind': 'task',
        'state': state,
        'reason_code': reason_code,
        'policy_refs': list(_tuple(policy_refs)),
        'metadata': {
            'source': 'ravenclaw_admission_projection',
            'subject_redacted': redacted,
            'workflow_owner': 'ravenclaw',
        },
    })
    return approval.as_dict()


def build_gov_audit_record_projection(value: Any, *, subject: Any = '', record_id: str = '', decision_ref: str = '') -> dict[str, Any]:
    data = _mapping(value)
    raw_subject = subject or data.get('host') or data.get('target') or data.get('subject_ref') or data.get('family') or 'ravenclaw-task'
    subject_ref, redacted = _subject_ref(raw_subject)
    reason = _text(data.get('reason_code'), 'recorded')
    audit = validate_audit_record({
        'record_id': record_id or f'{subject_ref}:audit:{reason}',
        'record_type': 'admission_decision',
        'subject_ref': subject_ref,
        'subject_kind': 'task',
        'decision_ref': decision_ref or _text(data.get('decision_id')),
        'reason_code': reason,
        'metadata': {
            'source': 'ravenclaw_admission_projection',
            'subject_redacted': redacted,
            'storage_owner': 'ravenclaw',
        },
    })
    return audit.as_dict()


def build_gov_admission_bundle_projection(value: Any, *, subject: Any = '') -> dict[str, Any]:
    admission = build_gov_admission_decision_projection(value, subject=subject)
    policy = build_gov_policy_decision_projection(value, subject=subject)
    audit = build_gov_audit_record_projection(value, subject=subject, decision_ref=admission['decision_id'])
    return {
        'artifact_type': 'ravenclaw_govengine_admission_projection',
        'profile': 'ravenclaw-security',
        'admission_decision': admission,
        'policy_decision': policy,
        'audit_record': audit,
        'non_claims': [
            'ravenclaw_owns_security_admission_policy',
            'does_not_expose_raw_target_to_govengine',
            'does_not_grant_execution_authority',
        ],
    }
