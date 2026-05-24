from __future__ import annotations

from typing import Any, Dict


BOUNDED_STRATEGIES = {
    'enumeration_lowering',
    'confirmatory_lowering',
    'variant_lowering',
    'state_transition_lowering',
}

NONE_STRATEGIES = {
    'passthrough',
    'differential_lowering',
}


def _safe_str(value: Any) -> str:
    return str(value or '').strip().lower()


def classify_semantic_loss(compiled_action: Dict[str, Any] | None, *, task_family: str = '') -> Dict[str, Any]:
    compiled = compiled_action if isinstance(compiled_action, dict) else {}
    strategy = _safe_str(compiled.get('compiler_strategy'))
    reason = _safe_str(compiled.get('normalization_reason'))
    action_type = _safe_str(compiled.get('action_type'))
    family = _safe_str(task_family or compiled.get('task_family'))
    detected = bool(compiled.get('semantic_loss_detected', False))

    policy = {
        'loss_class': 'none',
        'severity': 'none',
        'policy_response': 'proceed',
        'approved_under_degradation': False,
        'operator_visibility': 'none',
        'reason_code': 'semantic_loss_none',
        'normalization_reason': reason,
    }

    if not detected and strategy in NONE_STRATEGIES:
        if strategy == 'passthrough' and reason.startswith('recipe:'):
            policy.update({
                'loss_class': 'harmless_normalization',
                'severity': 'low',
                'policy_response': 'proceed',
                'operator_visibility': 'compact',
                'reason_code': 'semantic_loss_harmless_normalization',
            })
        return policy

    if not detected and strategy in BOUNDED_STRATEGIES:
        policy.update({
            'loss_class': 'bounded_lowering',
            'severity': 'medium',
            'policy_response': 'proceed_mark_degraded',
            'approved_under_degradation': True,
            'operator_visibility': 'compact',
            'reason_code': 'semantic_loss_bounded_lowering',
        })
        if strategy in {'confirmatory_lowering', 'state_transition_lowering'} or family in {'authz', 'auth_flow'}:
            policy.update({
                'policy_response': 'auditor_rereview',
                'operator_visibility': 'prominent',
                'reason_code': 'semantic_loss_bounded_rereview',
            })
        return policy

    if detected and reason == 'fingerprint_probe_lowered_to_single_probe':
        policy.update({
            'loss_class': 'degraded_semantics',
            'severity': 'high',
            'policy_response': 'auditor_rereview',
            'approved_under_degradation': True,
            'operator_visibility': 'prominent',
            'reason_code': 'semantic_loss_fingerprint_lowered',
        })
        return policy

    if detected and reason == 'unknown_action_type_lowered_to_passthrough':
        policy.update({
            'loss_class': 'unacceptable_flattening',
            'severity': 'high',
            'policy_response': 'required_replan',
            'approved_under_degradation': False,
            'operator_visibility': 'prominent',
            'reason_code': 'semantic_loss_unknown_action_flattened',
        })
        return policy

    if detected:
        policy.update({
            'loss_class': 'degraded_semantics',
            'severity': 'high',
            'policy_response': 'auditor_rereview',
            'approved_under_degradation': True,
            'operator_visibility': 'prominent',
            'reason_code': f'semantic_loss_detected:{reason or action_type or "unknown"}',
        })
        return policy

    return policy


def semantic_loss_runtime_gate(policy: Dict[str, Any] | None) -> Dict[str, Any]:
    p = policy if isinstance(policy, dict) else {}
    response = _safe_str(p.get('policy_response'))
    blocked = response in {'required_replan', 'block'}
    return {
        'blocked': blocked,
        'blocked_reason_code': _safe_str(p.get('reason_code') or response or 'semantic_loss_policy_block'),
        'blocked_reason': (
            f'semantic_loss_policy:{response}:{_safe_str(p.get("loss_class"))}'
            if blocked else ''
        ),
        'requires_rereview': response == 'auditor_rereview',
        'degraded_execution': response in {'proceed_mark_degraded', 'auditor_rereview'} or _safe_str(p.get('loss_class')) in {'bounded_lowering', 'degraded_semantics'},
    }


def semantic_loss_penalty(policy: Dict[str, Any] | None) -> float:
    p = policy if isinstance(policy, dict) else {}
    loss_class = _safe_str(p.get('loss_class'))
    severity = _safe_str(p.get('severity'))
    if loss_class == 'unacceptable_flattening':
        return -0.35
    if loss_class == 'degraded_semantics':
        return -0.25
    if loss_class == 'bounded_lowering' or severity == 'medium':
        return -0.12
    if loss_class == 'harmless_normalization' or severity == 'low':
        return -0.03
    return 0.0
