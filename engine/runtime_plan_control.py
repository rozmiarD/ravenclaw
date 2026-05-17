from __future__ import annotations

from typing import Any, Callable

from govengine.contracts.signal import (  # type: ignore
    signal_contract_adaptation_positive,
    signal_contract_planner_reconsult_worthy,
    success_outcome_status,
)


def adaptive_quality_context(planner_feedback: dict | None = None) -> dict:
    feedback = planner_feedback if isinstance(planner_feedback, dict) else {}
    branch_quality_rate = round(float(feedback.get('branch_quality_rate_recent', 0.0) or 0.0), 3)
    dead_end_pressure = round(float(feedback.get('dead_end_pressure_recent', 0.0) or 0.0), 3)
    recon_conversion_rate = round(float(feedback.get('recon_conversion_rate_recent', 0.0) or 0.0), 3)
    signal_to_confirmation_efficiency = round(float(feedback.get('signal_to_confirmation_efficiency_recent', 0.0) or 0.0), 3)
    branch_candidate_recent = int(feedback.get('branch_candidate_recent', 0) or 0)
    branch_quality_positive_recent = int(feedback.get('branch_quality_positive_recent', 0) or 0)
    dead_end_branch_recent = int(feedback.get('dead_end_branch_recent', 0) or 0)
    recon_to_exploit_candidate_recent = int(feedback.get('recon_to_exploit_candidate_recent', 0) or 0)
    recon_to_exploit_success_recent = int(feedback.get('recon_to_exploit_success_recent', 0) or 0)
    signal_bearing_recent = int(feedback.get('signal_bearing_recent', 0) or 0)
    confirmation_reached_recent = int(feedback.get('confirmation_reached_recent', 0) or 0)
    return {
        'branch_quality_rate_recent': branch_quality_rate,
        'dead_end_pressure_recent': dead_end_pressure,
        'recon_conversion_rate_recent': recon_conversion_rate,
        'signal_to_confirmation_efficiency_recent': signal_to_confirmation_efficiency,
        'branch_candidate_recent': branch_candidate_recent,
        'branch_quality_positive_recent': branch_quality_positive_recent,
        'dead_end_branch_recent': dead_end_branch_recent,
        'recon_to_exploit_candidate_recent': recon_to_exploit_candidate_recent,
        'recon_to_exploit_success_recent': recon_to_exploit_success_recent,
        'signal_bearing_recent': signal_bearing_recent,
        'confirmation_reached_recent': confirmation_reached_recent,
        'dead_end_heavy': dead_end_pressure >= 0.55,
        'quality_structural': branch_quality_rate >= 0.65 or recon_conversion_rate >= 0.5,
        'quality_strong': branch_quality_rate >= 0.75 or recon_conversion_rate >= 0.55,
        'quality_positive_balance': branch_quality_positive_recent > dead_end_branch_recent,
    }


