from __future__ import annotations

from typing import Any


def list_preview(values: Any, *, limit: int = 4) -> list[str]:
    out: list[str] = []
    if not isinstance(values, list):
        return out
    for item in values[:limit]:
        text = str(item or '').strip()
        if text:
            out.append(text)
    return out


def flatten_reason_map(value: Any, *, limit: int = 6) -> list[str]:
    out: list[str] = []
    if not isinstance(value, dict):
        return out
    for key, raw in list(value.items())[:limit]:
        if isinstance(raw, list):
            items = [str(x).strip() for x in raw if str(x).strip()]
            if items:
                out.append(f"{key}: {', '.join(items[:3])}")
        else:
            text = str(raw or '').strip()
            if text:
                out.append(f"{key}: {text}")
    return out


def resolve_trace_ladder(*, lineage_summary: dict[str, Any], planning_ladder: dict[str, Any], planner_rationale: dict[str, Any], runtime_task: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    current_stage = str(lineage_summary.get('current_stage') or planning_ladder.get('current_stage') or '-').strip() or '-'
    next_stage = str(lineage_summary.get('next_stage') or planning_ladder.get('next_stage') or '-').strip() or '-'
    recommended_progression = list_preview((planning_ladder.get('recommended_progression') if isinstance(planning_ladder, dict) else []) or runtime_task.get('recommended_progression'))
    target_surface_rationale = list_preview(lineage_summary.get('target_surface_rationale') or planner_rationale.get('target_surface_rationale') or runtime_task.get('target_surface_rationale'))
    sources = {
        'current_stage': 'semantic_lineage_summary' if lineage_summary.get('current_stage') else ('planning_ladder' if planning_ladder.get('current_stage') else 'missing'),
        'next_stage': 'semantic_lineage_summary' if lineage_summary.get('next_stage') else ('planning_ladder' if planning_ladder.get('next_stage') else 'missing'),
        'recommended_progression': 'planning_ladder' if planning_ladder.get('recommended_progression') else ('runtime_task' if runtime_task.get('recommended_progression') else 'missing'),
        'target_surface_rationale': 'semantic_lineage_summary' if lineage_summary.get('target_surface_rationale') else ('planner_rationale' if planner_rationale.get('target_surface_rationale') else ('runtime_task' if runtime_task.get('target_surface_rationale') else 'missing')),
    }
    return {
        'current_stage': current_stage,
        'next_stage': next_stage,
        'recommended_progression': recommended_progression,
        'target_surface_rationale': target_surface_rationale,
    }, sources


def resolve_trace_decision(*, row: dict[str, Any], runtime_decision: dict[str, Any], replay_result: dict[str, Any], runtime_task: dict[str, Any], lineage_summary: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    requested_reason = str(runtime_decision.get('requested_reason') or row.get('decision_requested_reason') or row.get('decision_selection_reason') or '-').strip() or '-'
    requested_action = str(replay_result.get('requested_action') or runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') or row.get('decision_selected_action') or '-').strip() or '-'
    effective_action = str(replay_result.get('effective_action') or runtime_decision.get('effective_action') or row.get('decision_effective_action') or '-').strip() or '-'
    effective_status = str(row.get('decision_effective_status') or runtime_decision.get('effective_status') or '-').strip() or '-'
    effective_summary = str(row.get('decision_effective_summary') or runtime_decision.get('effective_summary') or '-').strip() or '-'
    selected_secondary_action = str(runtime_decision.get('selected_secondary_action') or row.get('decision_selected_secondary_action') or '-').strip() or '-'
    effective_secondary_action = str(runtime_decision.get('effective_secondary_action') or row.get('decision_effective_secondary_action') or '-').strip() or '-'
    reasons = flatten_reason_map(row.get('decision_effective_reasons') if isinstance(row.get('decision_effective_reasons'), dict) else runtime_decision.get('effective_reasons'))
    blockers = flatten_reason_map(row.get('decision_effective_blockers') if isinstance(row.get('decision_effective_blockers'), dict) else runtime_decision.get('effective_blockers'))
    priority_score = ((row.get('decision_economics') or {}).get('priority_score') if isinstance(row.get('decision_economics'), dict) else (runtime_decision.get('economics') or {}).get('priority_score'))
    capability_lane = str(row.get('capability_lane') or runtime_task.get('capability_lane') or '-').strip() or '-'
    action_type = str(lineage_summary.get('action_type') or runtime_task.get('action_type') or '-').strip() or '-'
    capability = str(lineage_summary.get('capability') or runtime_task.get('capability') or '-').strip() or '-'
    sources = {
        'requested_reason': 'runtime_decision' if runtime_decision.get('requested_reason') else ('row' if row.get('decision_requested_reason') or row.get('decision_selection_reason') else 'missing'),
        'requested_action': 'replay' if replay_result.get('requested_action') else ('runtime_decision' if runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') else ('row' if row.get('decision_selected_action') else 'missing')),
        'effective_action': 'replay' if replay_result.get('effective_action') else ('runtime_decision' if runtime_decision.get('effective_action') else ('row' if row.get('decision_effective_action') else 'missing')),
        'effective_status': 'row' if row.get('decision_effective_status') else ('runtime_decision' if runtime_decision.get('effective_status') else 'missing'),
        'effective_summary': 'row' if row.get('decision_effective_summary') else ('runtime_decision' if runtime_decision.get('effective_summary') else 'missing'),
        'reasons': 'row' if isinstance(row.get('decision_effective_reasons'), dict) else ('runtime_decision' if runtime_decision.get('effective_reasons') else 'missing'),
        'blockers': 'row' if isinstance(row.get('decision_effective_blockers'), dict) else ('runtime_decision' if runtime_decision.get('effective_blockers') else 'missing'),
        'priority_score': 'row' if isinstance(row.get('decision_economics'), dict) and (row.get('decision_economics') or {}).get('priority_score') is not None else ('runtime_decision' if isinstance(runtime_decision.get('economics'), dict) and (runtime_decision.get('economics') or {}).get('priority_score') is not None else 'missing'),
        'capability_lane': 'row' if row.get('capability_lane') else ('runtime_task' if runtime_task.get('capability_lane') else 'missing'),
        'action_type': 'semantic_lineage_summary' if lineage_summary.get('action_type') else ('runtime_task' if runtime_task.get('action_type') else 'missing'),
        'capability': 'semantic_lineage_summary' if lineage_summary.get('capability') else ('runtime_task' if runtime_task.get('capability') else 'missing'),
    }
    return {
        'requested_reason': requested_reason,
        'requested_action': requested_action,
        'effective_action': effective_action,
        'effective_status': effective_status,
        'effective_summary': effective_summary,
        'selected_secondary_action': selected_secondary_action,
        'effective_secondary_action': effective_secondary_action,
        'reasons': reasons,
        'blockers': blockers,
        'priority_score': priority_score,
        'capability_lane': capability_lane,
        'action_type': action_type,
        'capability': capability,
    }, sources
