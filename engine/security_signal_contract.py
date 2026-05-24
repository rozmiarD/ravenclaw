from __future__ import annotations

from typing import Any, Dict


WORKFLOW_PROMOTABLE_STATUSES = {'promotable', 'confirmable'}
FINDING_POSITIVE_STATUSES = {'moderate', 'strong'}
ADAPTATION_POSITIVE_STATUSES = {'positive', 'strong_positive'}


def _safe_str(value: Any) -> str:
    return str(value or '').strip().lower()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def workflow_promotion_status(signal_contract: Dict[str, Any] | None) -> str:
    return _safe_str(_safe_dict(_safe_dict(signal_contract).get('workflow_promotion')).get('status'))


def success_outcome_status(signal_contract: Dict[str, Any] | None) -> str:
    return _safe_str(_safe_dict(_safe_dict(signal_contract).get('success_outcome')).get('status'))


def finding_signal_status(signal_contract: Dict[str, Any] | None) -> str:
    return _safe_str(_safe_dict(_safe_dict(signal_contract).get('finding_signal')).get('status'))


def adaptation_feedback_status(signal_contract: Dict[str, Any] | None) -> str:
    return _safe_str(_safe_dict(_safe_dict(signal_contract).get('adaptation_feedback')).get('status'))


def signal_contract_promising(signal_contract: Dict[str, Any] | None) -> bool:
    return workflow_promotion_status(signal_contract) in WORKFLOW_PROMOTABLE_STATUSES


def signal_contract_workflow_promotable(signal_contract: Dict[str, Any] | None) -> bool:
    return signal_contract_promising(signal_contract)


def signal_contract_signal_positive(signal_contract: Dict[str, Any] | None) -> bool:
    legacy = _safe_dict(_safe_dict(signal_contract).get('legacy_bridges'))
    weak_actionable = bool(legacy.get('weak_actionable_signal', False))
    return finding_signal_status(signal_contract) in FINDING_POSITIVE_STATUSES or signal_contract_promising(signal_contract) or weak_actionable


def signal_contract_host_promise_positive(signal_contract: Dict[str, Any] | None) -> bool:
    host_signal = _safe_str(_safe_dict(_safe_dict(signal_contract).get('adaptation_feedback')).get('host_signal'))
    return host_signal == 'positive'


def signal_contract_adaptation_positive(signal_contract: Dict[str, Any] | None) -> bool:
    return adaptation_feedback_status(signal_contract) in ADAPTATION_POSITIVE_STATUSES


def signal_contract_planner_reconsult_worthy(signal_contract: Dict[str, Any] | None) -> bool:
    return bool(_safe_dict(_safe_dict(signal_contract).get('adaptation_feedback')).get('planner_reconsult_worthy', False))