def recon_to_exploit_synthesis(*, planner_feedback: dict | None = None, next_stage: str = '', target_type: str = '', target_surface_rationale: list[str] | None = None, current_family: str = '') -> dict:
    feedback = planner_feedback if isinstance(planner_feedback, dict) else {}
    quality = adaptive_quality_context(feedback)
    stage = str(next_stage or '').strip().lower()
    target_type_l = str(target_type or '').strip().lower()
    surface = [str(x or '').strip().lower() for x in (target_surface_rationale or []) if str(x or '').strip()]
    family = str(current_family or '').strip().lower()
    exploit_surface = any(x in surface for x in {'authenticated_or_boundary_mapping', 'admin', 'billing', 'tenant', 'organization', 'api', 'auth', 'account'})
    artifact_like = 'artifact_capture' in surface or target_type_l in {'static', 'support'}
    if bool(quality.get('dead_end_heavy', False)) and stage in {'validation', 'bounded_exploit_proof', 'control_boundary_confirmation'}:
        return {
            'recommended_branch_action': 'pivot',
            'synthesis_reason': 'dead_end_pressure_redirect',
            'exploit_signal_present': exploit_surface,
            'quality_structural': bool(quality.get('quality_structural', False)),
        }
    if stage == 'report_artifact_capture' and artifact_like:
        return {
            'recommended_branch_action': 'confirm',
            'synthesis_reason': 'artifact_capture_confirmation_bias',
            'exploit_signal_present': exploit_surface,
            'quality_structural': bool(quality.get('quality_structural', False)),
        }
    if stage in {'control_boundary_confirmation', 'state_transition_confirmation'}:
        return {
            'recommended_branch_action': 'confirm',
            'synthesis_reason': 'confirmation_stage_bias',
            'exploit_signal_present': exploit_surface,
            'quality_structural': bool(quality.get('quality_structural', False)),
        }
    if stage == 'bounded_exploit_proof' and (bool(quality.get('quality_structural', False)) or exploit_surface or family in {'authz', 'idor', 'auth_flow', 'logic', 'workflow', 'state_transition'}):
        return {
            'recommended_branch_action': 'deepen',
            'synthesis_reason': 'bounded_proof_progression_bias',
            'exploit_signal_present': exploit_surface,
            'quality_structural': bool(quality.get('quality_structural', False)),
        }
    if stage == 'validation' and not exploit_surface and not bool(quality.get('quality_positive_balance', False)):
        return {
            'recommended_branch_action': 'abandon',
            'synthesis_reason': 'weak_validation_signal',
            'exploit_signal_present': exploit_surface,
            'quality_structural': bool(quality.get('quality_structural', False)),
        }
    return {
        'recommended_branch_action': 'confirm' if exploit_surface else 'pivot',
        'synthesis_reason': 'surface_weighted_default',
        'exploit_signal_present': exploit_surface,
        'quality_structural': bool(quality.get('quality_structural', False)),
    }


