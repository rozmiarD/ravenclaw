from __future__ import annotations

from typing import Any, Dict

import vuln_qualification as vq  # type: ignore
from auto_campaign_health import is_promising  # type: ignore


def compute_signal_assessment(
    qual: Dict[str, Any],
    summary_text: str,
    classification: str,
    qualification_mode: str,
    qualification_promising_threshold: str,
    *,
    shadow_workflow_bridge_enabled: bool = True,
) -> Dict[str, Any]:
    qualification_promising = vq.verdict_at_least(qual.get('verdict', 'none'), qualification_promising_threshold)
    heuristic_promising = is_promising(summary_text, classification)
    mode = str(qualification_mode or 'shadow').strip().lower()
    if mode not in {'shadow', 'enforce'}:
        mode = 'shadow'
    # Canonical truth stays qualification-driven. Shadow mode may still expose a bounded
    # workflow/adaptation bridge for guard-passing heuristic signals without redefining
    # the underlying qualification verdict itself.
    canonical_promising = bool(qualification_promising)
    guards_passed = bool(qual.get('false_positive_guards_passed', True))
    shadow_bridge_active = bool(
        shadow_workflow_bridge_enabled
        and mode == 'shadow'
        and not canonical_promising
        and guards_passed
        and heuristic_promising
    )
    source = 'hybrid_shadow' if shadow_bridge_active else 'qualification'
    workflow_promotable = bool(canonical_promising or shadow_bridge_active)
    adaptation_positive = bool(canonical_promising or shadow_bridge_active)
    host_promise_positive = bool(canonical_promising or shadow_bridge_active)
    return {
        'canonical_promising': canonical_promising,
        'qualification_promising': bool(qualification_promising),
        'heuristic_promising': bool(heuristic_promising),
        'signal_positive': bool(qualification_promising or heuristic_promising),
        'workflow_promotable': workflow_promotable,
        'adaptation_positive': adaptation_positive,
        'host_promise_positive': host_promise_positive,
        'shadow_bridge_active': shadow_bridge_active,
        'qualification_mode': mode,
        'qualification_threshold': str(qualification_promising_threshold or 'probable'),
        'source': source,
    }


def compute_promising(
    qual: Dict[str, Any],
    summary_text: str,
    classification: str,
    qualification_mode: str,
    qualification_promising_threshold: str,
) -> bool:
    assessment = compute_signal_assessment(
        qual,
        summary_text,
        classification,
        qualification_mode,
        qualification_promising_threshold,
    )
    return bool(assessment['canonical_promising'])


def finding_lifecycle(mode: str, qual: Dict[str, Any]) -> str:
    verdict = str(qual.get('verdict') or '')
    if str(mode) == 'confirm':
        return 'confirm_running'
    if verdict == 'confirmed':
        return 'confirmed'
    if verdict == 'probable':
        return 'probable'
    return 'signal'