def build_signal_contract(
    *,
    engine_status: str,
    auditor_decision: str,
    success_eval_status: str,
    qual: Dict[str, Any] | None,
    signal_assessment: Dict[str, Any] | None,
    runtime_decision: Dict[str, Any] | None,
    summary_text: str = '',
    reason_code: str = '',
    control_cmp: Dict[str, Any] | None = None,
    metrics_obj: Dict[str, Any] | None = None,
    success_semantics: Dict[str, Any] | None = None,
    weak_signal_positive_bridge_enabled: bool = True,
) -> Dict[str, Any]:
    qual = _safe_dict(qual)
    signal_assessment = _safe_dict(signal_assessment)
    runtime_decision = _safe_dict(runtime_decision)
    control_cmp = _safe_dict(control_cmp)
    metrics_obj = _safe_dict(metrics_obj)
    success_semantics = _safe_dict(success_semantics)

    engine_l = _safe_str(engine_status)
    auditor_l = _safe_str(auditor_decision)
    success_l = _safe_str(success_eval_status)
    verdict = _safe_str(qual.get('verdict') or 'none')
    threshold = _safe_str(signal_assessment.get('qualification_threshold') or 'probable')
    confidence = _safe_str(qual.get('confidence') or '')
    qualification_disposition = _safe_str(qual.get('disposition') or 'standard')
    requested_action = _safe_str(runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') or '')

    anomaly_status = 'none'
    anomaly_severity = 'none'
    anomaly_blocking = False
    anomaly_source = 'engine'
    anomaly_evidence: list[str] = []
    if auditor_l in {'reject', 'owner_approval_required'} or engine_l == 'blocked':
        anomaly_status = 'policy_block'
        anomaly_severity = 'high'
        anomaly_blocking = True
        anomaly_source = 'policy'
        anomaly_evidence.append(f'auditor:{auditor_l or "blocked"}')
    elif engine_l == 'timeout':
        anomaly_status = 'transport_failure'
        anomaly_severity = 'high'
        anomaly_blocking = True
        anomaly_evidence.append('engine_status:timeout')
    elif engine_l in {'failed', 'error'}:
        anomaly_status = 'tool_failure'
        anomaly_severity = 'high'
        anomaly_blocking = True
        anomaly_evidence.append(f'engine_status:{engine_l}')

    finding_status = 'none'
    finding_source = 'qualification'
    false_positive_risk = 'high'
    finding_evidence: list[str] = []
    if control_cmp.get('control_delta_observed'):
        finding_evidence.append('control_delta_observed')
        finding_source = 'mixed'
    if metrics_obj.get('code') is not None:
        finding_evidence.append(f'http_code:{metrics_obj.get("code")}')
    if reason_code:
        finding_evidence.append(f'reason_code:{str(reason_code)[:64]}')
    if qualification_disposition and qualification_disposition != 'standard':
        finding_evidence.append(f'qualification_disposition:{qualification_disposition}')
    if verdict == 'confirmed':
        finding_status = 'strong'
        false_positive_risk = 'low'
    elif verdict == 'probable':
        finding_status = 'moderate'
        false_positive_risk = 'medium'
    elif verdict == 'weak_signal' or bool(signal_assessment.get('heuristic_promising', False)) or bool(signal_assessment.get('signal_positive', False)):
        finding_status = 'weak'
        false_positive_risk = 'high'
        if finding_source == 'qualification' and bool(signal_assessment.get('heuristic_promising', False)):
            finding_source = 'mixed'

    workflow_status = 'not_promotable'
    workflow_reasons: list[str] = []
    if bool(signal_assessment.get('workflow_promotable', False)):
        if verdict in {'probable', 'confirmed'}:
            workflow_status = 'confirmable'
            workflow_reasons.append('qualification_confirmable')
        else:
            workflow_status = 'promotable'
            workflow_reasons.append('qualification_threshold_met')
        if requested_action:
            workflow_reasons.append(f'requested_action:{requested_action}')
    elif finding_status != 'none' or bool(signal_assessment.get('signal_positive', False)):
        workflow_status = 'candidate'
        workflow_reasons.append('signal_without_promotion')
    else:
        workflow_reasons.append('no_promotable_signal')
    if verdict:
        workflow_reasons.append(f'verdict:{verdict}')
    if threshold:
        workflow_reasons.append(f'threshold:{threshold}')

    success_evidence: list[str] = []
    if success_l and success_l != 'not_provided':
        success_evidence.append(f'success_eval:{success_l}')
    if confidence:
        success_evidence.append(f'qualification_confidence:{confidence}')

    weak_actionable_signal = bool(
        weak_signal_positive_bridge_enabled
        and finding_status == 'weak'
        and auditor_l == 'approve'
        and engine_l not in {'failed', 'error', 'timeout'}
        and success_l in {'partial', 'met'}
        and not anomaly_blocking
    )

    host_signal = 'positive' if bool(signal_assessment.get('host_promise_positive', False)) else 'neutral'
    adaptation_status = 'neutral'
    planner_reconsult_worthy = False
    plan_regen_pressure = 'none'
    adaptation_reasons: list[str] = []
    if workflow_status == 'confirmable':
        adaptation_status = 'strong_positive'
        planner_reconsult_worthy = True
        plan_regen_pressure = 'light'
        adaptation_reasons.append('confirmable_workflow_signal')
    elif bool(signal_assessment.get('adaptation_positive', False)) and workflow_status in {'promotable', 'candidate'}:
        adaptation_status = 'positive'
        planner_reconsult_worthy = True
        adaptation_reasons.append('adaptation_positive_signal')
        if success_l in {'partial', 'not_met'}:
            plan_regen_pressure = 'light'
    elif weak_actionable_signal and workflow_status == 'candidate':
        adaptation_status = 'positive'
        planner_reconsult_worthy = True
        plan_regen_pressure = 'light'
        adaptation_reasons.append('weak_actionable_signal_bridge')
    elif success_l == 'not_met':
        adaptation_status = 'negative'
        adaptation_reasons.append('success_not_met')
    elif success_l == 'partial':
        adaptation_reasons.append('partial_success_signal')
    if bool(signal_assessment.get('workflow_promotable', False)):
        adaptation_reasons.append('workflow_promotable')
    if summary_text:
        adaptation_reasons.append(f'summary:{str(summary_text)[:80]}')

    evidence_class = 'none'
    if finding_status != 'none':
        if qualification_disposition == 'governance_blocked':
            evidence_class = 'blocked_evidence'
        else:
            evidence_class = 'evidence_bearing'

    signal_contract = {
        'schema_version': 'p5-v1',
        'execution_anomaly': {
            'status': anomaly_status,
            'severity': anomaly_severity,
            'blocking': anomaly_blocking,
            'evidence': anomaly_evidence,
            'source': anomaly_source,
        },
        'finding_signal': {
            'status': finding_status,
            'evidence_bearing': finding_status != 'none',
            'evidence_class': evidence_class,
            'source': finding_source,
            'evidence': finding_evidence[:6],
            'false_positive_risk': false_positive_risk,
        },
        'success_outcome': {
            'status': success_l or 'not_provided',
            'scope': 'task',
            'evidence': (list(success_semantics.get('success_evidence') or [])[:6] or success_evidence[:6]),
            'gap': str(success_semantics.get('success_gap') or ('' if success_l in {'met', 'partial'} else ('missing_success_criteria' if success_l == 'not_provided' else 'needs_stronger_evidence'))),
            'typed_family_eval': str(success_semantics.get('typed_family_eval') or 'generic'),
            'success_model': str(success_semantics.get('success_model') or ''),
            'expected_signal_type': str(success_semantics.get('expected_signal_type') or ''),
            'evidence_goal_type': str(success_semantics.get('evidence_goal_type') or ''),
            'acceptance_checks_eval': list(success_semantics.get('acceptance_checks_eval') or [])[:6],
            'evidence_required_eval': list(success_semantics.get('evidence_required_eval') or [])[:6],
            'required_evidence_hits': list(success_semantics.get('required_evidence_hits') or [])[:6],
        },
        'workflow_promotion': {
            'status': workflow_status,
            'source': 'qualification',
            'threshold': threshold or 'probable',
            'verdict': verdict or 'none',
            'qualification_disposition': qualification_disposition or 'standard',
            'reasons': workflow_reasons[:6],
        },
        'adaptation_feedback': {
            'status': adaptation_status,
            'planner_reconsult_worthy': planner_reconsult_worthy,
            'plan_regeneration_pressure': plan_regen_pressure,
            'host_signal': host_signal,
            'reasons': adaptation_reasons[:6],
        },
    }
    high_signal = bool(
        finding_status in FINDING_POSITIVE_STATUSES
        or signal_contract_promising(signal_contract)
        or signal_contract['execution_anomaly']['status'] != 'none'
    )
    signal_positive = bool(
        finding_status in FINDING_POSITIVE_STATUSES
        or signal_contract_promising(signal_contract)
        or weak_actionable_signal
    )
    metrics_code = _safe_int(metrics_obj.get('code'))
    signal_contract['legacy_bridges'] = {
        'promising': signal_contract_promising(signal_contract),
        'high_signal': high_signal,
        'interesting_http_signal': bool(metrics_code is not None and metrics_code >= 400),
        'weak_actionable_signal': weak_actionable_signal,
        'signal_positive': signal_positive,
        'workflow_promotable': signal_contract_workflow_promotable(signal_contract),
        'adaptation_positive': signal_contract_adaptation_positive(signal_contract),
        'host_promise_positive': signal_contract_host_promise_positive(signal_contract),
    }
    return signal_contract
