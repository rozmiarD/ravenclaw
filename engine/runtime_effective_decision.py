from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from learning_store import top_progression_hints, top_transition_action_hints
from govengine_security_helpers import success_outcome_status, workflow_promotion_status, signal_contract_workflow_promotable  # type: ignore
from runtime_decision_contracts import canonical_action_flags_from_mapping  # type: ignore


EffectiveDecision = dict[str, Any]
ACTIONS = ('retry', 'confirm', 'followup', 'precision')


def branch_thread_identity(*, family: str = '', next_stage: str = '', branch_metadata: dict | None = None) -> dict[str, str]:
    metadata = branch_metadata if isinstance(branch_metadata, dict) else {}
    family_l = str(family or '').strip().lower() or 'generic'
    next_stage_l = str(next_stage or '').strip().lower() or 'continuation'
    branch_action = str(metadata.get('branch_action') or '').strip().lower() or 'defer'
    branch_reason = str(metadata.get('branch_reason') or '').strip().lower() or 'generic_continuation'
    key = '::'.join([family_l, next_stage_l, branch_action, branch_reason])
    label = f"{family_l}:{next_stage_l}:{branch_action}"
    return {
        'branch_thread_key': key,
        'branch_thread_label': label,
    }


def branch_lifecycle(*, branch_metadata: dict | None = None, signal_contract: dict | None = None, success_status: str = '', engine_status: str = '') -> dict[str, Any]:
    metadata = branch_metadata if isinstance(branch_metadata, dict) else {}
    contract = signal_contract if isinstance(signal_contract, dict) else {}
    branch_state = str(metadata.get('branch_state') or '').strip().lower()
    branch_action = str(metadata.get('branch_action') or '').strip().lower()
    branch_reason = str(metadata.get('branch_reason') or '').strip().lower()
    branch_score = float(metadata.get('branch_evidence_score') or 0.0)
    success_l = str(success_status or success_outcome_status(contract) or '').strip().lower()
    engine_l = str(engine_status or '').strip().lower()
    adaptation = contract.get('adaptation_feedback') if isinstance(contract.get('adaptation_feedback'), dict) else {}
    workflow = contract.get('workflow_promotion') if isinstance(contract.get('workflow_promotion'), dict) else {}
    adaptation_status = str(adaptation.get('status') or '').strip().lower()
    workflow_status = str(workflow.get('status') or '').strip().lower()

    status = 'deferred'
    reason = branch_reason or 'generic_continuation'
    confidence = min(1.0, max(0.0, 0.28 + branch_score))

    if branch_state == 'branch_candidate' or branch_action in {'confirm', 'deepen', 'pivot'} or branch_score >= 0.18:
        status = 'open'
        reason = branch_reason or ('branch_candidate' if branch_state == 'branch_candidate' else 'branch_open')
        confidence = min(1.0, max(0.22, 0.4 + branch_score))

    if success_l in {'partial', 'met'} and engine_l not in {'failed', 'error', 'timeout'} and workflow_status in {'promotable', 'confirmable'}:
        status = 'productive'
        reason = 'bounded_progress_confirmed'
        confidence = min(1.0, max(0.55, 0.58 + branch_score))
    elif success_l == 'met' and engine_l not in {'failed', 'error', 'timeout'}:
        status = 'productive'
        reason = 'success_criteria_met'
        confidence = min(1.0, max(0.6, 0.62 + branch_score))
    elif adaptation_status == 'negative' or success_l in {'not_met', 'not_provided'} or engine_l in {'failed', 'error', 'timeout'}:
        if branch_state == 'branch_candidate' or branch_action in {'confirm', 'deepen', 'pivot'} or branch_score >= 0.18:
            status = 'dead_end'
            reason = 'negative_or_failed_branch_outcome'
            confidence = min(1.0, max(0.5, 0.56 + branch_score))
    elif branch_action == 'defer' or branch_reason in {'insufficient_branch_evidence', 'generic_continuation'}:
        status = 'deferred'
        reason = branch_reason or 'insufficient_branch_evidence'
        confidence = min(1.0, max(0.22, 0.3 + branch_score))

    return {
        'branch_lifecycle_status': status,
        'branch_lifecycle_reason': reason,
        'branch_lifecycle_confidence': round(confidence, 3),
    }


def _normalize_flags(payload: dict | None) -> dict[str, bool]:
    src = payload if isinstance(payload, dict) else {}
    return {key: bool(src.get(key, False)) for key in ACTIONS}


def _canonical_post_decision(
    *,
    runtime_decision: dict,
    fallback_flags_fn: Callable[[], dict[str, bool]],
) -> dict[str, bool]:
    flags, source = canonical_action_flags_from_mapping(runtime_decision)
    if source != 'fallback':
        return _normalize_flags(flags)
    return _normalize_flags(fallback_flags_fn())


def _queue_priority(runtime_decision: dict, task: dict, *, fallback: float = 1.0) -> tuple[float, float]:
    eco = runtime_decision.get('economics') if isinstance(runtime_decision.get('economics'), dict) else {}
    explain = runtime_decision.get('explain') if isinstance(runtime_decision.get('explain'), dict) else {}
    priority = float(eco.get('priority_score', task.get('priority_score', fallback)) or fallback)
    utility = float(task.get('utility_score', explain.get('net_utility_score', priority)) or priority)
    return priority, utility


def _signal_evidence_bearing(signal_contract: dict) -> bool:
    finding = signal_contract.get('finding_signal') if isinstance(signal_contract.get('finding_signal'), dict) else {}
    return bool(finding.get('evidence_bearing', False))


