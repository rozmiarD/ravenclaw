from __future__ import annotations

from typing import Any, Callable, Dict


def quality_aware_followup_admission_hint(
    task: Dict[str, Any],
    result: Dict[str, Any] | None,
    runtime_decision: Dict[str, Any] | None,
    *,
    adaptive_quality_context_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    out = {'suppress_followup': False, 'force_high_priority': False, 'reason': ''}
    task_family = str((task or {}).get('task_family') or '').strip().lower()
    if not isinstance(result, dict):
        return out
    feedback = result.get('planner_feedback') if isinstance(result.get('planner_feedback'), dict) else {}
    if not feedback and isinstance(result.get('result_context'), dict):
        feedback = result['result_context'].get('planner_feedback') if isinstance(result['result_context'].get('planner_feedback'), dict) else {}
    quality = adaptive_quality_context_fn(feedback)
    exploitish = task_family in {'authz', 'idor', 'auth_flow', 'logic', 'workflow', 'state_transition', 'input_tamper'}
    decision = runtime_decision if isinstance(runtime_decision, dict) else {}
    intent_flags = decision.get('intent_flags') if isinstance(decision.get('intent_flags'), dict) else {}
    wants_followup = bool(intent_flags.get('followup', False))
    wants_confirm = bool(intent_flags.get('confirm', False))
    if float(quality.get('dead_end_pressure_recent', 0.0) or 0.0) >= 0.7 and exploitish and wants_followup and not wants_confirm:
        out['suppress_followup'] = True
        out['reason'] = 'dead_end_pressure'
        return out
    if bool(quality.get('quality_strong', False)) and exploitish and (wants_followup or wants_confirm):
        out['force_high_priority'] = True
        out['reason'] = 'quality_strength'
    return out


def apply_post_run_admission_hint(
    runtime_decision: Dict[str, Any] | None,
    admission_hint: Dict[str, Any] | None,
) -> Dict[str, Any]:
    runtime_decision_local = dict(runtime_decision or {}) if isinstance(runtime_decision, dict) else {}
    hint = admission_hint if isinstance(admission_hint, dict) else {}
    if hint.get('suppress_followup'):
        intent_flags = dict(runtime_decision_local.get('intent_flags') or {}) if isinstance(runtime_decision_local.get('intent_flags'), dict) else {}
        intent_flags['followup'] = False
        runtime_decision_local['intent_flags'] = intent_flags
    if hint.get('force_high_priority'):
        runtime_decision_local['high_priority'] = True
    return runtime_decision_local
