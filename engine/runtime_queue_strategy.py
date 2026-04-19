from __future__ import annotations

import math
from typing import Any, Callable

from learning_store import top_archetype_hints, top_branch_hints, top_transition_action_hints
from runtime_archetype_inference import infer_runtime_archetypes
from signal_contract import signal_contract_workflow_promotable  # type: ignore


def _learning_excluded(run: dict) -> bool:
    contamination = run.get('run_contamination') if isinstance(run.get('run_contamination'), dict) else {}
    return bool(contamination.get('learning_excluded', False))


def _family_recent_slice(runs: list[dict], fam: str, attack_family_fn: Callable[[str, str, str], str], window: int) -> list[dict]:
    return [
        r for r in runs[-window:]
        if isinstance(r, dict)
        and not _learning_excluded(r)
        and attack_family_fn(str(r.get('objective') or ''), str(r.get('target') or ''), str(r.get('task_family') or '')) == fam
    ]


def _family_yield_trend(recent: list[dict]) -> tuple[float, float]:
    sample = [r for r in recent if isinstance(r, dict)]
    if not sample:
        return 0.0, 0.0

    def _quality_score(bucket: list[dict]) -> float:
        if not bucket:
            return 0.0
        size = max(1, len(bucket))
        promotable = sum(1 for r in bucket if (signal_contract_workflow_promotable(r.get('signal_contract')) if isinstance(r.get('signal_contract'), dict) else bool(r.get('workflow_promotable', r.get('promising', False))))) / size
        probable = sum(1 for r in bucket if str(r.get('finding_lifecycle') or '') == 'probable') / size
        confirmed = sum(1 for r in bucket if str(r.get('finding_lifecycle') or '') == 'confirmed') / size
        partial_or_better = sum(1 for r in bucket if str(((r.get('signal_contract') or {}).get('success_outcome') or {}).get('status') or r.get('success_criteria_eval') or '').strip().lower() in {'met', 'partial'}) / size
        utility_avg = sum(float((r.get('runtime_utility') or {}).get('net_utility_score', 0.0) or 0.0) for r in bucket if isinstance(r.get('runtime_utility'), dict)) / size
        econ_avg = sum(float((r.get('decision_economics') or {}).get('priority_score', 0.0) or 0.0) for r in bucket if isinstance(r.get('decision_economics'), dict)) / size
        failure_rate = sum(1 for r in bucket if str(r.get('engine_status') or '').strip().lower() in {'failed', 'error', 'timeout'}) / size
        return (promotable * 0.36) + (probable * 0.24) + (confirmed * 0.34) + (partial_or_better * 0.2) + max(-0.18, min(0.18, utility_avg * 0.18)) + max(-0.14, min(0.14, econ_avg * 0.14)) - (failure_rate * 0.32)

    if len(sample) < 4:
        quality = _quality_score(sample)
        return quality * 0.35, max(0.0, -quality)
    split = max(2, len(sample) // 2)
    older = sample[:-split]
    newer = sample[-split:]
    older_score = _quality_score(older)
    newer_score = _quality_score(newer)
    trend = newer_score - older_score
    noise_pressure = max(0.0, -newer_score) + max(0.0, older_score - newer_score)
    return trend, noise_pressure


def _empirical_quality(recent: list[dict]) -> tuple[float, float, float, float]:
    sample = [r for r in recent if isinstance(r, dict)]
    if not sample:
        return 0.0, 0.0, 0.0, 0.0
    size = max(1, len(sample))
    promotable = sum(1 for r in sample if (signal_contract_workflow_promotable(r.get('signal_contract')) if isinstance(r.get('signal_contract'), dict) else bool(r.get('workflow_promotable', r.get('promising', False))))) / size
    probable = sum(1 for r in sample if str(r.get('finding_lifecycle') or '') == 'probable') / size
    confirmed = sum(1 for r in sample if str(r.get('finding_lifecycle') or '') == 'confirmed') / size
    partial_or_better = sum(1 for r in sample if str(((r.get('signal_contract') or {}).get('success_outcome') or {}).get('status') or r.get('success_criteria_eval') or '').strip().lower() in {'met', 'partial'}) / size
    utility_avg = sum(float((r.get('runtime_utility') or {}).get('net_utility_score', 0.0) or 0.0) for r in sample if isinstance(r.get('runtime_utility'), dict)) / size
    econ_avg = sum(float((r.get('decision_economics') or {}).get('priority_score', 0.0) or 0.0) for r in sample if isinstance(r.get('decision_economics'), dict)) / size
    yield_rate = (promotable * 0.34) + (probable * 0.24) + (confirmed * 0.34) + (partial_or_better * 0.18)
    score = yield_rate + max(-0.2, min(0.2, utility_avg * 0.18)) + max(-0.16, min(0.16, econ_avg * 0.14))
    exploration_bonus = min(0.12, math.sqrt(1.8 / (size + 1.0)) * 0.18)
    return score, exploration_bonus, yield_rate, float(size)


def _empirical_family_multiplier(task: dict, runs: list[dict], toggles: dict, attack_family_fn: Callable[[str, str, str], str]) -> tuple[float, float]:
    fam = attack_family_fn(str(task.get('objective') or ''), str(task.get('target') or ''), str(task.get('task_family') or ''))
    recent_window = max(20, int(toggles.get('empirical_recent_window_runs', 180) or 180))
    recent = _family_recent_slice(runs, fam, attack_family_fn, recent_window)
    score, exploration_bonus, _yield, _sample = _empirical_quality(recent)
    multiplier = max(0.82, min(1.28, 1.0 + (score * 0.18) + exploration_bonus))
    return multiplier, exploration_bonus


def _task_capability_candidates(task: dict) -> list[str]:
    runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    caps: list[str] = []
    for raw in [task.get('capability_candidates'), runtime_task.get('capability_candidates')]:
        if isinstance(raw, list):
            for item in raw:
                text = str(item).strip().lower()
                if text and text not in caps:
                    caps.append(text)
    capability = str(task.get('capability') or runtime_task.get('capability') or '').strip().lower()
    if capability and capability not in caps:
        caps.insert(0, capability)
    return caps[:6]


def _run_capability(run: dict) -> str:
    if not isinstance(run, dict):
        return ''
    brain = run.get('brain') if isinstance(run.get('brain'), dict) else {}
    summary = run.get('brain_reasoning_summary') if isinstance(run.get('brain_reasoning_summary'), dict) else {}
    return str(brain.get('capability') or summary.get('capability') or '').strip().lower()


def _capability_yield_multiplier(task: dict, runs: list[dict], toggles: dict) -> tuple[float, str, float]:
    candidates = _task_capability_candidates(task)
    if not candidates:
        return 1.0, '', 0.0
    recent_window = max(20, int(toggles.get('capability_recent_window_runs', 180) or 180))
    best_score = 1.0
    best_capability = ''
    best_exploration = 0.0
    for capability in candidates:
        recent = [r for r in runs[-recent_window:] if isinstance(r, dict) and not _learning_excluded(r) and _run_capability(r) == capability]
        if not recent:
            continue
        score, exploration_bonus, _yield, _sample = _empirical_quality(recent)
        multiplier = 1.0 + (score * 0.16) + exploration_bonus
        if multiplier > best_score:
            best_score = multiplier
            best_capability = capability
            best_exploration = exploration_bonus
    boosts = [str(x).strip().lower() for x in (toggles.get('capability_lane_boost', []) or []) if str(x).strip()] if isinstance(toggles.get('capability_lane_boost', []), list) else []
    suppress = [str(x).strip().lower() for x in (toggles.get('capability_lane_suppress', []) or []) if str(x).strip()] if isinstance(toggles.get('capability_lane_suppress', []), list) else []
    for capability in candidates:
        if capability in boosts:
            best_score = max(best_score, 1.15)
            best_capability = best_capability or capability
        if capability in suppress:
            best_score = min(best_score, 0.85)
            best_capability = best_capability or capability
    return max(0.6, min(1.45, best_score)), best_capability, best_exploration


def dynamic_family_boost(
    *,
    runs: list[dict],
    toggles: dict,
    attack_family_fn: Callable[[str, str, str], str],
) -> dict[str, float]:
    fam = {'recon': 1.0, 'xss': 1.0, 'idor': 1.0, 'generic': 1.0}
    for r in runs[-120:]:
        if not isinstance(r, dict) or _learning_excluded(r):
            continue
        f = attack_family_fn(str(r.get('objective') or ''), str(r.get('target') or ''), str(r.get('task_family') or ''))
        if f not in fam:
            fam[f] = 1.0
        st = str(r.get('engine_status') or '').lower()
        fam[f] += 0.08 if st in {'success', 'ok'} else (-0.06 if st in {'failed', 'error', 'timeout'} else 0)

    boosts = toggles.get('family_lane_boost', []) if isinstance(toggles.get('family_lane_boost', []), list) else []
    suppress = toggles.get('family_lane_suppress', []) if isinstance(toggles.get('family_lane_suppress', []), list) else []
    for b in [str(x).strip().lower() for x in boosts if str(x).strip()]:
        fam[b] = fam.get(b, 1.0) + 0.2
    for s in [str(x).strip().lower() for x in suppress if str(x).strip()]:
        fam[s] = fam.get(s, 1.0) - 0.2

    if bool(toggles.get('family_decay_enabled', True)):
        window = max(6, int(toggles.get('family_decay_window_runs', 24) or 24))
        penalty = float(toggles.get('family_decay_penalty', 0.12) or 0.12)
        eligible_recent = [r for r in runs[-window:] if isinstance(r, dict) and not _learning_excluded(r)]
        recent_fams = [
            attack_family_fn(str(r.get('objective') or ''), str(r.get('target') or ''), str(r.get('task_family') or ''))
            for r in eligible_recent
        ]
        for fkey in set(recent_fams):
            density = recent_fams.count(fkey) / max(1, len(recent_fams))
            if density >= 0.33:
                fam_runs = _family_recent_slice(runs, fkey, attack_family_fn, window)
                trend, noise_pressure = _family_yield_trend(fam_runs)
                base_decay = penalty * density
                relief = min(base_decay * 0.8, max(0.0, trend) * 0.18)
                extra = min(base_decay * 0.75, max(0.0, -trend) * 0.12 + noise_pressure * 0.08)
                fam[fkey] = fam.get(fkey, 1.0) - max(0.0, base_decay - relief + extra)

    for k, v in list(fam.items()):
        fam[k] = max(0.55, min(1.45, v))
    return fam


def _transition_prior_multiplier(task: dict) -> tuple[float, list[str]]:
    runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    planner_rationale = task.get('planner_rationale') if isinstance(task.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
    planning_ladder = task.get('planning_ladder') if isinstance(task.get('planning_ladder'), dict) else (runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {}))
    target = str(task.get('target') or runtime_task.get('target') or '').strip().lower()
    host = target.split('//', 1)[-1].split('/', 1)[0].strip().lower()
    hints = top_transition_action_hints(
        family=str(task.get('task_family') or runtime_task.get('task_family') or ''),
        capability=str(task.get('capability') or runtime_task.get('capability') or ''),
        action_type=str(task.get('action_type') or runtime_task.get('action_type') or ''),
        next_stage=str(planning_ladder.get('next_stage') or ''),
        host=host,
        limit=2,
    )
    if not hints:
        return 1.0, []
    top_score = max(float(item.get('score', 0.0) or 0.0) for item in hints)
    boost = min(0.18, max(0.0, top_score - 1.0) * 0.12)
    actions = [str(item.get('next_action_type') or '').strip().lower() for item in hints if str(item.get('next_action_type') or '').strip()]
    return 1.0 + boost, actions[:2]



def _archetype_multiplier(task: dict, host_from_target_fn: Callable[[str], str]) -> tuple[float, dict[str, Any]]:
    runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    planner_rationale = task.get('planner_rationale') if isinstance(task.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
    target_profile_summary = planner_rationale.get('target_profile_summary') if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
    target_type = str(target_profile_summary.get('target_type') or '').strip().lower()
    host = host_from_target_fn(str(task.get('target') or runtime_task.get('target') or ''))
    inferred = infer_runtime_archetypes(target_type=target_type, host=host, top_archetype_hints_fn=top_archetype_hints, limit=3)
    archetypes = [str(x or '').strip().lower() for x in (inferred.get('archetypes') or []) if str(x or '').strip()]
    if not archetypes:
        return 1.0, {'primary_archetype': '', 'archetypes': [], 'confidence': 0.0, 'flags': {}}
    flags = inferred.get('flags') if isinstance(inferred.get('flags'), dict) else {}
    mult = 1.0
    if bool(flags.get('auth_heavy')) or bool(flags.get('api_first')) or bool(flags.get('workflow_app')):
        mult += 0.08
    if bool(flags.get('admin_surface')):
        mult += 0.05
    if bool(flags.get('static_edge')) and str(task.get('task_family') or '').strip().lower() in {'tls_assessment', 'content_discovery', 'recon'}:
        mult += 0.06
    inferred_out = dict(inferred)
    inferred_out['archetypes'] = archetypes[:3]
    return max(0.9, min(1.22, mult)), inferred_out



def _branch_state_multiplier(task: dict) -> tuple[float, str]:
    branch_state = str(task.get('branch_state') or '').strip().lower()
    branch_action = str(task.get('branch_action') or '').strip().lower()
    branch_reason = str(task.get('branch_reason') or '').strip().lower()
    branch_score = float(task.get('branch_evidence_score') or 0.0)
    mult = 1.0
    if branch_state == 'branch_candidate':
        mult += 0.08
    if branch_action == 'deepen':
        mult += 0.1
    elif branch_action == 'confirm':
        mult += 0.07
    elif branch_action == 'pivot':
        mult += 0.05
    elif branch_action == 'defer':
        mult -= 0.08
    mult += min(0.12, max(0.0, branch_score) * 0.2)
    return max(0.82, min(1.24, mult)), branch_reason



def _branch_history_multiplier(task: dict, host_from_target_fn: Callable[[str], str]) -> tuple[float, list[str]]:
    runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    planner_rationale = task.get('planner_rationale') if isinstance(task.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
    planning_ladder = task.get('planning_ladder') if isinstance(task.get('planning_ladder'), dict) else (runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {}))
    host = host_from_target_fn(str(task.get('target') or runtime_task.get('target') or ''))
    hints = top_branch_hints(
        branch_state=str(task.get('branch_state') or runtime_task.get('branch_state') or ''),
        branch_action=str(task.get('branch_action') or runtime_task.get('branch_action') or ''),
        branch_reason=str(task.get('branch_reason') or runtime_task.get('branch_reason') or ''),
        next_stage=str(planning_ladder.get('next_stage') or ''),
        host=host,
        limit=2,
    )
    if not hints:
        return 1.0, []
    mult = 1.0
    reasons: list[str] = []
    for hint in hints:
        dead_end = int(hint.get('dead_end', 0) or 0)
        productive = int(hint.get('productive', 0) or 0)
        score = float(hint.get('score', 0.0) or 0.0)
        reason = str(hint.get('branch_reason') or '').strip().lower()
        lifecycle_status = str(hint.get('branch_lifecycle_status') or '').strip().lower()
        lifecycle_reason = str(hint.get('branch_lifecycle_reason') or '').strip().lower()
        thread_label = str(hint.get('branch_thread_label') or '').strip().lower()
        if reason:
            reasons.append(reason)
        if lifecycle_reason and lifecycle_reason not in reasons:
            reasons.append(lifecycle_reason)
        if thread_label and thread_label not in reasons:
            reasons.append(thread_label)
        if lifecycle_status == 'dead_end':
            mult -= min(0.2, 0.07 + max(0, dead_end - productive) * 0.04)
        elif lifecycle_status == 'productive':
            mult += min(0.14, 0.05 + max(0, productive - dead_end) * 0.03)
        elif dead_end > productive and score < 0:
            mult -= min(0.18, 0.05 + (dead_end - productive) * 0.04)
        elif productive > dead_end and score > 0:
            mult += min(0.12, 0.04 + (productive - dead_end) * 0.03)
    deduped: list[str] = []
    for item in reasons:
        if item and item not in deduped:
            deduped.append(item)
    return max(0.78, min(1.18, mult)), deduped[:3]



def _semantic_task_multiplier(task: dict) -> float:
    runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    planner_rationale = task.get('planner_rationale') if isinstance(task.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
    planning_ladder = task.get('planning_ladder') if isinstance(task.get('planning_ladder'), dict) else (runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {}))
    exploit_ladder = task.get('exploit_ladder') if isinstance(task.get('exploit_ladder'), dict) else (runtime_task.get('exploit_ladder') if isinstance(runtime_task.get('exploit_ladder'), dict) else {})
    actor_requirements = task.get('actor_requirements') if isinstance(task.get('actor_requirements'), dict) else (runtime_task.get('actor_requirements') if isinstance(runtime_task.get('actor_requirements'), dict) else {})
    session_requirements = task.get('session_requirements') if isinstance(task.get('session_requirements'), dict) else (runtime_task.get('session_requirements') if isinstance(runtime_task.get('session_requirements'), dict) else {})
    promotion_policy = task.get('promotion_policy') if isinstance(task.get('promotion_policy'), dict) else (runtime_task.get('promotion_policy') if isinstance(runtime_task.get('promotion_policy'), dict) else {})
    approval_sensitivity = task.get('approval_sensitivity') if isinstance(task.get('approval_sensitivity'), dict) else (runtime_task.get('approval_sensitivity') if isinstance(runtime_task.get('approval_sensitivity'), dict) else {})
    target_profile_summary = planner_rationale.get('target_profile_summary') if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
    recommended_progression = [str(x or '').strip().lower() for x in (planner_rationale.get('recommended_progression') or []) if str(x or '').strip()]
    target_surface_rationale = [str(x or '').strip().lower() for x in (task.get('target_surface_rationale') or planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()]
    stage = str(exploit_ladder.get('stage') or planning_ladder.get('current_stage') or '').strip().lower()
    next_stage = str(planning_ladder.get('next_stage') or '').strip().lower()
    mult = 1.0
    if stage == 'control_boundary_confirmation':
        mult += 0.18
    elif stage == 'state_transition_confirmation':
        mult += 0.22
    elif stage == 'bounded_exploit_proof':
        mult += 0.28
    elif stage == 'report_artifact_capture':
        mult += 0.10
    elif stage == 'validation':
        mult += 0.05
    if bool(actor_requirements.get('differential')):
        mult += 0.05
    if bool(session_requirements.get('stateful')):
        mult += 0.04
    if bool(session_requirements.get('auth_context')):
        mult += 0.03
    if next_stage in {'bounded_exploit_proof', 'report_artifact_capture'}:
        mult += 0.05
    if next_stage and next_stage in recommended_progression:
        mult += 0.03
    target_type = str(target_profile_summary.get('target_type') or '').strip().lower()
    if target_type in {'api', 'auth', 'integration'} and stage in {'control_boundary_confirmation', 'state_transition_confirmation'}:
        mult += 0.05
    if target_type in {'static', 'support'} and stage == 'discovery' and next_stage == 'report_artifact_capture':
        mult += 0.08
    if 'authenticated_or_boundary_mapping' in target_surface_rationale:
        mult += 0.04
    if 'artifact_capture' in target_surface_rationale:
        mult += 0.05
    if any(x in target_surface_rationale for x in {'admin', 'billing', 'tenant', 'organization', 'api', 'auth', 'account'}):
        mult += 0.03
    evidence_focus = [str(x or '').strip().lower() for x in (task.get('followup_evidence_focus') or []) if str(x or '').strip()]
    if any(x in evidence_focus for x in {'actor_boundary_delta', 'state_transition_artifact', 'exposure_artifact'}):
        mult += 0.04
    prerequisites = [str(x or '').strip().lower() for x in (session_requirements.get('prerequisites') or []) if str(x or '').strip()]
    open_questions = [str(x or '').strip().lower() for x in (task.get('open_questions') or []) if str(x or '').strip()]
    if prerequisites and open_questions and any(p in q or q in p for p in prerequisites for q in open_questions):
        mult -= 0.45
    actor_requirements = task.get('actor_requirements') if isinstance(task.get('actor_requirements'), dict) else (runtime_task.get('actor_requirements') if isinstance(runtime_task.get('actor_requirements'), dict) else {})
    actor_keywords = ('identity', 'identities', 'role', 'roles', 'actor', 'account', 'comparison')
    if bool(actor_requirements.get('required')) and any(any(k in q for k in actor_keywords) for q in open_questions):
        mult -= 0.28
    if bool(promotion_policy.get('confirm_preferred')):
        mult += 0.03
    if bool(approval_sensitivity.get('auth_sensitive')):
        mult += 0.02
    return max(0.7, min(1.65, mult))



def _default_attack_family(objective: str, target: str, task_family: str = '') -> str:
    return str(task_family or 'generic').strip().lower()



def _default_family_allowed_for_host_stage(host_state: dict, target: str, fam: str) -> bool:
    return True



def _default_planner_vector_weight(task: dict, hints: dict) -> float:
    return 1.0



def _default_host_from_target(target: str) -> str:
    return str(target or '').split('//', 1)[-1].split('/', 1)[0].strip().lower()



def reprioritize_queues(
    *,
    followup_queue: list[dict],
    precision_queue: list[dict],
    runs: list[dict] | None = None,
    toggles: dict | None = None,
    planner_hints_cache: dict | None = None,
    host_state: dict | None = None,
    host_family_owner_gate: dict | None = None,
    attack_family_fn: Callable[[str, str, str], str] | None = None,
    family_allowed_for_host_stage_fn: Callable[[dict, str, str], bool] | None = None,
    planner_vector_weight_fn: Callable[[dict, dict], float] | None = None,
    host_from_target_fn: Callable[[str], str] | None = None,
    **_legacy_kwargs: Any,
) -> dict[str, float]:
    runs = runs if isinstance(runs, list) else []
    toggles = toggles if isinstance(toggles, dict) else {}
    planner_hints_cache = planner_hints_cache if isinstance(planner_hints_cache, dict) else {}
    host_state = host_state if isinstance(host_state, dict) else {}
    host_family_owner_gate = host_family_owner_gate if isinstance(host_family_owner_gate, dict) else {}
    attack_family_fn = attack_family_fn or _default_attack_family
    family_allowed_for_host_stage_fn = family_allowed_for_host_stage_fn or _default_family_allowed_for_host_stage
    planner_vector_weight_fn = planner_vector_weight_fn or _default_planner_vector_weight
    host_from_target_fn = host_from_target_fn or _default_host_from_target
    family_weights = dynamic_family_boost(runs=runs, toggles=toggles, attack_family_fn=attack_family_fn)

    def _score(task: dict) -> float:
        fam = attack_family_fn(str(task.get('objective') or ''), str(task.get('target') or ''), str(task.get('task_family') or ''))
        fam_score = float(family_weights.get(fam, 1.0))
        if not family_allowed_for_host_stage_fn(host_state, str(task.get('target') or ''), fam):
            return 0.01
        fy = 1.0
        recent = _family_recent_slice(runs, fam, attack_family_fn, 180)
        if recent:
            promising_n = sum(1 for r in recent if (signal_contract_workflow_promotable(r.get('signal_contract')) if isinstance(r.get('signal_contract'), dict) else bool(r.get('workflow_promotable', r.get('promising', False)))))
            confirmed_n = sum(1 for r in recent if str(r.get('finding_lifecycle') or '') == 'confirmed')
            probable_n = sum(1 for r in recent if str(r.get('finding_lifecycle') or '') == 'probable')
            utility_avg = sum(float((r.get('runtime_utility') or {}).get('net_utility_score', 0.0) or 0.0) for r in recent if isinstance(r.get('runtime_utility'), dict)) / max(1, len(recent))
            econ_avg = sum(float((r.get('decision_economics') or {}).get('priority_score', 0.0) or 0.0) for r in recent if isinstance(r.get('decision_economics'), dict)) / max(1, len(recent))
            fy = min(1.35, 1.0 + ((promising_n * 0.03 + probable_n * 0.05 + confirmed_n * 0.08) / max(1, len(recent))) + min(0.12, max(-0.12, utility_avg * 0.15)) + min(0.1, max(-0.1, econ_avg * 0.12)))
        empirical_family_score, family_exploration_bonus = _empirical_family_multiplier(task, runs, toggles, attack_family_fn)
        capability_score, selected_capability, capability_exploration_bonus = _capability_yield_multiplier(task, runs, toggles)
        hint_score = float(planner_vector_weight_fn(task, planner_hints_cache))
        runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
        planner_rationale = task.get('planner_rationale') if isinstance(task.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
        planning_ladder = task.get('planning_ladder') if isinstance(task.get('planning_ladder'), dict) else (runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {}))
        exploit_ladder = task.get('exploit_ladder') if isinstance(task.get('exploit_ladder'), dict) else (runtime_task.get('exploit_ladder') if isinstance(runtime_task.get('exploit_ladder'), dict) else {})
        stage = str(exploit_ladder.get('stage') or planning_ladder.get('current_stage') or '').strip().lower()
        next_stage = str(planning_ladder.get('next_stage') or '').strip().lower()
        if selected_capability:
            task['capability_lane'] = selected_capability
            if isinstance(runtime_task, dict):
                runtime_task['capability_lane'] = selected_capability
        task['empirical_family_score'] = round(empirical_family_score, 3)
        task['empirical_family_exploration_bonus'] = round(family_exploration_bonus, 3)
        task['empirical_capability_score'] = round(capability_score, 3)
        task['empirical_capability_exploration_bonus'] = round(capability_exploration_bonus, 3)
        utility_base = float(task.get('utility_score') or runtime_task.get('utility_score') or 0.0)
        priority_base = float(task.get('priority_score') or runtime_task.get('priority_score') or task.get('target_score', 1.0) or 1.0)
        if utility_base:
            priority_base = (priority_base * 0.7) + (utility_base * 0.3)
        host = host_from_target_fn(str(task.get('target') or ''))
        hs = ((host_state or {}).get('hosts') or {}).get(host, {}) if isinstance((host_state or {}).get('hosts'), dict) else {}
        promise = float(hs.get('promise_score', 1.0) or 1.0)
        noise = float(hs.get('noise_score', 1.0) or 1.0)
        host_band = str(hs.get('state_band') or hs.get('state') or '').strip().lower()
        exploitation_score = float(hs.get('exploitation_score', 0.0) or 0.0)
        exploit_focus_family = str(hs.get('exploit_focus_family') or '').strip().lower()
        preferred_stages = {str(x or '').strip().lower() for x in (hs.get('preferred_stages') or []) if str(x or '').strip()}
        host_surface_rationale = {str(x or '').strip().lower() for x in (hs.get('target_surface_rationale') or []) if str(x or '').strip()}
        task_surface_rationale = {str(x or '').strip().lower() for x in (task.get('target_surface_rationale') or planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()}
        stage_match = bool(stage and stage in preferred_stages)
        next_stage_match = bool(next_stage and next_stage in preferred_stages)
        surface_match = bool(host_surface_rationale & task_surface_rationale)
        host_focus = 1.0
        if host_band == 'exploitation':
            host_focus += min(0.28, 0.12 + (exploitation_score * 0.18))
            if stage_match or next_stage_match:
                host_focus += 0.12
            elif preferred_stages:
                host_focus -= 0.05
            if surface_match:
                host_focus += 0.08
            elif host_surface_rationale and task_surface_rationale:
                host_focus -= 0.04
            if not preferred_stages and not host_surface_rationale:
                if exploit_focus_family and fam == exploit_focus_family:
                    host_focus += 0.12
                elif exploit_focus_family and fam != exploit_focus_family:
                    host_focus -= 0.08
        elif host_band == 'promising':
            if stage_match or next_stage_match:
                host_focus += 0.06
            elif exploit_focus_family and fam == exploit_focus_family and not preferred_stages:
                host_focus += 0.05
            if surface_match:
                host_focus += 0.04
        host_boosts = toggles.get('host_family_lane_boost', {}) if isinstance(toggles.get('host_family_lane_boost', {}), dict) else {}
        host_suppress = toggles.get('host_family_lane_suppress', {}) if isinstance(toggles.get('host_family_lane_suppress', {}), dict) else {}
        if host in host_boosts and fam in [str(x).strip().lower() for x in (host_boosts.get(host) or []) if str(x).strip()]:
            fam_score += 0.25
        if host in host_suppress and fam in [str(x).strip().lower() for x in (host_suppress.get(host) or []) if str(x).strip()]:
            fam_score -= 0.25
        gate_ct = int(host_family_owner_gate.get((host, fam), 0) or 0)
        if gate_ct >= 2:
            fam_score -= 0.35
        cost_band = str(task.get('cost_band') or ((task.get('runtime_task') or {}).get('cost_band') if isinstance(task.get('runtime_task'), dict) else '') or 'medium').lower()
        cost_penalty = {'low': 1.08, 'medium': 1.0, 'high': 0.9}.get(cost_band, 1.0)
        priority_tier = str(task.get('priority_tier') or runtime_task.get('priority_tier') or 'medium').strip().lower()
        expected_depth = str(task.get('expected_depth') or runtime_task.get('expected_depth') or 'medium').strip().lower()
        activation_phase = int(task.get('activation_phase') or runtime_task.get('activation_phase') or 1)
        activation_mode = str(task.get('activation_mode') or runtime_task.get('activation_mode') or 'immediate').strip().lower()
        surface_role = str(task.get('surface_role') or runtime_task.get('surface_role') or 'primary').strip().lower()
        planner_execution_multiplier = 1.0
        planner_execution_multiplier *= {'high': 1.22, 'medium': 1.0, 'low': 0.82}.get(priority_tier, 1.0)
        planner_execution_multiplier *= {'deep': 1.08, 'medium': 1.0, 'light': 0.9}.get(expected_depth, 1.0)
        planner_execution_multiplier *= {1: 1.18, 2: 0.94, 3: 0.72}.get(max(1, min(3, activation_phase)), 1.0)
        planner_execution_multiplier *= {'immediate': 1.1, 'if_signal': 0.92, 'if_confirmed': 0.82, 'background': 0.7}.get(activation_mode, 1.0)
        planner_execution_multiplier *= {'primary': 1.08, 'supporting': 0.92, 'background': 0.75}.get(surface_role, 1.0)
        semantic_multiplier = _semantic_task_multiplier(task)
        transition_prior_multiplier, transition_prior_actions = _transition_prior_multiplier(task)
        archetype_multiplier, archetype_inferred = _archetype_multiplier(task, host_from_target_fn)
        branch_state_multiplier, branch_reason = _branch_state_multiplier(task)
        branch_history_multiplier, branch_history_reasons = _branch_history_multiplier(task, host_from_target_fn)
        task['semantic_multiplier'] = round(semantic_multiplier, 3)
        task['planner_execution_multiplier'] = round(planner_execution_multiplier, 3)
        task['transition_prior_multiplier'] = round(transition_prior_multiplier, 3)
        task['archetype_multiplier'] = round(archetype_multiplier, 3)
        task['branch_state_multiplier'] = round(branch_state_multiplier, 3)
        task['branch_history_multiplier'] = round(branch_history_multiplier, 3)
        if transition_prior_actions:
            task['transition_prior_actions'] = list(transition_prior_actions)
        archetypes = [str(x or '').strip().lower() for x in (archetype_inferred.get('archetypes') or []) if str(x or '').strip()]
        if archetypes:
            task['archetype_hints'] = list(archetypes)
            task['archetype_primary'] = str(archetype_inferred.get('primary_archetype') or archetypes[0])
            task['archetype_confidence'] = round(float(archetype_inferred.get('confidence', 0.0) or 0.0), 3)
        if branch_reason:
            task['branch_reason_scored'] = branch_reason
        if branch_history_reasons:
            task['branch_history_reasons'] = list(branch_history_reasons)
        return priority_base * fam_score * fy * empirical_family_score * capability_score * hint_score * promise * noise * host_focus * cost_penalty * semantic_multiplier * planner_execution_multiplier * transition_prior_multiplier * archetype_multiplier * branch_state_multiplier * branch_history_multiplier

    followup_queue.sort(key=lambda x: -_score(x))
    precision_queue.sort(key=lambda x: -_score(x))
    return family_weights
