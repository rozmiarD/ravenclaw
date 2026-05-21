from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from auto_campaign_targets import host_from_target  # type: ignore
from runtime_host_model import default_host_state, update_host_state  # type: ignore
from decision_quality import compute_decision_quality, aggregate_campaign_learning  # type: ignore
from runtime_utility import compute_runtime_utility  # type: ignore
from campaign_state_machine import derive_family_state, derive_host_stage  # type: ignore
from runtime_adaptation_engine import build_adaptation_signal  # type: ignore
from govengine_security_helpers import (  # type: ignore
    signal_contract_host_promise_positive,
    signal_contract_signal_positive,
    signal_contract_workflow_promotable,
)


def _derive_run_contamination(run_info: dict) -> dict:
    request_shape = run_info.get('request_shape_hygiene') if isinstance(run_info.get('request_shape_hygiene'), dict) else {}
    status = str(request_shape.get('request_shape_hygiene_status') or '').strip().lower()
    match_status = str(request_shape.get('target_host_match_status') or '').strip().lower()
    auditor_decision = str(run_info.get('auditor_decision') or '').strip().lower()
    reason_code = str(run_info.get('reason_code') or '').strip().lower()
    tags: list[str] = []
    sources: list[str] = []
    score = 0.0
    if status == 'cross_host_mismatch':
        tags.append('request_shape_cross_host_mismatch')
        sources.append('request_shape')
        score += 0.4
    elif status == 'ambiguous':
        tags.append('request_shape_ambiguous')
        sources.append('request_shape')
        score += 0.18
    if auditor_decision in {'owner_approval_required', 'reject', 'blocked'}:
        tags.append(f'auditor_{auditor_decision}')
        if 'policy_gate' not in sources:
            sources.append('policy_gate')
        score += 0.12
    if reason_code == 'policy_gate_block':
        tags.append('policy_gate_block')
        if 'policy_gate' not in sources:
            sources.append('policy_gate')
        score += 0.15
    if reason_code.startswith('owner_approval_required'):
        tags.append('owner_gate_required')
        if 'owner_gate' not in sources:
            sources.append('owner_gate')
        score += 0.12
    score = round(min(0.75, max(0.0, score)), 3)
    contaminated = score > 0.0
    return {
        'status': 'contaminated' if contaminated else 'clean',
        'score': score,
        'tags': tags,
        'sources': sources,
        'learning_excluded': contaminated,
        'yield_excluded': contaminated,
        'request_shape_hygiene_status': status or 'unknown',
        'target_host_match_status': match_status or 'unknown',
    }


def _apply_contamination_to_economics(economics: dict, contamination: dict) -> dict:
    econ = dict(economics or {})
    cont = contamination if isinstance(contamination, dict) else {}
    score = float(cont.get('score', 0.0) or 0.0)
    econ['contamination_status'] = str(cont.get('status') or 'clean')
    econ['contamination_score'] = round(score, 3)
    econ['contamination_tags'] = list(cont.get('tags') or [])
    econ['learning_excluded'] = bool(cont.get('learning_excluded', False))
    econ['yield_excluded'] = bool(cont.get('yield_excluded', False))
    if score <= 0.0:
        return econ
    base_value = float(econ.get('value_estimate', 0.0) or 0.0)
    base_cost = float(econ.get('cost_weight', 0.0) or 0.0)
    econ['base_value_estimate'] = round(base_value, 3)
    econ['base_cost_weight'] = round(base_cost, 3)
    econ['base_priority_score'] = round(float(econ.get('priority_score', 0.0) or 0.0), 3)
    econ['value_estimate'] = round(max(0.0, base_value - (score * 0.25)), 3)
    econ['cost_weight'] = round(min(1.5, base_cost + (score * 0.1)), 3)
    econ['priority_score'] = round(econ['value_estimate'] - econ['cost_weight'], 3)
    return econ


