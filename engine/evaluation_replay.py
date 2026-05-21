from __future__ import annotations

from typing import Any, Dict

from evaluation_bundle import validate_replay_bundle  # type: ignore
from runtime_effective_decision import branch_lifecycle, branch_thread_identity  # type: ignore
from runtime_plan_control import recon_to_exploit_synthesis  # type: ignore
from govengine_security_helpers import adaptation_feedback_status, finding_signal_status, success_outcome_status, workflow_promotion_status  # type: ignore


REPLAY_RESULT_SCHEMA_VERSION = 'phase5-replay-result-v1'
ACTION_PRIORITY = ('confirm', 'followup', 'precision', 'retry')


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_str(value: Any) -> str:
    return str(value or '').strip().lower()


def _pick_action(flags: Dict[str, Any] | None) -> str:
    flags = _safe_dict(flags)
    for action in ACTION_PRIORITY:
        if bool(flags.get(action, False)):
            return action
    return ''


def _flatten_blockers(value: Any) -> list[str]:
    blockers: list[str] = []
    raw = _safe_dict(value)
    for val in raw.values():
        if isinstance(val, list):
            blockers.extend([_safe_str(x) for x in val if _safe_str(x)])
        elif _safe_str(val):
            blockers.append(_safe_str(val))
    return blockers


def _runtime_stage(bundle: Dict[str, Any]) -> str:
    summary = _safe_dict(bundle.get('semantic_lineage_summary'))
    if _safe_str(summary.get('current_stage')):
        return _safe_str(summary.get('current_stage'))
    runtime_task = _safe_dict(bundle.get('runtime_task'))
    exploit_ladder = _safe_dict(runtime_task.get('exploit_ladder'))
    return _safe_str(exploit_ladder.get('stage'))


def _target_surface_flags(bundle: Dict[str, Any]) -> list[str]:
    summary = _safe_dict(bundle.get('semantic_lineage_summary'))
    return [_safe_str(x) for x in list(summary.get('target_surface_rationale') or []) if _safe_str(x)]


def _branch_metadata(bundle: Dict[str, Any]) -> tuple[str, str, str, float]:
    runtime_task = _safe_dict(bundle.get('runtime_task'))
    branch_state = _safe_str(runtime_task.get('branch_state'))
    branch_action = _safe_str(runtime_task.get('branch_action'))
    branch_reason = _safe_str(runtime_task.get('branch_reason'))
    try:
        branch_score = float(runtime_task.get('branch_evidence_score') or 0.0)
    except Exception:
        branch_score = 0.0
    return branch_state, branch_action, branch_reason, branch_score


def _looks_recon_like(bundle: Dict[str, Any], current_stage: str) -> bool:
    run_identity = _safe_dict(bundle.get('run_identity'))
    runtime_task = _safe_dict(bundle.get('runtime_task'))
    task_family = _safe_str(run_identity.get('task_family') or runtime_task.get('task_family'))
    target_surface = _target_surface_flags(bundle)
    return bool(
        task_family in {'recon', 'content_discovery', 'historical_url_mining', 'subdomain_expansion'}
        or current_stage == 'discovery'
        or any(sig in {'authenticated_or_boundary_mapping', 'artifact_capture', 'pivot_candidate'} for sig in target_surface)
    )


def _is_signal_bearing(candidate: bool, useful_negative: bool, exploit_proof: bool, finding_status: str) -> bool:
    return bool(candidate or useful_negative or exploit_proof or finding_status in {'weak', 'moderate', 'strong'})


def _is_policy_blocked(bundle: Dict[str, Any], signal_contract: Dict[str, Any]) -> bool:
    execution = _safe_dict(bundle.get('execution'))
    anomaly = _safe_dict(signal_contract.get('execution_anomaly'))
    return (
        _safe_str(anomaly.get('status')) == 'policy_block'
        or _safe_str(execution.get('engine_status')) == 'blocked'
        or _safe_str(execution.get('auditor_decision')) in {'reject', 'owner_approval_required'}
    )


