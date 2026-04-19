from __future__ import annotations

from typing import Any, Dict


FAMILY_ACTION_BIAS = {
    'authz': {
        'differential_probe': 0.04,
        'confirmatory_probe': 0.03,
        'state_transition_probe': 0.12,
        'variant_probe': 0.02,
    },
    'idor': {
        'differential_probe': 0.04,
        'confirmatory_probe': 0.03,
        'state_transition_probe': 0.1,
    },
    'logic': {
        'differential_probe': 0.05,
        'state_transition_probe': 0.1,
        'confirmatory_probe': 0.04,
    },
    'workflow': {
        'differential_probe': 0.04,
        'state_transition_probe': 0.1,
    },
    'input_tamper': {
        'differential_probe': 0.03,
        'variant_probe': 0.06,
    },
    'recon': {
        'enumeration_probe': 0.03,
        'fingerprint_probe': 0.04,
        'state_transition_probe': -0.04,
    },
}


def compute_runtime_utility(*, action_type: str, decision_quality: dict | None, economics: dict | None, promising: bool, host_state_band: str = '', task_family: str = '', contamination: dict | None = None) -> Dict[str, float]:
    dq = decision_quality if isinstance(decision_quality, dict) else {}
    eco = economics if isinstance(economics, dict) else {}
    information_gain = float(dq.get('information_gain_score', 0.0) or 0.0)
    novelty_gain = float(dq.get('novelty_gain_score', 0.0) or 0.0)
    reproducibility_score = float(dq.get('reproducibility_score', 0.0) or 0.0)
    false_positive_risk_penalty = float(dq.get('false_positive_risk_penalty', 0.0) or 0.0)
    base_priority = float(eco.get('priority_score', 0.0) or 0.0)
    band = str(host_state_band or '').lower()
    family = str(task_family or '').strip().lower()
    noise_penalty = 0.12 if band in {'degraded', 'noisy'} else 0.0
    action_bias = {
        'single_probe': 0.0,
        'differential_probe': 0.08,
        'confirmatory_probe': 0.05,
        'enumeration_probe': 0.02,
        'variant_probe': -0.03,
        'fingerprint_probe': 0.01,
        'state_transition_probe': -0.05,
    }.get(str(action_type or 'single_probe'), 0.0)
    family_action_bias = float((FAMILY_ACTION_BIAS.get(family) or {}).get(str(action_type or 'single_probe'), 0.0) or 0.0)
    contamination_obj = contamination if isinstance(contamination, dict) else {}
    contamination_score = float(contamination_obj.get('score', 0.0) or 0.0)
    contamination_penalty = round(contamination_score * 0.45, 3)
    exploitation_bonus = 0.0
    if band == 'exploitation':
        exploitation_bonus += 0.08
        if family in {'authz', 'idor', 'logic', 'workflow', 'input_tamper'} and str(action_type or '') in {'differential_probe', 'state_transition_probe', 'confirmatory_probe', 'variant_probe'}:
            exploitation_bonus += 0.05
    signed_adjustment = float(dq.get('redundancy_adjustment', 0.0) or 0.0)
    redundancy_penalty = float(dq.get('redundancy_penalty', 0.0) or 0.0)
    redundancy_bonus = float(dq.get('redundancy_bonus', 0.0) or 0.0)
    if 'redundancy_adjustment' not in dq and 'redundancy_bonus' not in dq and 'redundancy_penalty' in dq:
        legacy = float(dq.get('redundancy_penalty', 0.0) or 0.0)
        redundancy_penalty = abs(min(0.0, legacy))
        redundancy_bonus = max(0.0, legacy)
        signed_adjustment = legacy
    expected_value = round(
        base_priority
        + information_gain
        + novelty_gain
        + reproducibility_score
        + action_bias
        + family_action_bias
        + exploitation_bonus
        + (0.06 if promising else 0.0)
        - contamination_penalty
        - noise_penalty
        - redundancy_penalty
        + redundancy_bonus
        - false_positive_risk_penalty,
        3,
    )
    return {
        'expected_value_score': expected_value,
        'base_priority_score': round(base_priority, 3),
        'information_gain_score': round(information_gain, 3),
        'novelty_gain_score': round(novelty_gain, 3),
        'reproducibility_score': round(reproducibility_score, 3),
        'false_positive_risk_penalty': round(false_positive_risk_penalty, 3),
        'noise_penalty': round(noise_penalty, 3),
        'redundancy_penalty': round(redundancy_penalty, 3),
        'redundancy_bonus': round(redundancy_bonus, 3),
        'redundancy_adjustment': round(signed_adjustment, 3),
        'action_bias': round(action_bias, 3),
        'family_action_bias': round(family_action_bias, 3),
        'exploitation_bonus': round(exploitation_bonus, 3),
        'contamination_penalty': contamination_penalty,
        'contamination_status': str(contamination_obj.get('status') or 'clean'),
        'contamination_score': round(contamination_score, 3),
        'learning_excluded': bool(contamination_obj.get('learning_excluded', False)),
        'net_utility_score': expected_value,
    }