def _evidence_bearing_followup_allowed(*, toggles: dict, signal_contract: dict, qual: dict, engine_status: str, success_status: str, workflow_promotable: bool) -> bool:
    if not bool(toggles.get('evidence_bearing_followup_bridge', True)):
        return False
    if str(success_status or '').lower() == 'partial':
        return False
    finding = signal_contract.get('finding_signal') if isinstance(signal_contract.get('finding_signal'), dict) else {}
    finding_status = str(finding.get('status') or '').strip().lower()
    return bool(
        signal_contract
        and workflow_promotable
        and _signal_evidence_bearing(signal_contract)
        and finding_status in {'weak', 'moderate', 'strong'}
        and bool((qual or {}).get('false_positive_guards_passed', False))
        and str(engine_status or '').strip().lower() not in {'failed', 'error', 'timeout'}
    )


def _dedupe_keep_order(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        norm = str(item or '').strip().lower()
        if not norm or norm in seen:
            continue
        out.append(norm)
        seen.add(norm)
    return out


def _evidence_family_lane(*, task_family: str, success_semantics: dict) -> str:
    fam = str(task_family or '').strip().lower()
    typed = str((success_semantics or {}).get('typed_family_eval') or '').strip().lower()
    success_model = str((success_semantics or {}).get('success_model') or '').strip().lower()
    if typed in {'authz_boundary', 'inventory_growth', 'input_validation'}:
        return typed
    if success_model == 'fingerprint_or_exposure_signal':
        return 'exposure_or_fingerprint'
    if fam in {'authz', 'idor', 'auth_flow', 'workflow', 'logic', 'state_transition', 'redirect_trust', 'session'}:
        return 'authz_boundary'
    if fam in {'input_tamper', 'client_input', 'xss', 'sqli', 'ssti', 'ssrf', 'graphql', 'cors'}:
        return 'input_validation'
    if fam in {'recon', 'content_discovery', 'historical_url_mining', 'subdomain_expansion'}:
        return 'inventory_growth'
    if fam in {'tls_assessment', 'secret_hunt', 'headers', 'transport_tls'}:
        return 'exposure_or_fingerprint'
    return 'generic'


def _evidence_gap_hints(*, task_family: str, success_semantics: dict, gap: str, mode: str, evidence_required: list[str], acceptance_checks: list[str]) -> list[str]:
    lane = _evidence_family_lane(task_family=task_family, success_semantics=success_semantics)
    gap_l = str(gap or '').strip().lower()
    required = {str(x).strip().lower() for x in (evidence_required or []) if str(x).strip()}
    checks = {str(x).strip().lower() for x in (acceptance_checks or []) if str(x).strip()}

    if lane == 'authz_boundary':
        if gap_l in {'missing_success_criteria', 'need_stronger_repro_or_impact_evidence'}:
            base = ['differential_probe', 'state_transition_probe', 'confirmatory_probe']
        elif gap_l in {'need_clear_allow_deny_or_boundary_evidence', 'no_authz_boundary_evidence'}:
            base = ['state_transition_probe', 'differential_probe', 'confirmatory_probe']
        else:
            base = ['differential_probe', 'confirmatory_probe', 'state_transition_probe']
    elif lane == 'inventory_growth':
        if gap_l in {'missing_success_criteria', 'no_inventory_growth_evidence'}:
            base = ['enumeration_probe', 'fingerprint_probe', 'confirmatory_probe']
        else:
            base = ['fingerprint_probe', 'enumeration_probe', 'confirmatory_probe']
    elif lane == 'input_validation':
        if gap_l in {'missing_success_criteria', 'need_stronger_repro_or_impact_evidence'}:
            base = ['variant_probe', 'differential_probe', 'confirmatory_probe']
        elif gap_l in {'need_clear_input_or_trust_boundary_evidence', 'no_input_validation_evidence'}:
            base = ['differential_probe', 'variant_probe', 'confirmatory_probe']
        else:
            base = ['variant_probe', 'confirmatory_probe', 'differential_probe']
    elif lane == 'exposure_or_fingerprint':
        base = ['fingerprint_probe', 'confirmatory_probe', 'enumeration_probe']
    else:
        base = ['differential_probe', 'confirmatory_probe'] if mode == 'precision' else ['confirmatory_probe', 'differential_probe']

    if 'endpoint_or_header_inventory' in required and 'enumeration_probe' in base:
        base = ['enumeration_probe'] + [x for x in base if x != 'enumeration_probe']
    if 'response_diff' in required and 'differential_probe' in base:
        base = ['differential_probe'] + [x for x in base if x != 'differential_probe']
    if 'reflection_or_behavior_delta' in required:
        prefer = 'variant_probe' if 'variant_probe' in base else ('differential_probe' if 'differential_probe' in base else '')
        if prefer:
            base = [prefer] + [x for x in base if x != prefer]
    if 'negative_control' in checks and 'confirmatory_probe' in base:
        base = [base[0]] + ['confirmatory_probe'] + [x for x in base[1:] if x != 'confirmatory_probe']
    if mode == 'precision' and 'state_transition_probe' in base:
        base = ['state_transition_probe'] + [x for x in base if x != 'state_transition_probe']
    return _dedupe_keep_order(base)


def _family_evidence_focus(*, task_family: str, exploit_ladder: dict, evidence_goal: str, session_requirements: dict, actor_requirements: dict, open_questions: list[str], planning_ladder: dict | None = None, planner_rationale: dict | None = None) -> list[str]:
    fam = str(task_family or '').strip().lower()
    stage = str((exploit_ladder or {}).get('stage') or '').strip().lower()
    goal = str(evidence_goal or '').strip().lower()
    focus: list[str] = []

    if fam in {'authz', 'idor'} or bool((actor_requirements or {}).get('differential')) or goal == 'controlled_comparison':
        focus += ['actor_boundary_delta', 'negative_control', 'identifier_rebind_check']
    elif fam in {'workflow', 'logic', 'state_transition', 'auth_flow'} or stage in {'state_transition_confirmation', 'bounded_exploit_proof'}:
        focus += ['state_transition_artifact', 'state_marker_capture', 'transition_guard']
    elif fam in {'recon', 'content_discovery', 'historical_url_mining', 'subdomain_expansion'} or goal in {'surface_expansion', 'endpoint_or_header_inventory', 'novel_endpoint_or_asset'} or stage == 'discovery':
        focus += ['inventory_growth', 'novel_surface', 'pivot_candidate']
    elif fam in {'tls_assessment', 'secret_hunt', 'headers', 'transport_tls'}:
        focus += ['exposure_artifact', 'fingerprint_confirmation']
    else:
        focus += ['repro_signal', 'confirmatory_probe']

    planning_ladder = dict(planning_ladder or {}) if isinstance(planning_ladder, dict) else {}
    planner_rationale = dict(planner_rationale or {}) if isinstance(planner_rationale, dict) else {}
    target_profile_summary = dict(planner_rationale.get('target_profile_summary') or {}) if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
    target_type = str(target_profile_summary.get('target_type') or '').strip().lower()
    target_surface = [str(x or '').strip().lower() for x in ((planner_rationale.get('planner_preferences') or {}).get('surface_keywords') or [])] if isinstance(planner_rationale.get('planner_preferences'), dict) else []
    next_stage = str(planning_ladder.get('next_stage') or '').strip().lower()
    if bool((session_requirements or {}).get('stateful')):
        focus.append('stateful_session_context')
    if bool((session_requirements or {}).get('auth_context')):
        focus.append('auth_context_confirmation')
    if target_type in {'api', 'auth', 'integration'}:
        focus.append('authenticated_or_boundary_mapping')
    elif target_type in {'static', 'support'}:
        focus.append('artifact_capture')
    if next_stage:
        focus.append(f'next_stage:{next_stage}')
    focus.extend([x for x in target_surface if x in {'admin', 'billing', 'tenant', 'organization', 'api', 'auth', 'account'}])
    for item in open_questions or []:
        q = str(item or '').strip().lower()
        if q:
            focus.append(f'open_question:{q}')
    return _dedupe_keep_order(focus)


def _branch_synthesis(*, task: dict, runtime_task: dict, signal_contract: dict, next_task_family: str, mode: str) -> dict[str, Any]:
    planner_rationale = dict(task.get('planner_rationale') or runtime_task.get('planner_rationale') or {})
    planning_ladder = dict(task.get('planning_ladder') or runtime_task.get('planning_ladder') or planner_rationale.get('planning_ladder') or {})
    exploit_ladder = dict(task.get('exploit_ladder') or runtime_task.get('exploit_ladder') or {})
    success_semantics = dict(task.get('success_semantics') or runtime_task.get('success_semantics') or {})
    outcome = signal_contract.get('success_outcome') if isinstance(signal_contract.get('success_outcome'), dict) else {}
    workflow = signal_contract.get('workflow_promotion') if isinstance(signal_contract.get('workflow_promotion'), dict) else {}
    gap = str(success_semantics.get('success_gap') or outcome.get('gap') or '').strip().lower()
    stage = str(exploit_ladder.get('stage') or planning_ladder.get('current_stage') or '').strip().lower()
    next_stage = str(planning_ladder.get('next_stage') or '').strip().lower()
    target_profile = planner_rationale.get('target_profile_summary') if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
    target_type = str(target_profile.get('target_type') or '').strip().lower()
    target_surface = [str(x or '').strip().lower() for x in (planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()]
    host = str(task.get('host') or '').strip().lower()
    if not host:
        target = str(task.get('target') or runtime_task.get('target') or '').strip().lower()
        host = target.split('//', 1)[-1].split('/', 1)[0].strip().lower()
    progression_hints = top_progression_hints(
        family=str(next_task_family or ''),
        target_type=target_type,
        target_surface_signal=str(target_surface[0] if target_surface else ''),
        next_stage=next_stage,
        host=host,
        limit=2,
    )
    evidence_score = 0.0
    evidence_signals: list[str] = []
    branch_action = 'defer'
    branch_state = 'continuation'
    branch_reason = 'generic_continuation'
    if str((workflow or {}).get('status') or '').strip().lower() in {'promotable', 'confirmable'}:
        evidence_score += 0.18
        evidence_signals.append('workflow_promotable')
    if gap in {'missing_success_criteria', 'need_stronger_repro_or_impact_evidence', 'need_clear_allow_deny_or_boundary_evidence'}:
        evidence_score += 0.22
        evidence_signals.append(f'evidence_gap:{gap}')
    if next_stage in {'control_boundary_confirmation', 'state_transition_confirmation', 'bounded_exploit_proof'}:
        evidence_score += 0.2
        evidence_signals.append(f'next_stage:{next_stage}')
    if 'authenticated_or_boundary_mapping' in target_surface:
        evidence_score += 0.18
        evidence_signals.append('surface:authenticated_or_boundary_mapping')
    if 'artifact_capture' in target_surface:
        evidence_score += 0.14
        evidence_signals.append('surface:artifact_capture')
    for hint in progression_hints:
        hint_action = str(hint.get('next_family') or '').strip().lower()
        if hint_action:
            evidence_score += min(0.16, float(hint.get('score', 0.0) or 0.0) * 0.08)
            evidence_signals.append(f'progression_hint:{hint_action}')
    if next_stage == 'bounded_exploit_proof' or stage == 'bounded_exploit_proof':
        branch_action = 'deepen'
        branch_state = 'branch_candidate'
        branch_reason = 'proof_path_ready'
        evidence_score += 0.24
    elif gap in {'need_clear_allow_deny_or_boundary_evidence', 'missing_success_criteria'}:
        branch_action = 'confirm'
        branch_state = 'branch_candidate'
        branch_reason = 'confirmation_gap'
    elif next_task_family and next_task_family != str(task.get('task_family') or runtime_task.get('task_family') or '').strip().lower():
        branch_action = 'pivot'
        branch_state = 'branch_candidate'
        branch_reason = 'family_pivot_opportunity'
        evidence_score += 0.08
    elif stage == 'discovery' and target_type in {'api', 'auth', 'integration'}:
        branch_action = 'deepen'
        branch_state = 'branch_candidate'
        branch_reason = 'recon_to_exploit_synthesis'
        evidence_score += 0.12
    if evidence_score < 0.18:
        branch_state = 'continuation'
        branch_action = 'defer'
        branch_reason = 'insufficient_branch_evidence'
    return {
        'branch_state': branch_state,
        'branch_action': branch_action,
        'branch_reason': branch_reason,
        'branch_evidence_score': round(min(1.0, evidence_score), 3),
        'branch_evidence_signals': evidence_signals[:5],
    }



def _augment_followup_guidance(*, task: dict, runtime_task: dict, signal_contract: dict, next_task_family: str, mode: str) -> tuple[list[str], list[str], dict[str, Any], str, dict[str, Any]]:
    existing_actions = list(task.get('recommended_action_types') or runtime_task.get('recommended_action_types') or [])
    open_questions = list(task.get('open_questions') or runtime_task.get('open_questions') or [])
    planner_preferences = dict(task.get('planner_preferences') or runtime_task.get('planner_preferences') or {})
    success_semantics = dict(task.get('success_semantics') or runtime_task.get('success_semantics') or {})
    outcome = signal_contract.get('success_outcome') if isinstance(signal_contract.get('success_outcome'), dict) else {}
    gap = str(success_semantics.get('success_gap') or outcome.get('gap') or '').strip()
    typed_family_eval = str(success_semantics.get('typed_family_eval') or outcome.get('typed_family_eval') or '').strip().lower()
    if typed_family_eval and 'typed_family_eval' not in success_semantics:
        success_semantics = dict(success_semantics)
        success_semantics['typed_family_eval'] = typed_family_eval
    evidence_required = list(success_semantics.get('evidence_required_eval') or success_semantics.get('evidence_required') or [])
    acceptance_checks = list(success_semantics.get('acceptance_checks_eval') or success_semantics.get('acceptance_checks') or [])
    guided_actions = _evidence_gap_hints(
        task_family=next_task_family,
        success_semantics=success_semantics,
        gap=gap,
        mode=mode,
        evidence_required=evidence_required,
        acceptance_checks=acceptance_checks,
    )
    task_planning_ladder = dict(task.get('planning_ladder') or runtime_task.get('planning_ladder') or {})
    task_host = str(task.get('host') or '').strip().lower()
    if not task_host:
        target = str(task.get('target') or runtime_task.get('target') or '').strip().lower()
        task_host = target.split('//', 1)[-1].split('/', 1)[0].strip().lower()
    transition_hints = top_transition_action_hints(
        family=next_task_family,
        capability=str(task.get('capability') or runtime_task.get('capability') or ''),
        action_type=str(task.get('action_type') or runtime_task.get('action_type') or (existing_actions[0] if existing_actions else '')),
        next_stage=str(task_planning_ladder.get('next_stage') or ''),
        host=task_host,
        limit=2,
    )
    prior_actions = [str(item.get('next_action_type') or '').strip().lower() for item in transition_hints if str(item.get('next_action_type') or '').strip()]
    merged_actions = _dedupe_keep_order(prior_actions + guided_actions + existing_actions)
    lane = _evidence_family_lane(task_family=next_task_family, success_semantics=success_semantics)
    if gap:
        open_questions = _dedupe_keep_order(open_questions + [f'evidence_gap:{gap}', f'evidence_lane:{lane}'])
        planner_preferences = dict(planner_preferences)
        planner_preferences['evidence_gap_priority'] = gap
        planner_preferences['evidence_lane'] = lane
        planner_preferences['followup_strategy'] = 'evidence_gap_first'
    if transition_hints:
        planner_preferences = dict(planner_preferences)
        planner_preferences['transition_prior_strategy'] = 'learning_store_transition_memory'
        planner_preferences['transition_prior_actions'] = prior_actions[:2]
    branch_metadata = _branch_synthesis(
        task=task,
        runtime_task=runtime_task,
        signal_contract=signal_contract,
        next_task_family=next_task_family,
        mode=mode,
    )
    lifecycle = branch_lifecycle(branch_metadata=branch_metadata, signal_contract=signal_contract)
    thread_identity = branch_thread_identity(
        family=str(next_task_family or task.get('task_family') or runtime_task.get('task_family') or ''),
        next_stage=str(task_planning_ladder.get('next_stage') or ''),
        branch_metadata=branch_metadata,
    )
    branch_metadata = dict(branch_metadata)
    branch_metadata.update(lifecycle)
    branch_metadata.update(thread_identity)
    planner_preferences = dict(planner_preferences)
    planner_preferences['branch_state'] = str(branch_metadata.get('branch_state') or '')
    planner_preferences['branch_action'] = str(branch_metadata.get('branch_action') or '')
    planner_preferences['branch_lifecycle_status'] = str(branch_metadata.get('branch_lifecycle_status') or '')
    planner_preferences['branch_thread_key'] = str(branch_metadata.get('branch_thread_key') or '')
    return merged_actions, open_questions, planner_preferences, gap, branch_metadata


def apply_effective_decision(
    *,
    task: dict,
    result: dict,
    qual: dict,
    classification: str,
    auditor: str,
    engine_status: str,
    success_eval_status: str,
    summary_text: str,
    reason_code: str,
    target: str,
    objective: str,
    aggression: int,
    owner_auth: bool,
    owner_override: bool,
    retry_counts: dict,
    retry_limit: int,
    followup_queue: list,
    followup_counts: dict,
    followup_recent: dict,
    max_followups_per_target: int,
    scheduled_keys: set,
    host_weak_count: dict,
    host_family_owner_gate: dict,
    confirm_counts: dict,
    confirm_recent: dict,
    confirm_total: int,
    confirm_class_counts: dict,
    max_confirm_jobs_per_target: int,
    max_confirm_jobs_total: int,
    max_confirm_jobs_per_class: int,
    confirm_job_cooldown_sec: int,
    quality_telemetry: dict,
    toggles: dict,
    promising: bool,
    signal_contract: dict | None,
    runtime_decision: dict | None,
    dedup_key_fn: Callable[[str, str], tuple],
    attack_family_fn: Callable[[str, str, str], str],
    host_from_target_fn: Callable[[str], str],
    next_followup_family_fn: Callable[[str, dict | None], str],
    clamp_aggression_fn: Callable[[int], int],
    capped_aggression_fn: Callable[[str, str, int], int],
    adaptive_aggression_fn: Callable[[int, str, str, bool], int],
    enqueue_followup_task_fn: Callable[[dict, bool], None],
    post_run_decision_fn: Callable[..., dict[str, bool]],
    log_event_fn: Callable[..., None],
) -> tuple[int, EffectiveDecision]:
    target_key = target.strip().lower()
    rk = dedup_key_fn(objective, target)
    runtime_decision = runtime_decision if isinstance(runtime_decision, dict) else {}
    signal_contract = signal_contract if isinstance(signal_contract, dict) else {}
    workflow_status = workflow_promotion_status(signal_contract)
    workflow_promotable = signal_contract_workflow_promotable(signal_contract) if signal_contract else bool(promising)
    success_status = success_outcome_status(signal_contract) or str(success_eval_status or '')
    evidence_bearing_followup_allowed = _evidence_bearing_followup_allowed(
        toggles=toggles,
        signal_contract=signal_contract,
        qual=qual,
        engine_status=engine_status,
        success_status=success_status,
        workflow_promotable=workflow_promotable,
    )
    runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    task_capability_candidates = list(task.get('capability_candidates') or runtime_task.get('capability_candidates') or [])
    task_recommended_action_types = list(task.get('recommended_action_types') or runtime_task.get('recommended_action_types') or [])
    task_hypothesis_candidates = list(task.get('hypothesis_candidates') or runtime_task.get('hypothesis_candidates') or [])
    task_planner_constraints = dict(task.get('planner_constraints') or runtime_task.get('planner_constraints') or {})
    task_planner_preferences = dict(task.get('planner_preferences') or runtime_task.get('planner_preferences') or {})
    task_planner_rationale = dict(task.get('planner_rationale') or runtime_task.get('planner_rationale') or {})
    task_planning_ladder = dict(task.get('planning_ladder') or runtime_task.get('planning_ladder') or task_planner_rationale.get('planning_ladder') or {})
    task_open_questions = list(task.get('open_questions') or runtime_task.get('open_questions') or [])
    task_success_semantics = dict(task.get('success_semantics') or runtime_task.get('success_semantics') or {})
    task_experiment_intent_id = str(task.get('experiment_intent_id') or runtime_task.get('experiment_intent_id') or '')
    task_exploit_ladder = dict(task.get('exploit_ladder') or runtime_task.get('exploit_ladder') or {})
    task_actor_requirements = dict(task.get('actor_requirements') or runtime_task.get('actor_requirements') or {})
    task_session_requirements = dict(task.get('session_requirements') or runtime_task.get('session_requirements') or {})
    task_promotion_policy = dict(task.get('promotion_policy') or runtime_task.get('promotion_policy') or {})
    task_contamination_policy = dict(task.get('contamination_policy') or runtime_task.get('contamination_policy') or {})
    task_approval_sensitivity = dict(task.get('approval_sensitivity') or runtime_task.get('approval_sensitivity') or {})
    task_action_type = str(task.get('action_type') or runtime_task.get('action_type') or '')
    task_capability = str(task.get('capability') or runtime_task.get('capability') or '')
    task_experiment_shape = str(task.get('experiment_shape') or runtime_task.get('experiment_shape') or '')
    task_evidence_goal = str(task.get('evidence_goal') or runtime_task.get('evidence_goal') or '')
    task_prerequisites = [str(x or '').strip().lower() for x in (task_session_requirements.get('prerequisites') or []) if str(x or '').strip()]
    task_open_questions_lower = [str(x or '').strip().lower() for x in task_open_questions if str(x or '').strip()]
    precondition_gaps = [p for p in task_prerequisites if any(p in q or q in p for q in task_open_questions_lower)]
    actor_keywords = ('identity', 'identities', 'role', 'roles', 'actor', 'account', 'comparison')
    actor_state_gaps = [q for q in task_open_questions_lower if any(k in q for k in actor_keywords)]
    actor_state_blocking = bool(task_actor_requirements.get('required') and actor_state_gaps and (bool(task_actor_requirements.get('differential')) or bool(task_session_requirements.get('auth_context'))))
    evidence_focus = _family_evidence_focus(
        task_family=task.get('task_family') or runtime_task.get('task_family') or '',
        exploit_ladder=task_exploit_ladder,
        evidence_goal=task_evidence_goal,
        session_requirements=task_session_requirements,
        actor_requirements=task_actor_requirements,
        open_questions=list(dict.fromkeys(task_open_questions + precondition_gaps))[:8],
        planning_ladder=task_planning_ladder,
        planner_rationale=task_planner_rationale,
    )
    precondition_blocking = bool(task_session_requirements.get('stateful') and precondition_gaps and str(task_exploit_ladder.get('stage') or '').strip().lower() in {'state_transition_confirmation', 'bounded_exploit_proof'})
    post_decision = _canonical_post_decision(
        runtime_decision=runtime_decision,
        fallback_flags_fn=lambda: post_run_decision_fn(
            task,
            result if isinstance(result, dict) else {},
            qual,
            classification,
            auditor,
            engine_status,
            success_eval_status,
            toggles,
            mode=str(task.get('mode') or ''),
        ),
    )
    fam_gate = attack_family_fn(objective, target, str(task.get('task_family') or ''))
    if host_family_owner_gate.get((host_from_target_fn(target), fam_gate), 0) >= 2 and auditor == 'owner_approval_required':
        post_decision['followup'] = False
        post_decision['confirm'] = False
    code000 = ('__rc_metrics__ code=000' in (summary_text or '').lower() or 'code=000' in (summary_text or '').lower())
    eff_retry_limit = min(retry_limit, 1) if code000 else retry_limit
    family_hint_result = dict(result or {}) if isinstance(result, dict) else {}
    family_hint_result.setdefault('planning_ladder', dict(task_planning_ladder))
    family_hint_result.setdefault('planner_rationale', dict(task_planner_rationale))
    family_hint_runtime_task = family_hint_result.get('runtime_task') if isinstance(family_hint_result.get('runtime_task'), dict) else {}
    family_hint_runtime_task = dict(family_hint_runtime_task)
    family_hint_runtime_task.setdefault('planning_ladder', dict(task_planning_ladder))
    family_hint_runtime_task.setdefault('planner_rationale', dict(task_planner_rationale))
    family_hint_result['runtime_task'] = family_hint_runtime_task
    next_task_family = next_followup_family_fn(str(task.get('task_family') or ''), family_hint_result)
    guided_actions_followup, guided_questions_followup, guided_preferences_followup, evidence_gap, branch_followup = _augment_followup_guidance(
        task=task,
        runtime_task=runtime_task,
        signal_contract=signal_contract,
        next_task_family=next_task_family,
        mode='followup',
    )
    guided_actions_precision, guided_questions_precision, guided_preferences_precision, precision_gap, branch_precision = _augment_followup_guidance(
        task=task,
        runtime_task=runtime_task,
        signal_contract=signal_contract,
        next_task_family=next_task_family,
        mode='precision',
    )
    confirm_total_local = int(confirm_total or 0)
    priority_score, utility_score = _queue_priority(runtime_decision, task)
    policy_followup_allowed = bool(task_promotion_policy.get('followup_allowed', True))

    effective_flags = {key: False for key in ACTIONS}
    effective_reasons: dict[str, str] = {}
    effective_blockers: dict[str, list[str]] = {key: [] for key in ACTIONS}

    def _block(action: str, reason: str) -> None:
        effective_blockers.setdefault(action, []).append(reason)

    def _mark(action: str, reason: str) -> None:
        effective_flags[action] = True
        effective_reasons[action] = reason

    if post_decision.get('retry'):
        if retry_counts.get(rk, 0) >= eff_retry_limit:
            _block('retry', 'retry_limit_reached')
        else:
            retry_counts[rk] = retry_counts.get(rk, 0) + 1
            followup_queue.append({
                'objective': objective,
                'target': target,
                'aggression': aggression,
                'mode': f"retry_{retry_counts[rk]}",
                'owner_approved_auth': owner_auth,
                'owner_override': owner_override,
                'task_family': next_task_family,
                'priority_score': priority_score,
                'utility_score': utility_score,
                'campaign_success_criteria': str(task.get('campaign_success_criteria') or ''),
                'task_success_criteria': str(task.get('task_success_criteria') or ''),
                'acceptance_checks': list(task.get('acceptance_checks') or []),
                'evidence_required': list(task.get('evidence_required') or []),
                'success_semantics': dict(task_success_semantics),
                'experiment_intent_id': task_experiment_intent_id,
                'capability_candidates': list(task_capability_candidates),
                'recommended_action_types': list(task_recommended_action_types),
                'hypothesis_candidates': list(task_hypothesis_candidates),
                'planner_constraints': dict(task_planner_constraints),
                'planner_preferences': dict(task_planner_preferences),
                'planner_rationale': dict(task_planner_rationale),
                'planning_ladder': dict(task_planning_ladder),
                'target_surface_rationale': [str(x or '').strip().lower() for x in (task_planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()],
                'open_questions': list(task_open_questions),
                'name': f"Retry {retry_counts[rk]}: {task.get('name') or objective}",
            })
            _mark('retry', f"retry_{retry_counts[rk]}_queued")
            log_event_fn('AUTO_CAMPAIGN', 'retry_requeue', 'warning', f"Queued retry_{retry_counts[rk]} for target={target}", actor='auto_campaign', highlight=True)

    queued_confirm = False
    queued_followup = False
    requested_secondary_action = str(runtime_decision.get('selected_secondary_action') or '').strip().lower()

    if post_decision.get('confirm'):
        if precondition_blocking:
            _block('confirm', 'preconditions_unresolved')
        elif actor_state_blocking:
            _block('confirm', 'actor_state_unresolved')
        elif confirm_counts.get(target_key, 0) >= max_confirm_jobs_per_target:
            _block('confirm', 'confirm_cap_per_target')
        elif int(confirm_total_local) >= max_confirm_jobs_total:
            _block('confirm', 'confirm_cap_total')
        else:
            now_ts = datetime.now(timezone.utc).timestamp()
            if now_ts - float(confirm_recent.get(target_key, 0.0) or 0.0) < float(confirm_job_cooldown_sec):
                _block('confirm', 'confirm_cooldown_active')
            else:
                vclass = str(qual.get('vuln_class') or 'generic')
                if int(confirm_class_counts.get(vclass, 0)) >= max_confirm_jobs_per_class:
                    _block('confirm', 'confirm_cap_per_class')
                else:
                    confirm_objective = f"{objective} [CONFIRM:{vclass}]"
                    keyc = dedup_key_fn(confirm_objective, target)
                    if keyc in scheduled_keys:
                        _block('confirm', 'confirm_duplicate_suppressed')
                    else:
                        scheduled_keys.add(keyc)
                        enqueue_followup_task_fn({
                            'objective': confirm_objective,
                            'target': target,
                            'aggression': clamp_aggression_fn(max(int(aggression), 3)),
                            'mode': 'confirm',
                            'owner_approved_auth': owner_auth,
                            'owner_override': owner_override,
                            'priority_score': priority_score,
                            'utility_score': utility_score,
                            'exploit_ladder': dict(task_exploit_ladder),
                            'actor_requirements': dict(task_actor_requirements),
                            'session_requirements': dict(task_session_requirements),
                            'promotion_policy': dict(task_promotion_policy),
                            'contamination_policy': dict(task_contamination_policy),
                            'approval_sensitivity': dict(task_approval_sensitivity),
                            'action_type': task_action_type,
                            'capability': task_capability,
                            'experiment_shape': task_experiment_shape,
                            'evidence_goal': task_evidence_goal,
                            'name': f"Confirm: {task.get('name') or objective}",
                        }, True)
                        confirm_recent[target_key] = now_ts
                        confirm_counts[target_key] = confirm_counts.get(target_key, 0) + 1
                        confirm_total_local += 1
                        queued_confirm = True
                        confirm_class_counts[vclass] = int(confirm_class_counts.get(vclass, 0)) + 1
                        quality_telemetry['confirm_queued'] = int(quality_telemetry.get('confirm_queued', 0)) + 1
                        _mark('confirm', 'confirm_job_queued')
                        log_event_fn('AUTO_CAMPAIGN', 'confirm_job_queued', 'in_progress', f"target={target};verdict=probable;vuln_class={qual.get('vuln_class')}", actor='auto_campaign', row_type='service', highlight=True)

    if post_decision.get('followup'):
        if queued_confirm:
            if requested_secondary_action == 'followup':
                _mark('followup', 'dual_action_followup_attached')
            else:
                _block('followup', 'confirm_precedence')
        elif not policy_followup_allowed:
            _block('followup', 'followup_policy_disabled')
        elif not workflow_promotable:
            _block('followup', f'workflow_not_promotable:{workflow_status or "none"}')
        elif followup_counts.get(target_key, 0) >= max_followups_per_target:
            _block('followup', 'followup_cap_per_target')
        elif str(success_status or '').lower() not in {'partial'} and not evidence_bearing_followup_allowed:
            _block('followup', f"success_outcome_{str(success_status or 'unknown').lower()}")
            log_event_fn('AUTO_CAMPAIGN', 'followup_skipped_by_success_outcome', 'skipped', f"target={target};success_outcome={success_status or 'unknown'};workflow_status={workflow_status or 'none'};verdict={qual.get('verdict','none')}", actor='auto_campaign', row_type='service')
        else:
            now_ts = datetime.now(timezone.utc).timestamp()
            followup_cooldown_sec = int((toggles or {}).get('followup_cooldown_sec', 900) or 900)
            if now_ts - float(followup_recent.get(target_key, 0.0) or 0.0) < followup_cooldown_sec:
                _block('followup', 'followup_cooldown_active')
            else:
                followup_objective = f"{objective} [FOLLOWUP:{classification}]"
                key2 = dedup_key_fn(followup_objective, target)
                if key2 in scheduled_keys:
                    _block('followup', 'followup_duplicate_suppressed')
                else:
                    scheduled_keys.add(key2)
                    enqueue_followup_task_fn({
                        'objective': followup_objective,
                        'target': target,
                        'aggression': capped_aggression_fn(next_task_family, target, adaptive_aggression_fn(int(aggression) + 1, classification, reason_code, owner_override)),
                        'mode': 'followup',
                        'owner_approved_auth': owner_auth,
                        'owner_override': owner_override,
                        'task_family': next_task_family,
                        'priority_score': priority_score,
                        'utility_score': utility_score,
                        'campaign_success_criteria': str(task.get('campaign_success_criteria') or ''),
                        'task_success_criteria': str(task.get('task_success_criteria') or ''),
                        'acceptance_checks': list(task.get('acceptance_checks') or []),
                        'evidence_required': list(task.get('evidence_required') or []),
                        'success_semantics': dict(task_success_semantics),
                        'experiment_intent_id': task_experiment_intent_id,
                        'capability_candidates': list(task_capability_candidates),
                        'recommended_action_types': list(guided_actions_followup),
                        'hypothesis_candidates': list(task_hypothesis_candidates),
                        'planner_constraints': dict(task_planner_constraints),
                        'planner_preferences': dict(guided_preferences_followup),
                        'planner_rationale': dict(task_planner_rationale),
                        'planning_ladder': dict(task_planning_ladder),
                        'target_surface_rationale': [str(x or '').strip().lower() for x in (task_planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()],
                        'open_questions': list(dict.fromkeys(task_open_questions + guided_questions_followup + list(task_session_requirements.get('prerequisites') or [])))[:8],
                        'followup_evidence_gap': evidence_gap,
                        'followup_evidence_focus': list(evidence_focus),
                        'exploit_ladder': dict(task_exploit_ladder),
                        'actor_requirements': dict(task_actor_requirements),
                        'session_requirements': dict(task_session_requirements),
                        'promotion_policy': dict(task_promotion_policy),
                        'contamination_policy': dict(task_contamination_policy),
                        'approval_sensitivity': dict(task_approval_sensitivity),
                        'action_type': task_action_type,
                        'capability': task_capability,
                        'experiment_shape': task_experiment_shape,
                        'evidence_goal': task_evidence_goal,
                        'branch_state': str(branch_followup.get('branch_state') or ''),
                        'branch_action': str(branch_followup.get('branch_action') or ''),
                        'branch_reason': str(branch_followup.get('branch_reason') or ''),
                        'branch_lifecycle_status': str(branch_followup.get('branch_lifecycle_status') or ''),
                        'branch_lifecycle_reason': str(branch_followup.get('branch_lifecycle_reason') or ''),
                        'branch_lifecycle_confidence': float(branch_followup.get('branch_lifecycle_confidence') or 0.0),
                        'branch_thread_key': str(branch_followup.get('branch_thread_key') or ''),
                        'branch_thread_label': str(branch_followup.get('branch_thread_label') or ''),
                        'branch_evidence_score': float(branch_followup.get('branch_evidence_score') or 0.0),
                        'branch_evidence_signals': list(branch_followup.get('branch_evidence_signals') or []),
                        'name': f"Follow-up: {task.get('name') or objective}",
                    }, bool(classification in {'high', 'critical'} and '__rc_metrics__ code=403' not in summary_text.lower() and '__rc_metrics__ code=000' not in summary_text.lower() and 'code=000' not in summary_text.lower()))
                    followup_recent[target_key] = now_ts
                    followup_counts[target_key] = followup_counts.get(target_key, 0) + 1
                    queued_followup = True
                    _mark('followup', 'followup_job_queued')
                    log_event_fn('AUTO_CAMPAIGN', 'requeue_followup', 'retry_1', f"Queued follow-up for target={target}", actor='auto_campaign', highlight=True)

    if post_decision.get('precision'):
        if queued_confirm:
            _block('precision', 'confirm_precedence')
        elif queued_followup and requested_secondary_action != 'precision':
            _block('precision', 'followup_precedence')
        elif host_weak_count.get(host_from_target_fn(target), 0) < 2:
            _block('precision', 'insufficient_host_weak_signals')
        else:
            precision_objective = f"{objective} [PRECISION:{classification}]"
            pkey = dedup_key_fn(precision_objective, target)
            if pkey in scheduled_keys:
                _block('precision', 'precision_duplicate_suppressed')
            else:
                scheduled_keys.add(pkey)
                enqueue_followup_task_fn({
                    'objective': precision_objective,
                    'target': target,
                    'aggression': capped_aggression_fn(next_task_family, target, adaptive_aggression_fn(int(aggression), classification, reason_code, owner_override)),
                    'mode': 'precision',
                    'owner_approved_auth': owner_auth,
                    'owner_override': owner_override,
                    'task_family': next_task_family,
                    'priority_score': priority_score,
                    'utility_score': utility_score,
                    'campaign_success_criteria': str(task.get('campaign_success_criteria') or ''),
                    'task_success_criteria': str(task.get('task_success_criteria') or ''),
                    'acceptance_checks': list(task.get('acceptance_checks') or []),
                    'evidence_required': list(task.get('evidence_required') or []),
                    'success_semantics': dict(task_success_semantics),
                    'experiment_intent_id': task_experiment_intent_id,
                    'capability_candidates': list(task_capability_candidates),
                    'recommended_action_types': list(guided_actions_precision),
                    'hypothesis_candidates': list(task_hypothesis_candidates),
                    'planner_constraints': dict(task_planner_constraints),
                    'planner_preferences': dict(guided_preferences_precision),
                    'planner_rationale': dict(task_planner_rationale),
                    'planning_ladder': dict(task_planning_ladder),
                    'target_surface_rationale': [str(x or '').strip().lower() for x in (task_planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()],
                    'open_questions': list(dict.fromkeys(task_open_questions + guided_questions_precision + list(task_session_requirements.get('prerequisites') or [])))[:8],
                    'followup_evidence_gap': precision_gap,
                    'followup_evidence_focus': list(evidence_focus),
                    'exploit_ladder': dict(task_exploit_ladder),
                    'actor_requirements': dict(task_actor_requirements),
                    'session_requirements': dict(task_session_requirements),
                    'promotion_policy': dict(task_promotion_policy),
                    'contamination_policy': dict(task_contamination_policy),
                    'approval_sensitivity': dict(task_approval_sensitivity),
                    'action_type': task_action_type,
                    'capability': task_capability,
                    'experiment_shape': task_experiment_shape,
                    'evidence_goal': task_evidence_goal,
                    'branch_state': str(branch_precision.get('branch_state') or ''),
                    'branch_action': str(branch_precision.get('branch_action') or ''),
                    'branch_reason': str(branch_precision.get('branch_reason') or ''),
                    'branch_lifecycle_status': str(branch_precision.get('branch_lifecycle_status') or ''),
                    'branch_lifecycle_reason': str(branch_precision.get('branch_lifecycle_reason') or ''),
                    'branch_lifecycle_confidence': float(branch_precision.get('branch_lifecycle_confidence') or 0.0),
                    'branch_thread_key': str(branch_precision.get('branch_thread_key') or ''),
                    'branch_thread_label': str(branch_precision.get('branch_thread_label') or ''),
                    'branch_evidence_score': float(branch_precision.get('branch_evidence_score') or 0.0),
                    'branch_evidence_signals': list(branch_precision.get('branch_evidence_signals') or []),
                    'name': f"Precision: {task.get('name') or objective}",
                }, True)
                _mark('precision', 'precision_job_queued')
                log_event_fn('AUTO_CAMPAIGN', 'requeue_precision', 'in_progress', f"Queued precision task after ambiguous follow-up for target={target}", actor='auto_campaign', highlight=True)

    trimmed_blockers = {k: v for k, v in effective_blockers.items() if v}
    selected = [k for k, v in effective_flags.items() if v]
    attempted = [k for k, v in post_decision.items() if v]
    if selected and trimmed_blockers:
        effective_status = 'partial'
    elif selected:
        effective_status = 'applied'
    elif attempted and trimmed_blockers:
        effective_status = 'blocked'
    else:
        effective_status = 'noop'

    selected_action = selected[0] if selected else ''
    effective_secondary_action = ''
    if requested_secondary_action and effective_flags.get(requested_secondary_action, False) and requested_secondary_action != selected_action:
        if selected_action == 'confirm' and requested_secondary_action == 'followup':
            effective_secondary_action = 'followup'
        elif selected_action == 'followup' and requested_secondary_action == 'precision':
            effective_secondary_action = 'precision'
    summary = f"selected={','.join(selected) if selected else 'none'}"
    if effective_secondary_action:
        summary += f";secondary={effective_secondary_action}"
    if attempted:
        summary += f";attempted={','.join(attempted)}"
    if trimmed_blockers:
        summary += ';blockers=' + ';'.join(f"{k}:{','.join(v[:2])}" for k, v in trimmed_blockers.items())
    return confirm_total_local, {
        'requested_action': str(runtime_decision.get('requested_action') or runtime_decision.get('selected_primary_action') or ''),
        'effective_action': selected_action,
        'effective_secondary_action': effective_secondary_action,
        'effective_status': effective_status,
        'effective_flags': effective_flags,
        'effective_reasons': effective_reasons,
        'effective_blockers': trimmed_blockers,
        'effective_summary': summary,
    }