def summarize_planner_feedback(*, runs: list[dict], host_state: dict | None = None) -> dict:
    recent = [r for r in (runs or []) if isinstance(r, dict)][-12:]
    aligned = 0
    overrides = 0
    high_redundancy = 0
    partial = 0
    not_met = 0
    adaptation_positive = 0
    reconsult_worthy = 0
    next_family_hints: list[str] = []
    next_stage_hints: list[str] = []
    target_surface_rationale: list[str] = []
    override_reasons: list[str] = []
    branch_candidate_recent = 0
    branch_quality_positive_recent = 0
    dead_end_branch_recent = 0
    recon_to_exploit_candidate_recent = 0
    recon_to_exploit_success_recent = 0
    signal_bearing_recent = 0
    confirmation_reached_recent = 0
    for run in recent:
        brain = run.get('brain') if isinstance(run.get('brain'), dict) else {}
        align = str(brain.get('planner_alignment') or '').strip().lower()
        if align == 'aligned':
            aligned += 1
        elif align == 'override':
            overrides += 1
            reason = str(brain.get('planner_override_reason') or '').strip()
            if reason:
                override_reasons.append(reason[:120])
        if str(brain.get('redundancy_risk') or '').strip().lower() == 'high':
            high_redundancy += 1
        signal_contract = run.get('signal_contract') if isinstance(run.get('signal_contract'), dict) else {}
        analysis = run.get('analysis') if isinstance(run.get('analysis'), dict) else {}
        sev = success_outcome_status(signal_contract) or str(analysis.get('success_criteria_eval') or '').strip().lower()
        if sev == 'partial':
            partial += 1
        elif sev == 'not_met':
            not_met += 1
        if signal_contract_adaptation_positive(signal_contract):
            adaptation_positive += 1
        if signal_contract_planner_reconsult_worthy(signal_contract):
            reconsult_worthy += 1
        hint = str(analysis.get('next_family_hint') or '').strip().lower()
        if hint:
            next_family_hints.append(hint)
        runtime_task = run.get('runtime_task') if isinstance(run.get('runtime_task'), dict) else {}
        planner_rationale = runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else (run.get('planner_rationale') if isinstance(run.get('planner_rationale'), dict) else {})
        planning_ladder = runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {})
        next_stage = str(analysis.get('next_stage_hint') or planning_ladder.get('next_stage') or '').strip().lower()
        if next_stage:
            next_stage_hints.append(next_stage)
        for signal in list(planner_rationale.get('target_surface_rationale') or [])[:4] if isinstance(planner_rationale, dict) else []:
            sig = str(signal or '').strip().lower()
            if sig:
                target_surface_rationale.append(sig)
        runtime_decision = run.get('runtime_decision') if isinstance(run.get('runtime_decision'), dict) else {}
        branch_state = str(runtime_task.get('branch_state') or run.get('branch_state') or '').strip().lower()
        branch_action = str(runtime_task.get('branch_action') or run.get('branch_action') or '').strip().lower()
        branch_score = float(runtime_task.get('branch_evidence_score') or run.get('branch_evidence_score') or 0.0)
        branch_candidate = branch_state == 'branch_candidate' or branch_action in {'confirm', 'deepen', 'pivot'} or branch_score >= 0.18
        if branch_candidate:
            branch_candidate_recent += 1
        success_l = str(sev or '').strip().lower()
        effective_action = str(runtime_decision.get('effective_action') or run.get('decision_effective_action') or '').strip().lower()
        finding_signal = signal_contract.get('finding_signal') if isinstance(signal_contract.get('finding_signal'), dict) else {}
        finding_status = str(finding_signal.get('status') or '').strip().lower()
        candidate = bool(signal_contract_planner_reconsult_worthy(signal_contract) or finding_status in {'weak', 'moderate', 'strong'})
        signal_bearing = bool(candidate or finding_status in {'weak', 'moderate', 'strong'})
        if signal_bearing:
            signal_bearing_recent += 1
        confirmation_reached = bool(effective_action == 'confirm' or success_l in {'partial', 'met'})
        if confirmation_reached:
            confirmation_reached_recent += 1
        recon_like = bool(
            str(run.get('task_family') or runtime_task.get('task_family') or '').strip().lower() in {'recon', 'content_discovery', 'historical_url_mining', 'subdomain_expansion'}
            or str(planning_ladder.get('current_stage') or '').strip().lower() == 'discovery'
        )
        if recon_like and branch_candidate:
            recon_to_exploit_candidate_recent += 1
        recon_success = bool(recon_like and branch_candidate and str(planning_ladder.get('next_stage') or '').strip().lower() in {'bounded_exploit_proof', 'report_artifact_capture'} and success_l in {'partial', 'met'})
        if recon_success:
            recon_to_exploit_success_recent += 1
        dead_end_branch = bool(branch_candidate and success_l in {'not_met', ''} and str(signal_contract.get('adaptation_feedback', {}).get('status') if isinstance(signal_contract.get('adaptation_feedback'), dict) else '').strip().lower() == 'negative')
        if dead_end_branch:
            dead_end_branch_recent += 1
        branch_quality_positive = bool(branch_candidate and success_l in {'partial', 'met'} and not dead_end_branch)
        if branch_quality_positive:
            branch_quality_positive_recent += 1
    degraded = 0
    exploitation = 0
    if isinstance(host_state, dict):
        hosts = (host_state.get('hosts') or {}) if isinstance(host_state.get('hosts'), dict) else {}
        degraded = sum(1 for _h, meta in hosts.items() if isinstance(meta, dict) and str(meta.get('state') or '') == 'degraded')
        exploitation = sum(1 for _h, meta in hosts.items() if isinstance(meta, dict) and str(meta.get('state_band') or meta.get('state') or '').strip().lower() == 'exploitation')
    branch_quality_rate_recent = round(branch_quality_positive_recent / max(1, branch_candidate_recent), 3)
    dead_end_pressure_recent = round(dead_end_branch_recent / max(1, branch_candidate_recent), 3)
    recon_conversion_rate_recent = round(recon_to_exploit_success_recent / max(1, recon_to_exploit_candidate_recent), 3)
    signal_to_confirmation_efficiency_recent = round(confirmation_reached_recent / max(1, signal_bearing_recent), 3)
    feedback = {
        'window_runs': len(recent),
        'planner_aligned_recent': aligned,
        'planner_override_recent': overrides,
        'high_redundancy_recent': high_redundancy,
        'partial_recent': partial,
        'not_met_recent': not_met,
        'adaptation_positive_recent': adaptation_positive,
        'reconsult_worthy_recent': reconsult_worthy,
        'degraded_hosts': degraded,
        'exploitation_hosts': exploitation,
        'recent_next_family_hints': next_family_hints[-4:],
        'recent_next_stage_hints': next_stage_hints[-4:],
        'recent_target_surface_rationale': target_surface_rationale[-6:],
        'recent_override_reasons': override_reasons[-4:],
        'branch_candidate_recent': branch_candidate_recent,
        'branch_quality_positive_recent': branch_quality_positive_recent,
        'dead_end_branch_recent': dead_end_branch_recent,
        'recon_to_exploit_candidate_recent': recon_to_exploit_candidate_recent,
        'recon_to_exploit_success_recent': recon_to_exploit_success_recent,
        'signal_bearing_recent': signal_bearing_recent,
        'confirmation_reached_recent': confirmation_reached_recent,
        'branch_quality_rate_recent': branch_quality_rate_recent,
        'dead_end_pressure_recent': dead_end_pressure_recent,
        'recon_conversion_rate_recent': recon_conversion_rate_recent,
        'signal_to_confirmation_efficiency_recent': signal_to_confirmation_efficiency_recent,
    }
    feedback['adaptive_quality'] = adaptive_quality_context(feedback)
    return feedback


