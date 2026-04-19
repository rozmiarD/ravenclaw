from __future__ import annotations

from typing import Any, Dict

from signal_contract import signal_contract_promising, success_outcome_status  # type: ignore
from semantic_loss_policy import semantic_loss_penalty  # type: ignore


def _score_from_scale(value: Any, mapping: Dict[str, float], *, default: float = 0.0) -> float:
    raw = str(value or '').strip().lower()
    if not raw:
        return default
    if raw in mapping:
        return mapping[raw]
    try:
        numeric = float(raw)
        return numeric
    except Exception:
        return default


def compute_decision_quality(run_info: Dict[str, Any]) -> Dict[str, Any]:
    brain = run_info.get('brain') if isinstance(run_info.get('brain'), dict) else {}
    analysis = run_info.get('analysis_contract') if isinstance(run_info.get('analysis_contract'), dict) else {}
    compiler = run_info.get('engine_compiler') if isinstance(run_info.get('engine_compiler'), dict) else {}
    signal_contract = run_info.get('signal_contract') if isinstance(run_info.get('signal_contract'), dict) else {}
    semantic_policy = compiler.get('semantic_loss_policy') if isinstance(compiler.get('semantic_loss_policy'), dict) else {}
    promising = signal_contract_promising(signal_contract) if signal_contract else bool(run_info.get('workflow_promotable', run_info.get('promising', False)))
    quality = 0.0
    if promising:
        quality += 0.3
    if str(analysis.get('expected_signal_observed') or '') == 'yes':
        quality += 0.25
    elif str(analysis.get('expected_signal_observed') or '') == 'partial':
        quality += 0.12
    if str(analysis.get('evidence_goal_met') or '') == 'yes':
        quality += 0.2
    elif str(analysis.get('evidence_goal_met') or '') == 'partial':
        quality += 0.1
    if str(analysis.get('hypothesis_support') or '') == 'strengthened':
        quality += 0.15
    elif str(analysis.get('hypothesis_support') or '') == 'weakened':
        quality -= 0.1
    if str(brain.get('planner_alignment') or '') == 'override':
        quality += 0.08 if promising else -0.05
    quality += semantic_loss_penalty(semantic_policy or ({'loss_class': 'degraded_semantics'} if bool(compiler.get('semantic_loss_detected', False)) else {}))
    redundancy_risk = str(brain.get('redundancy_risk') or 'unknown')
    if redundancy_risk == 'high':
        quality -= 0.1
    elif redundancy_risk == 'low':
        quality += 0.05

    novelty_gain_score = _score_from_scale(
        analysis.get('novelty_gain'),
        {'none': 0.0, 'low': 0.04, 'medium': 0.1, 'high': 0.18, 'very_high': 0.24},
    )
    reproducibility_score = _score_from_scale(
        analysis.get('reproducibility_level'),
        {'none': 0.0, 'low': 0.03, 'medium': 0.08, 'high': 0.14},
    )
    false_positive_risk_penalty = _score_from_scale(
        analysis.get('false_positive_risk'),
        {'low': 0.0, 'medium': 0.06, 'high': 0.14},
    )
    artifact_quality_score = _score_from_scale(
        analysis.get('artifact_quality'),
        {'low': 0.0, 'medium': 0.04, 'high': 0.08},
    )

    quality += novelty_gain_score + reproducibility_score + artifact_quality_score - false_positive_risk_penalty

    contamination = run_info.get('run_contamination') if isinstance(run_info.get('run_contamination'), dict) else {}
    contamination_score = float(contamination.get('score', 0.0) or 0.0)
    contamination_penalty = round(contamination_score * 0.4, 3)
    quality -= contamination_penalty

    information_gain = 0.0
    if str(analysis.get('expected_signal_observed') or '') in {'yes', 'partial'}:
        information_gain += 0.2
    if str(analysis.get('hypothesis_support') or '') == 'strengthened':
        information_gain += 0.15
    information_gain += max(0.0, novelty_gain_score)
    decision_quality_score = round(max(-1.0, min(1.5, quality)), 3)
    information_gain_score = round(max(0.0, min(1.5, information_gain)), 3)
    redundancy_adjustment = round(-0.1 if redundancy_risk == 'high' else (0.05 if redundancy_risk == 'low' else 0.0), 3)
    return {
        'decision_quality_score': decision_quality_score,
        'information_gain_score': information_gain_score,
        'planner_override_value': round(0.08 if str(brain.get('planner_alignment') or '') == 'override' and promising else (-0.05 if str(brain.get('planner_alignment') or '') == 'override' else 0.0), 3),
        'semantic_loss_penalty': round(semantic_loss_penalty(semantic_policy or ({'loss_class': 'degraded_semantics'} if bool(compiler.get('semantic_loss_detected', False)) else {})), 3),
        'redundancy_adjustment': redundancy_adjustment,
        'redundancy_penalty': round(abs(min(0.0, redundancy_adjustment)), 3),
        'redundancy_bonus': round(max(0.0, redundancy_adjustment), 3),
        'novelty_gain_score': round(novelty_gain_score, 3),
        'reproducibility_score': round(reproducibility_score, 3),
        'false_positive_risk_penalty': round(false_positive_risk_penalty, 3),
        'artifact_quality_score': round(artifact_quality_score, 3),
        'contamination_penalty': contamination_penalty,
        'contamination_status': str(contamination.get('status') or 'clean'),
        'contamination_score': round(contamination_score, 3),
        'learning_excluded': bool(contamination.get('learning_excluded', False)),
        'contamination_tags': list(contamination.get('tags') or []),
        'evidence_goal_quality': str(analysis.get('evidence_goal_met') or 'unknown'),
    }