def _has_owner_gate_pending(bundle: Dict[str, Any]) -> bool:
    execution = _safe_dict(bundle.get('execution'))
    return _safe_str(execution.get('auditor_decision')) == 'owner_approval_required' and not bool(execution.get('owner_override', False))


def _contamination_state(bundle: Dict[str, Any]) -> tuple[bool, list[str]]:
    governance = _safe_dict(bundle.get('governance'))
    contamination = _safe_dict(governance.get('run_contamination'))
    tags = [_safe_str(x) for x in list(contamination.get('tags') or []) if _safe_str(x)]
    status = _safe_str(contamination.get('status'))
    excluded = bool(contamination.get('learning_excluded', False)) or status in {'contaminated', 'mismatch'}
    return excluded, tags


def _auth_prereq_missing(bundle: Dict[str, Any], blockers: list[str]) -> bool:
    runtime_task = _safe_dict(bundle.get('runtime_task'))
    actor_requirements = _safe_dict(runtime_task.get('actor_requirements'))
    session_requirements = _safe_dict(runtime_task.get('session_requirements'))
    joined = ' '.join(blockers)
    if any(token in joined for token in ('auth', 'credential', 'cookie', 'token', 'login')):
        return True
    requires_auth = bool(actor_requirements.get('requires_auth', False)) or bool(session_requirements.get('requires_auth', False))
    if requires_auth:
        execution = _safe_dict(bundle.get('execution'))
        signal_contract = _safe_dict(bundle.get('signal_contract'))
        workflow_status = workflow_promotion_status(signal_contract)
        success_status = success_outcome_status(signal_contract)
        if _safe_str(execution.get('auditor_decision')) == 'owner_approval_required':
            return True
        if _safe_str(execution.get('engine_status')) == 'blocked' and not bool(execution.get('owner_approved_auth', False)):
            return True
        if not bool(execution.get('owner_approved_auth', False)) and workflow_status not in {'candidate', 'promotable', 'confirmable'} and success_status not in {'partial', 'met'}:
            return True
    return False


def _state_prereq_missing(bundle: Dict[str, Any], blockers: list[str]) -> bool:
    runtime_task = _safe_dict(bundle.get('runtime_task'))
    session_requirements = _safe_dict(runtime_task.get('session_requirements'))
    stage = _runtime_stage(bundle)
    joined = ' '.join(blockers)
    if any(token in joined for token in ('state', 'csrf', 'prereq', 'transition', 'session')):
        return True
    if stage in {'state_transition_confirmation', 'control_boundary_confirmation'} and bool(session_requirements):
        return bool(session_requirements.get('requires_state', False) or session_requirements.get('requires_transition', False))
    return False


def _finding_evidence_class(signal_contract: Dict[str, Any]) -> str:
    finding = _safe_dict(signal_contract.get('finding_signal'))
    evidence_class = _safe_str(finding.get('evidence_class'))
    if evidence_class:
        return evidence_class
    if _safe_str(finding.get('status')) in {'weak', 'moderate', 'strong'}:
        return 'evidence_bearing'
    return 'none'


def _is_useful_negative(policy_blocked: bool, finding_status: str, success_status: str, confirmed: bool) -> bool:
    return (not policy_blocked) and finding_status in {'none', 'weak'} and success_status in {'partial', 'met'} and not confirmed