def refresh_planner_hints_and_reprioritize(
    *,
    reason: str,
    tier: str,
    load_planner_hints_fn: Callable[[], dict],
    reprioritize_queues_fn: Callable[[], None],
    log_event_fn: Callable[..., None],
    followup_queue_len: int,
    precision_queue_len: int,
    planner_feedback: dict | None = None,
) -> dict:
    planner_hints = load_planner_hints_fn()
    reprioritize_queues_fn()
    vectors = planner_hints.get('suggested_attack_vectors', []) if isinstance(planner_hints, dict) else []
    feedback = planner_feedback if isinstance(planner_feedback, dict) else {}
    stage_hints = list(feedback.get('recent_next_stage_hints') or []) if isinstance(feedback, dict) else []
    surface_hints = list(feedback.get('recent_target_surface_rationale') or []) if isinstance(feedback, dict) else []
    log_event_fn(
        'PLANER',
        'contextual_reconsult_applied',
        'in_progress',
        f"reason={reason};tier={tier};vectors={len(vectors)};followup_q={followup_queue_len};precision_q={precision_queue_len};aligned={feedback.get('planner_aligned_recent',0)};override={feedback.get('planner_override_recent',0)};partial={feedback.get('partial_recent',0)};not_met={feedback.get('not_met_recent',0)};exploitation_hosts={feedback.get('exploitation_hosts',0)};stage_hints={','.join(str(x) for x in stage_hints[:3])};surface_hints={','.join(str(x) for x in surface_hints[:3])}",
        actor='auto_campaign',
        row_type='service',
        highlight=True,
    )
    return planner_hints if isinstance(planner_hints, dict) else {}


