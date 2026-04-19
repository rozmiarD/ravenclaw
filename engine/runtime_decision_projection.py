from __future__ import annotations

from typing import Any, Dict

from runtime_decision_contracts import canonical_action_flags_from_mapping  # type: ignore


def project_runtime_decision_to_run_info(
    *,
    run_info: Dict[str, Any],
    effective_decision: Dict[str, Any] | None,
) -> Dict[str, Any]:
    effective_decision = effective_decision if isinstance(effective_decision, dict) else {}
    runtime_decision = dict(run_info.get('runtime_decision') or {}) if isinstance(run_info.get('runtime_decision'), dict) else {}
    intent_flags, intent_flags_source = canonical_action_flags_from_mapping(
        runtime_decision,
        fallback=run_info.get('decision_intent_flags') or runtime_decision.get('action_flags') or {},
    )
    effective_flags = dict(effective_decision.get('effective_flags') or {})
    effective_reasons = dict(effective_decision.get('effective_reasons') or {})
    effective_blockers = dict(effective_decision.get('effective_blockers') or {})
    effective_status = str(effective_decision.get('effective_status') or 'noop')
    effective_summary = str(effective_decision.get('effective_summary') or '')

    runtime_decision['intent_flags'] = dict(intent_flags)
    runtime_decision['action_flags'] = dict(intent_flags)
    runtime_decision['intent_flags_source'] = str(runtime_decision.get('intent_flags_source') or intent_flags_source)
    runtime_decision['action_flags_source'] = str(runtime_decision.get('action_flags_source') or intent_flags_source)
    runtime_decision['eligibility'] = dict(runtime_decision.get('eligibility') or run_info.get('decision_eligibility') or {})
    runtime_decision['requested_action'] = str(runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') or run_info.get('decision_selected_action') or '')
    runtime_decision['requested_reason'] = str(runtime_decision.get('requested_reason') or runtime_decision.get('selection_reason') or run_info.get('decision_selection_reason') or '')
    runtime_decision['selected_primary_action'] = str(runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') or run_info.get('decision_selected_action') or '')
    runtime_decision['selection_reason'] = str(runtime_decision.get('requested_reason') or runtime_decision.get('selection_reason') or run_info.get('decision_selection_reason') or '')
    runtime_decision['selected_secondary_action'] = str(runtime_decision.get('selected_secondary_action') or run_info.get('decision_selected_secondary_action') or '')
    runtime_decision['secondary_selection_reason'] = str(runtime_decision.get('secondary_selection_reason') or run_info.get('decision_secondary_selection_reason') or '')
    runtime_decision['effective_status'] = effective_status
    runtime_decision['effective_action'] = str(effective_decision.get('effective_action') or '')
    runtime_decision['effective_secondary_action'] = str(effective_decision.get('effective_secondary_action') or runtime_decision.get('effective_secondary_action') or run_info.get('decision_effective_secondary_action') or '')
    runtime_decision['effective_flags'] = effective_flags
    runtime_decision['effective_reasons'] = effective_reasons
    runtime_decision['effective_blockers'] = effective_blockers
    runtime_decision['effective_summary'] = effective_summary

    run_info['runtime_decision'] = runtime_decision
    run_info['decision_intent_flags'] = dict(intent_flags)
    run_info['decision_eligibility'] = dict(runtime_decision.get('eligibility') or {})
    run_info['decision_requested_action'] = str(runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') or '')
    run_info['decision_requested_reason'] = str(runtime_decision.get('requested_reason') or runtime_decision.get('selection_reason') or '')
    run_info['decision_selected_action'] = str(runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') or '')
    run_info['decision_selection_reason'] = str(runtime_decision.get('requested_reason') or runtime_decision.get('selection_reason') or '')
    run_info['decision_selected_secondary_action'] = str(runtime_decision.get('selected_secondary_action') or '')
    run_info['decision_secondary_selection_reason'] = str(runtime_decision.get('secondary_selection_reason') or '')
    run_info['decision_flags'] = effective_flags
    run_info['decision_effective_flags'] = effective_flags
    run_info['decision_effective_status'] = effective_status
    run_info['decision_effective_action'] = str(runtime_decision.get('effective_action') or '')
    run_info['decision_effective_secondary_action'] = str(runtime_decision.get('effective_secondary_action') or '')
    run_info['decision_effective_reasons'] = effective_reasons
    run_info['decision_effective_blockers'] = effective_blockers
    run_info['decision_effective_summary'] = effective_summary
    if isinstance(run_info.get('decision_explain'), dict):
        run_info['decision_explain']['effective_summary'] = effective_summary
        run_info['decision_explain']['requested_reason'] = runtime_decision['requested_reason']
        run_info['decision_explain']['requested_action'] = runtime_decision['requested_action']
        run_info['decision_explain']['selected_primary_action'] = runtime_decision['selected_primary_action']
        run_info['decision_explain']['selected_secondary_action'] = runtime_decision['selected_secondary_action']
        run_info['decision_explain']['effective_action'] = runtime_decision['effective_action']
        run_info['decision_explain']['effective_secondary_action'] = runtime_decision['effective_secondary_action']
    return run_info