def aggregate_campaign_learning(runs: list[dict]) -> Dict[str, Any]:
    action_type_yield: dict[str, dict[str, float]] = {}
    capability_yield: dict[str, dict[str, float]] = {}
    tool_yield: dict[str, dict[str, float]] = {}
    host_stage_yield: dict[str, dict[str, float]] = {}
    planning_stage_yield: dict[str, dict[str, float]] = {}
    next_stage_yield: dict[str, dict[str, float]] = {}
    target_type_yield: dict[str, dict[str, float]] = {}
    target_surface_signal_yield: dict[str, dict[str, float]] = {}
    contamination_summary = {'excluded_runs': 0, 'tags': {}}
    override_success = {'count': 0, 'promising': 0}
    for run in [r for r in (runs or []) if isinstance(r, dict)]:
        contamination = run.get('run_contamination') if isinstance(run.get('run_contamination'), dict) else {}
        if bool(contamination.get('learning_excluded', False)):
            contamination_summary['excluded_runs'] += 1
            for tag in list(contamination.get('tags') or []):
                contamination_summary['tags'][tag] = int(contamination_summary['tags'].get(tag, 0)) + 1
            continue
        action_type = str((run.get('brain') or {}).get('action_type') or (run.get('brain_reasoning_summary') or {}).get('action_type') or 'single_probe')
        capability = str((run.get('brain') or {}).get('capability') or (run.get('brain_reasoning_summary') or {}).get('capability') or '')
        tool = str((run.get('engine_compiler') or {}).get('compiler_tool_choice') or (run.get('brain') or {}).get('tool') or '')
        host_stage = str((run.get('campaign_state') or {}).get('host_stage') or '')
        runtime_task = run.get('runtime_task') if isinstance(run.get('runtime_task'), dict) else {}
        planner_rationale = run.get('planner_rationale') if isinstance(run.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
        planning_ladder = run.get('planning_ladder') if isinstance(run.get('planning_ladder'), dict) else (runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {}))
        target_profile = planner_rationale.get('target_profile_summary') if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
        planning_stage = str(planning_ladder.get('current_stage') or '')
        next_stage = str(planning_ladder.get('next_stage') or '')
        target_type = str(target_profile.get('target_type') or '')
        target_surface_rationale = [str(x or '').strip().lower() for x in (planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()]
        analysis = run.get('analysis_contract') if isinstance(run.get('analysis_contract'), dict) else {}
        signal_contract = run.get('signal_contract') if isinstance(run.get('signal_contract'), dict) else {}
        promising = signal_contract_promising(signal_contract) if signal_contract else bool(run.get('workflow_promotable', run.get('promising', False)))
        success_status = success_outcome_status(signal_contract) if signal_contract else ''
        partial_or_better = success_status in {'met', 'partial'} if success_status else str(analysis.get('expected_signal_observed') or '') in {'yes', 'partial'}

        def _accumulate(bucket: dict[str, dict[str, float]], key: str) -> None:
            if not key:
                return
            item = bucket.setdefault(key, {'runs': 0, 'promising': 0, 'partial_or_better': 0})
            item['runs'] += 1
            if promising:
                item['promising'] += 1
            if partial_or_better:
                item['partial_or_better'] += 1

        _accumulate(action_type_yield, action_type)
        _accumulate(capability_yield, capability)
        _accumulate(tool_yield, tool)
        _accumulate(host_stage_yield, host_stage)
        _accumulate(planning_stage_yield, planning_stage)
        _accumulate(next_stage_yield, next_stage)
        _accumulate(target_type_yield, target_type)
        for signal in target_surface_rationale[:6]:
            _accumulate(target_surface_signal_yield, signal)
        if str((run.get('brain') or {}).get('planner_alignment') or '') == 'override':
            override_success['count'] += 1
            if promising:
                override_success['promising'] += 1
    return {
        'action_type_yield': action_type_yield,
        'capability_yield': capability_yield,
        'tool_yield': tool_yield,
        'host_stage_yield': host_stage_yield,
        'planning_stage_yield': planning_stage_yield,
        'next_stage_yield': next_stage_yield,
        'target_type_yield': target_type_yield,
        'target_surface_signal_yield': target_surface_signal_yield,
        'planner_override_success': override_success,
        'contamination_summary': contamination_summary,
    }