def maybe_trigger_plan_regeneration(
    *,
    reason: str,
    force: bool,
    toggles: dict,
    runs_count: int,
    last_regen_run_index: int,
    regenerate_runtime_plan_fn: Callable[[str], dict],
    log_event_fn: Callable[..., None],
    planner_feedback: dict | None = None,
) -> int:
    if bool(toggles.get('freeze_plan_revision', False)):
        return last_regen_run_index
    if not bool(toggles.get('dynamic_plan_adaptation', True)) and not force:
        return last_regen_run_index
    min_gap = 2 if bool(toggles.get('aggressive_adaptation', False)) else 5
    feedback = planner_feedback if isinstance(planner_feedback, dict) else {}
    stage_hints = [str(x or '').strip().lower() for x in (feedback.get('recent_next_stage_hints') or []) if str(x or '').strip()]
    surface_hints = [str(x or '').strip().lower() for x in (feedback.get('recent_target_surface_rationale') or []) if str(x or '').strip()]
    if 'exploitation' in str(reason or '').lower() or int(feedback.get('exploitation_hosts', 0) or 0) > 0:
        min_gap = min(min_gap, 2)
    quality = adaptive_quality_context(feedback)
    if bool(quality.get('dead_end_heavy', False)):
        min_gap = max(min_gap, 6)
    elif bool(quality.get('quality_structural', False)):
        min_gap = min(min_gap, 3)
    if any(stage in {'bounded_exploit_proof', 'state_transition_confirmation'} for stage in stage_hints):
        min_gap = min(min_gap, 2)
    if any(sig in {'authenticated_or_boundary_mapping', 'artifact_capture'} for sig in surface_hints):
        min_gap = min(min_gap, 3)
    if not force and (runs_count - last_regen_run_index) < min_gap:
        return last_regen_run_index
    res = regenerate_runtime_plan_fn(reason)
    if res.get('ok'):
        last_regen_run_index = runs_count
        if res.get('skipped'):
            log_event_fn(
                'AUTO_CAMPAIGN',
                'plan_regen_skipped',
                'info',
                f"reason={reason};material_change=false;added={res.get('added_tasks')};deprecated={res.get('deprecated_tasks')};override={feedback.get('planner_override_recent',0)};partial={feedback.get('partial_recent',0)};stage_hints={','.join(stage_hints[:3])};surface_hints={','.join(surface_hints[:3])}",
                actor='auto_campaign',
                row_type='service',
            )
        else:
            log_event_fn(
                'AUTO_CAMPAIGN',
                'plan_regenerated',
                'in_progress',
                f"reason={reason};revision={res.get('plan_revision')};added={res.get('added_tasks')};deprecated={res.get('deprecated_tasks')};override={feedback.get('planner_override_recent',0)};partial={feedback.get('partial_recent',0)};adaptation_positive={feedback.get('adaptation_positive_recent',0)};reconsult_worthy={feedback.get('reconsult_worthy_recent',0)};exploitation_hosts={feedback.get('exploitation_hosts',0)};stage_hints={','.join(stage_hints[:3])};surface_hints={','.join(surface_hints[:3])}",
                actor='auto_campaign',
                row_type='service',
                highlight=True,
            )
    return last_regen_run_index


def reconcile_active_plan_if_needed(
    *,
    reason: str,
    curated_plan: list[dict],
    active_plan_revision: int,
    active_plan_hash: str,
    load_runtime_plan_meta_fn: Callable[[], dict],
    load_curated_plan_fn: Callable[[], list[dict]],
    dedup_key_fn: Callable[[str, str], tuple],
    reprioritize_queues_fn: Callable[[], None],
    log_event_fn: Callable[..., None],
    followup_queue_len: int,
    precision_queue_len: int,
) -> tuple[list[dict], int, str, bool]:
    try:
        latest_meta = load_runtime_plan_meta_fn()
        new_rev = int(latest_meta.get('plan_revision', 0) or 0)
        new_hash = str(latest_meta.get('plan_hash') or '')
        if new_rev <= active_plan_revision or (new_hash and new_hash == active_plan_hash):
            return curated_plan, active_plan_revision, active_plan_hash, False
        new_plan = load_curated_plan_fn()
        if not isinstance(new_plan, list) or not new_plan:
            return curated_plan, active_plan_revision, active_plan_hash, False
        old_keys = {dedup_key_fn(str(e.get('objective') or ''), str(e.get('target') or '')) for e in curated_plan if isinstance(e, dict)}
        new_keys = {dedup_key_fn(str(e.get('objective') or ''), str(e.get('target') or '')) for e in new_plan if isinstance(e, dict)}
        added = len(new_keys - old_keys)
        deprecated = len(old_keys - new_keys)
        reprioritize_queues_fn()
        log_event_fn(
            'AUTO_CAMPAIGN',
            'plan_reconciled',
            'in_progress',
            f'reason={reason};revision={new_rev};added={added};deprecated={deprecated};followup_q={followup_queue_len};precision_q={precision_queue_len}',
            actor='auto_campaign',
            row_type='service',
            highlight=True,
        )
        return new_plan, new_rev, new_hash, True
    except Exception as exc:
        log_event_fn('AUTO_CAMPAIGN', 'plan_reconcile_failed', 'warning', str(exc)[:220], actor='auto_campaign', row_type='service')
        return curated_plan, active_plan_revision, active_plan_hash, False