def record_and_persist_run(
    *,
    runs: list[dict],
    history: list[dict],
    run_info: dict,
    host_state: dict,
    last_persist_ts: float,
    record_run_fn: Callable[[list[dict], dict], None],
    persist_live_summary_fn: Callable[[], None],
    update_learning_fn: Callable[[str, str, str, bool, str], Any],
    save_host_state_fn: Callable[[dict], None],
    reprioritize_queues_fn: Callable[[], None],
    attack_family_fn: Callable[[str, str, str], str],
) -> float:
    host = host_from_target(str(run_info.get('target') or ''))
    fam = attack_family_fn(
        str(run_info.get('objective') or ''),
        str(run_info.get('target') or ''),
        str(run_info.get('task_family') or ''),
    )
    signal_contract = run_info.get('signal_contract') if isinstance(run_info.get('signal_contract'), dict) else {}
    run_info['run_contamination'] = _derive_run_contamination(run_info)
    if signal_contract:
        run_info['promising'] = signal_contract_workflow_promotable(signal_contract)
        run_info['workflow_promotable'] = signal_contract_workflow_promotable(signal_contract)
        run_info['host_promise_positive'] = signal_contract_host_promise_positive(signal_contract)
        run_info['signal_positive'] = signal_contract_signal_positive(signal_contract)
    hs_all = host_state.setdefault('hosts', {}) if isinstance(host_state, dict) else {}
    prev = hs_all.get(host) if isinstance(hs_all.get(host), dict) else default_host_state()
    host_update = update_host_state(host=host, family=fam, previous=prev, run_info=run_info)

    run_info['host_state'] = dict(host_update.state)
    run_info['host_update'] = host_update.as_dict()
    run_info['host_state_band'] = str(host_update.current_state_band)
    run_info['host_transition'] = {
        'from_state': str(host_update.previous_state),
        'from_band': str(host_update.previous_state_band),
        'to_state': str(host_update.current_state),
        'to_band': str(host_update.current_state_band),
        'changed': bool(host_update.state_changed),
        'reasons': list(host_update.reasons),
        'deltas': dict(host_update.deltas),
    }
    run_info['host_regeneration_reason'] = str(host_update.regeneration_reason or '')

    workflow_promotable = signal_contract_workflow_promotable(signal_contract) if signal_contract else bool(run_info.get('workflow_promotable', run_info.get('promising', False)))
    host_signal_positive = signal_contract_host_promise_positive(signal_contract) if signal_contract else bool(run_info.get('host_promise_positive', run_info.get('promising', False)))
    finding_signal_positive = signal_contract_signal_positive(signal_contract) if signal_contract else bool(run_info.get('signal_positive', run_info.get('promising', False)))

    run_info['decision_quality'] = compute_decision_quality(run_info)
    run_info['decision_economics'] = _apply_contamination_to_economics(
        run_info.get('decision_economics') if isinstance(run_info.get('decision_economics'), dict) else {},
        run_info.get('run_contamination') if isinstance(run_info.get('run_contamination'), dict) else {},
    )
    family_state = derive_family_state(
        analysis_contract=run_info.get('analysis_contract') if isinstance(run_info.get('analysis_contract'), dict) else {},
        promising=workflow_promotable,
        host_state_band=str(run_info.get('host_state_band') or ''),
    )
    host_stage = derive_host_stage(
        promising=host_signal_positive,
        family_state=family_state,
        host_state_band=str(run_info.get('host_state_band') or ''),
    )
    run_info['campaign_state'] = {
        'family_state': family_state,
        'host_stage': host_stage,
    }
    run_info['runtime_utility'] = compute_runtime_utility(
        action_type=str((run_info.get('brain') or {}).get('action_type') or (run_info.get('brain_reasoning_summary') or {}).get('action_type') or 'single_probe'),
        decision_quality=run_info.get('decision_quality'),
        economics=run_info.get('decision_economics'),
        promising=finding_signal_positive,
        host_state_band=str(run_info.get('host_state_band') or ''),
        task_family=str(run_info.get('task_family') or ''),
        contamination=run_info.get('run_contamination') if isinstance(run_info.get('run_contamination'), dict) else {},
    )
    record_run_fn(runs, run_info)
    now_ts = datetime.now(timezone.utc).timestamp()
    if len(runs) % 5 == 0 or (now_ts - last_persist_ts) >= 5:
        persist_live_summary_fn()
        last_persist_ts = now_ts
    history.append(run_info)
    runtime_task = run_info.get('runtime_task') if isinstance(run_info.get('runtime_task'), dict) else {}
    planner_rationale = run_info.get('planner_rationale') if isinstance(run_info.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
    planning_ladder = run_info.get('planning_ladder') if isinstance(run_info.get('planning_ladder'), dict) else (runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {}))
    target_profile_summary = planner_rationale.get('target_profile_summary') if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
    update_learning_fn(
        host,
        fam,
        str(run_info.get('classification') or 'unknown'),
        workflow_promotable,
        str(run_info.get('engine_status') or 'unknown'),
        capability=str((run_info.get('brain') or {}).get('capability') or (run_info.get('brain_reasoning_summary') or {}).get('capability') or ''),
        tool=str((run_info.get('engine_compiler') or {}).get('compiler_tool_choice') or (run_info.get('brain') or {}).get('tool') or ''),
        action_type=str((run_info.get('brain') or {}).get('action_type') or (run_info.get('brain_reasoning_summary') or {}).get('action_type') or 'single_probe'),
        host_stage=host_stage,
        planning_stage=str(planning_ladder.get('current_stage') or ''),
        next_stage=str(planning_ladder.get('next_stage') or ''),
        target_type=str(target_profile_summary.get('target_type') or ''),
        target_surface_rationale=[str(x or '').strip().lower() for x in (planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()],
    )
    hs_all[host] = host_update.state
    host_state['hosts'] = hs_all
    save_host_state_fn(host_state)
    run_info['adaptation_signal'] = build_adaptation_signal(
        host_update=host_update.as_dict(),
        runs_count=len(runs),
        run_info=run_info,
        recent_runs=runs[-24:],
    )
    if len(runs) % 20 == 0:
        reprioritize_queues_fn()
    return last_persist_ts