def replay_decision_bundle(bundle: Dict[str, Any] | None, *, replay_mode: str = 'decision') -> Dict[str, Any]:
    normalized = validate_replay_bundle(bundle)
    runtime_decision = _safe_dict(normalized.get('runtime_decision'))
    signal_contract = _safe_dict(normalized.get('signal_contract'))
    execution = _safe_dict(normalized.get('execution'))
    lineage_summary = _safe_dict(normalized.get('semantic_lineage_summary'))

    stored_requested = _safe_str(runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action'))
    inferred_requested = _pick_action(runtime_decision.get('intent_flags'))
    requested_action = stored_requested or inferred_requested

    stored_effective = _safe_str(runtime_decision.get('effective_action'))
    inferred_effective = _pick_action(runtime_decision.get('effective_flags'))
    effective_action = stored_effective or inferred_effective

    divergence_reasons: list[str] = []
    missing_fields: list[str] = []
    if stored_requested and inferred_requested and stored_requested != inferred_requested:
        divergence_reasons.append(f'requested_action_mismatch:{stored_requested}!={inferred_requested}')
    if stored_effective and inferred_effective and stored_effective != inferred_effective:
        divergence_reasons.append(f'effective_action_mismatch:{stored_effective}!={inferred_effective}')
    if _safe_str(runtime_decision.get('effective_status')) == 'applied' and not effective_action:
        divergence_reasons.append('effective_status_applied_without_effective_action')
    if not _safe_str(lineage_summary.get('lineage_sha256')):
        missing_fields.append('semantic_lineage_summary.lineage_sha256')

    workflow_status = workflow_promotion_status(signal_contract)
    finding_status = finding_signal_status(signal_contract)
    success_status = success_outcome_status(signal_contract)
    adaptation_status = adaptation_feedback_status(signal_contract)
    policy_blocked = _is_policy_blocked(normalized, signal_contract)
    owner_gate_pending = _has_owner_gate_pending(normalized)
    contamination_excluded, contamination_tags = _contamination_state(normalized)
    blockers = _flatten_blockers(runtime_decision.get('effective_blockers'))
    auth_prereq_missing = _auth_prereq_missing(normalized, blockers)
    state_prereq_missing = _state_prereq_missing(normalized, blockers)
    confirmed = workflow_status == 'confirmable' or _safe_str(_safe_dict(signal_contract.get('workflow_promotion')).get('verdict')) == 'confirmed'
    evidence_class = _finding_evidence_class(signal_contract)
    semantic_outcome_class = 'blocked_evidence' if policy_blocked and evidence_class == 'blocked_evidence' else ('weak_evidence' if evidence_class == 'evidence_bearing' and finding_status == 'weak' else ('stronger_evidence' if evidence_class == 'evidence_bearing' else 'no_evidence'))
    candidate = workflow_status in {'candidate', 'promotable', 'confirmable'} or finding_status in {'weak', 'moderate', 'strong'}
    current_stage = _runtime_stage(normalized)
    report_artifact = current_stage == 'report_artifact_capture' and success_status in {'partial', 'met'}
    exploit_proof = current_stage in {'bounded_exploit_proof', 'report_artifact_capture'} and success_status in {'partial', 'met'}
    useful_negative = _is_useful_negative(policy_blocked, finding_status, success_status, confirmed)
    lineage_complete = bool(_safe_str(lineage_summary.get('lineage_sha256')))
    semantic_loss_class = _safe_str(execution.get('semantic_loss_class'))
    fallback_degraded = semantic_loss_class not in {'', 'none', 'exact'}
    repeat_probe_waste = effective_action == 'retry' and finding_status == 'none' and success_status in {'not_met', 'not_provided', ''}
    dead_branch_retry = repeat_probe_waste and adaptation_status == 'negative'
    auth_branch = bool(_safe_dict(_safe_dict(normalized.get('runtime_task')).get('actor_requirements'))) or normalized['run_identity'].get('task_family') in {'auth', 'authz', 'idor'}
    stateful_branch = bool(_safe_dict(_safe_dict(normalized.get('runtime_task')).get('session_requirements'))) or current_stage in {'state_transition_confirmation', 'bounded_exploit_proof', 'report_artifact_capture'}
    actor_asymmetry_branch = 'actor_asymmetry' in _target_surface_flags(normalized) or normalized['run_identity'].get('task_family') in {'authz', 'idor'}
    branch_completed = report_artifact or exploit_proof or useful_negative or success_status == 'met'
    branch_state, branch_action, branch_reason, branch_evidence_score = _branch_metadata(normalized)
    branch_candidate = branch_state == 'branch_candidate' or branch_action in {'confirm', 'deepen', 'pivot'} or branch_evidence_score >= 0.18
    branch_metadata = {
        'branch_state': branch_state,
        'branch_action': branch_action,
        'branch_reason': branch_reason,
        'branch_evidence_score': branch_evidence_score,
    }
    lifecycle = branch_lifecycle(
        branch_metadata=branch_metadata,
        signal_contract=signal_contract,
        success_status=success_status,
        engine_status=str(normalized.get('engine_status') or ''),
    )
    runtime_task = _safe_dict(normalized.get('runtime_task'))
    planning_ladder = _safe_dict(normalized.get('planning_ladder') or runtime_task.get('planning_ladder'))
    thread_identity = branch_thread_identity(
        family=str(normalized['run_identity'].get('task_family') or runtime_task.get('task_family') or ''),
        next_stage=str(planning_ladder.get('next_stage') or ''),
        branch_metadata=branch_metadata,
    )
    branch_lifecycle_status = str(lifecycle.get('branch_lifecycle_status') or '').strip().lower()
    branch_lifecycle_reason = str(lifecycle.get('branch_lifecycle_reason') or '').strip().lower()
    branch_lifecycle_confidence = float(lifecycle.get('branch_lifecycle_confidence') or 0.0)
    dead_end_branch = branch_lifecycle_status == 'dead_end' or (branch_candidate and not branch_completed and (dead_branch_retry or adaptation_status == 'negative' or success_status in {'not_met', 'not_provided', ''}))
    branch_quality_positive = branch_lifecycle_status == 'productive' or (branch_candidate and branch_completed and not policy_blocked and not contamination_excluded)
    recon_like = _looks_recon_like(normalized, current_stage)
    recon_to_exploit_candidate = recon_like and branch_candidate
    recon_to_exploit_success = recon_to_exploit_candidate and (exploit_proof or report_artifact or current_stage in {'bounded_exploit_proof', 'report_artifact_capture'})
    signal_bearing = _is_signal_bearing(candidate, useful_negative, exploit_proof, finding_status)
    confirmation_reached = confirmed or exploit_proof or report_artifact
    planner_rationale = _safe_dict(normalized.get('planner_rationale') or runtime_task.get('planner_rationale'))
    target_profile_summary = _safe_dict(planner_rationale.get('target_profile_summary'))
    synthesis = recon_to_exploit_synthesis(
        planner_feedback=_safe_dict(normalized.get('planner_feedback') or _safe_dict(normalized.get('result_context')).get('planner_feedback')),
        next_stage=str(planning_ladder.get('next_stage') or ''),
        target_type=str(target_profile_summary.get('target_type') or ''),
        target_surface_rationale=list(planner_rationale.get('target_surface_rationale') or []),
        current_family=str(normalized['run_identity'].get('task_family') or runtime_task.get('task_family') or ''),
    )
    synthesis_recommended_action = _safe_str(synthesis.get('recommended_branch_action'))
    synthesis_reason = _safe_str(synthesis.get('synthesis_reason'))
    synthesis_alignment = synthesis_recommended_action == branch_action or (synthesis_recommended_action == 'confirm' and effective_action == 'confirm') or (synthesis_recommended_action == 'deepen' and effective_action in {'followup', 'confirm'}) or (synthesis_recommended_action == 'pivot' and effective_action in {'followup', 'retry'})
    synthesis_positive = bool(synthesis_alignment and success_status in {'partial', 'met'})
    synthesis_pivot_avoidance = bool(synthesis_recommended_action == 'pivot' and not dead_end_branch)

    metric_exclusion_reasons: list[str] = []
    if policy_blocked:
        metric_exclusion_reasons.append('policy_blocked')
    if owner_gate_pending:
        metric_exclusion_reasons.append('owner_gate_pending')
    if contamination_excluded:
        metric_exclusion_reasons.append('contamination_excluded')

    status = 'ok'
    if missing_fields:
        status = 'partial'
    if divergence_reasons:
        status = 'divergent'

    return {
        'schema_version': REPLAY_RESULT_SCHEMA_VERSION,
        'replay_mode': _safe_str(replay_mode) or 'decision',
        'bundle_id': normalized.get('bundle_id'),
        'dataset_variant_id': _safe_str(_safe_dict(normalized.get('variant')).get('variant_id')),
        'status': status,
        'missing_fields': missing_fields,
        'divergence_reasons': divergence_reasons,
        'run_identity': normalized.get('run_identity'),
        'requested_action': requested_action,
        'effective_action': effective_action,
        'workflow_status': workflow_status,
        'finding_status': finding_status,
        'evidence_class': evidence_class,
        'semantic_outcome_class': semantic_outcome_class,
        'success_status': success_status,
        'adaptation_status': adaptation_status,
        'current_stage': current_stage,
        'candidate': candidate,
        'confirmed': confirmed,
        'exploit_proof': exploit_proof,
        'report_artifact': report_artifact,
        'useful_negative': useful_negative,
        'policy_blocked': policy_blocked,
        'owner_gate_pending': owner_gate_pending,
        'contamination_excluded': contamination_excluded,
        'contamination_tags': contamination_tags,
        'auth_prereq_missing': auth_prereq_missing,
        'state_prereq_missing': state_prereq_missing,
        'lineage_complete': lineage_complete,
        'fallback_degraded': fallback_degraded,
        'repeat_probe_waste': repeat_probe_waste,
        'dead_branch_retry': dead_branch_retry,
        'branch_completed': branch_completed,
        'branch_state': branch_state,
        'branch_action': branch_action,
        'branch_reason': branch_reason,
        'branch_evidence_score': round(branch_evidence_score, 3),
        'branch_lifecycle_status': branch_lifecycle_status,
        'branch_lifecycle_reason': branch_lifecycle_reason,
        'branch_lifecycle_confidence': round(branch_lifecycle_confidence, 3),
        'branch_thread_key': str(thread_identity.get('branch_thread_key') or ''),
        'branch_thread_label': str(thread_identity.get('branch_thread_label') or ''),
        'branch_candidate': branch_candidate,
        'dead_end_branch': dead_end_branch,
        'branch_quality_positive': branch_quality_positive,
        'recon_like': recon_like,
        'recon_to_exploit_candidate': recon_to_exploit_candidate,
        'recon_to_exploit_success': recon_to_exploit_success,
        'signal_bearing': signal_bearing,
        'confirmation_reached': confirmation_reached,
        'synthesis_recommended_action': synthesis_recommended_action,
        'synthesis_reason': synthesis_reason,
        'synthesis_alignment': synthesis_alignment,
        'synthesis_positive': synthesis_positive,
        'synthesis_pivot_avoidance': synthesis_pivot_avoidance,
        'auth_branch': auth_branch,
        'stateful_branch': stateful_branch,
        'actor_asymmetry_branch': actor_asymmetry_branch,
        'actor_asymmetry_success': actor_asymmetry_branch and (confirmed or exploit_proof),
        'request_count_estimate': int(_safe_dict(normalized.get('governance')).get('request_count_estimate') or 1),
        'metric_exclusion_reasons': metric_exclusion_reasons,
    }


def replay_dataset(dataset: Dict[str, Any] | None, *, replay_mode: str = 'decision') -> Dict[str, Any]:
    raw = _safe_dict(dataset)
    bundles = [item for item in list(raw.get('bundles') or []) if isinstance(item, dict)]
    results = [replay_decision_bundle(bundle, replay_mode=replay_mode) for bundle in bundles]
    status_counts = {'ok': 0, 'partial': 0, 'divergent': 0, 'invalid': 0}
    for item in results:
        status_counts[item['status']] = int(status_counts.get(item['status'], 0)) + 1
    return {
        'schema_version': 'phase5-replay-output-v1',
        'dataset_id': raw.get('dataset_id'),
        'run_id': raw.get('run_id'),
        'campaign_key': raw.get('campaign_key'),
        'variant': raw.get('variant'),
        'replay_mode': _safe_str(replay_mode) or 'decision',
        'bundle_count': len(results),
        'status_counts': status_counts,
        'results': results,
    }
