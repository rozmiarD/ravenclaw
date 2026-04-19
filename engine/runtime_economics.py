from __future__ import annotations

from typing import Any, Dict


ENGINE_FAILURE_COST = {
    'failed': 0.7,
    'error': 0.75,
    'timeout': 0.8,
    'blocked': 0.6,
    'ok': 0.2,
    'success': 0.2,
}

MODE_COST = {
    'fast': 0.2,
    'followup': 0.4,
    'deep': 0.6,
    'confirm': 0.7,
}

VERDICT_VALUE = {
    'none': 0.0,
    'weak_signal': 0.25,
    'probable': 0.65,
    'confirmed': 0.9,
}


def compute_runtime_economics(
    *,
    verdict: str,
    confidence: float,
    engine_status: str,
    success_eval_status: str,
    mode: str,
    blocked: bool,
) -> Dict[str, float]:
    verdict_l = str(verdict or 'none').strip().lower()
    engine_l = str(engine_status or 'unknown').strip().lower()
    success_l = str(success_eval_status or '').strip().lower()
    mode_l = str(mode or '').strip().lower()

    cost_weight = MODE_COST.get(mode_l, 0.3) + ENGINE_FAILURE_COST.get(engine_l, 0.35)
    if blocked:
        cost_weight += 0.15
    if success_l not in {'partial', 'met'}:
        cost_weight += 0.05
    cost_weight = round(min(1.5, max(0.0, cost_weight)), 3)

    value_estimate = VERDICT_VALUE.get(verdict_l, 0.0) + min(1.0, max(0.0, float(confidence))) * 0.35
    if success_l == 'met':
        value_estimate += 0.15
    elif success_l == 'partial':
        value_estimate += 0.08
    if blocked:
        value_estimate -= 0.1
    value_estimate = round(min(1.5, max(0.0, value_estimate)), 3)

    priority_score = round(value_estimate - cost_weight, 3)
    return {
        'cost_weight': cost_weight,
        'value_estimate': value_estimate,
        'priority_score': priority_score,
    }
