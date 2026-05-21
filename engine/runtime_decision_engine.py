from __future__ import annotations

from typing import Any, Dict

import vuln_qualification as vq  # type: ignore
from runtime_decision_contracts import DecisionOutcome, QualificationSummary, RuntimeDecisionRecord
from runtime_economics import compute_runtime_economics  # type: ignore
from runtime_explain import build_compact_explain  # type: ignore
from govengine_security_helpers import success_outcome_status, workflow_promotion_status, finding_signal_status  # type: ignore


BLOCKED_AUDITOR_DECISIONS = {"blocked", "deny", "reject", "owner_approval_required"}
FAILED_ENGINE_STATUSES = {"failed", "error", "timeout"}
DEFAULT_HIGH_LEVERAGE_PRECISION_FAMILIES = {'authz', 'idor', 'logic', 'workflow', 'state_transition', 'input_tamper'}
DEFAULT_DUAL_ACTION_FAMILIES = {'authz', 'idor', 'logic', 'workflow', 'state_transition', 'session', 'redirect_trust', 'input_tamper'}


def _selected_action(record: RuntimeDecisionRecord) -> tuple[str, str]:
    for name, outcome in (
        ('retry', record.retry),
        ('confirm', record.confirm),
        ('followup', record.followup),
        ('precision', record.precision),
    ):
        if outcome.allowed:
            return name, str(outcome.reason_code or '')
    if record.blocked:
        return '', str(record.blocked_reason or 'auditor_block')
    return '', 'no_action_selected'


def _high_leverage_precision_families(toggles: Dict[str, Any]) -> set[str]:
    raw = toggles.get('high_leverage_precision_families', []) if isinstance(toggles, dict) else []
    if isinstance(raw, list):
        families = {str(item).strip().lower() for item in raw if str(item).strip()}
        if families:
            return families
    return set(DEFAULT_HIGH_LEVERAGE_PRECISION_FAMILIES)


def _dual_action_families(toggles: Dict[str, Any]) -> set[str]:
    raw = toggles.get('dual_action_allowed_families', []) if isinstance(toggles, dict) else []
    if isinstance(raw, list):
        families = {str(item).strip().lower() for item in raw if str(item).strip()}
        if families:
            return families
    return set(DEFAULT_DUAL_ACTION_FAMILIES)


def _signal_evidence_bearing(signal_contract: Dict[str, Any]) -> bool:
    finding = signal_contract.get('finding_signal') if isinstance(signal_contract.get('finding_signal'), dict) else {}
    return bool(finding.get('evidence_bearing', False))


def _family_promotion_profile(
    *,
    task_family: str,
    evidence_goal: str,
    ladder_stage: str,
    actor_requirements: Dict[str, Any],
    session_requirements: Dict[str, Any],
    workflow_status: str,
    finding_status: str,
    success_status: str,
    precondition_blocking: bool,
    actor_state_blocking: bool,
) -> Dict[str, Any]:
    fam = str(task_family or '').strip().lower()
    evidence_goal_l = str(evidence_goal or '').strip().lower()
    ladder_stage_l = str(ladder_stage or '').strip().lower()
    workflow_l = str(workflow_status or '').strip().lower()
    finding_l = str(finding_status or '').strip().lower()
    success_l = str(success_status or '').strip().lower()
    discovery_only = bool(
        evidence_goal_l in {'surface_expansion', 'endpoint_or_header_inventory', 'novel_endpoint_or_asset'}
        or ladder_stage_l == 'discovery'
        or fam in {'recon', 'content_discovery', 'historical_url_mining', 'subdomain_expansion'}
    )
    comparison_heavy = bool(actor_requirements.get('differential')) or fam in {'authz', 'idor', 'logic'}
    stateful = bool(session_requirements.get('stateful')) or ladder_stage_l in {'state_transition_confirmation', 'bounded_exploit_proof'} or fam in {'workflow', 'state_transition', 'auth_flow'}
    blocked_preconditions = bool(precondition_blocking or actor_state_blocking)

    exploit_readiness = 'exploit_path_ready'
    if discovery_only:
        exploit_readiness = 'discovery_only'
    elif blocked_preconditions:
        exploit_readiness = 'blocked_preconditions'
    elif comparison_heavy and workflow_l in {'candidate', 'promotable', 'confirmable'}:
        exploit_readiness = 'comparison_expansion'
    elif stateful and success_l in {'partial', 'met'} and finding_l in {'moderate', 'strong'}:
        exploit_readiness = 'exploit_path_ready'
    elif stateful:
        exploit_readiness = 'state_transition_mapping'

    prefer_followup = bool(
        discovery_only
        or blocked_preconditions
        or (comparison_heavy and workflow_l in {'candidate', 'promotable', 'confirmable'})
        or (stateful and workflow_l in {'candidate', 'promotable', 'confirmable'} and success_l in {'partial', 'met'})
    )
    prefer_precision = bool(
        not discovery_only
        and not blocked_preconditions
        and ladder_stage_l in {'state_transition_confirmation', 'bounded_exploit_proof'}
        and workflow_l == 'candidate'
        and success_l in {'partial', 'met'}
    )
    suppress_confirm = bool(discovery_only or blocked_preconditions)
    return {
        'task_family': fam or 'generic',
        'evidence_goal': evidence_goal_l,
        'ladder_stage': ladder_stage_l,
        'discovery_only': discovery_only,
        'comparison_heavy': comparison_heavy,
        'stateful': stateful,
        'blocked_preconditions': blocked_preconditions,
        'prefer_followup': prefer_followup,
        'prefer_precision': prefer_precision,
        'suppress_confirm': suppress_confirm,
        'exploit_readiness': exploit_readiness,
    }


def build_runtime_decision(
    *,
    qual: Dict[str, Any] | None,
    auditor: str,
    engine_status: str,
    success_eval_status: str,
    toggles: Dict[str, Any] | None,
    mode: str = "",
    signal_contract: Dict[str, Any] | None = None,
    task_family: str = "",
    runtime_task: Dict[str, Any] | None = None,
) -> RuntimeDecisionRecord:
    toggles = toggles if isinstance(toggles, dict) else {}
    q = QualificationSummary.from_qual(qual)
    mode_l = str(mode or "").strip().lower()
    auditor_l = str(auditor or "").strip().lower()
    engine_l = str(engine_status or "").strip().lower()
    signal_contract = signal_contract if isinstance(signal_contract, dict) else {}
    success_l = success_outcome_status(signal_contract) or str(success_eval_status or "").strip().lower()
    workflow_status = workflow_promotion_status(signal_contract)
    finding_status = finding_signal_status(signal_contract)
    task_family_l = str(task_family or '').strip().lower()
    runtime_task = dict(runtime_task or {}) if isinstance(runtime_task, dict) else {}
    promotion_policy = dict(runtime_task.get('promotion_policy') or {}) if isinstance(runtime_task.get('promotion_policy'), dict) else {}
    exploit_ladder = dict(runtime_task.get('exploit_ladder') or {}) if isinstance(runtime_task.get('exploit_ladder'), dict) else {}
    actor_requirements = dict(runtime_task.get('actor_requirements') or {}) if isinstance(runtime_task.get('actor_requirements'), dict) else {}
    session_requirements = dict(runtime_task.get('session_requirements') or {}) if isinstance(runtime_task.get('session_requirements'), dict) else {}
    approval_sensitivity = dict(runtime_task.get('approval_sensitivity') or {}) if isinstance(runtime_task.get('approval_sensitivity'), dict) else {}
    planner_rationale = dict(runtime_task.get('planner_rationale') or {}) if isinstance(runtime_task.get('planner_rationale'), dict) else {}
    planning_ladder = dict(runtime_task.get('planning_ladder') or planner_rationale.get('planning_ladder') or {}) if isinstance(runtime_task.get('planning_ladder') or planner_rationale.get('planning_ladder'), dict) else {}
    evidence_goal = str(runtime_task.get('evidence_goal') or '').strip().lower()
    ladder_stage = str(exploit_ladder.get('stage') or '').strip().lower()
    task_open_questions = [str(x or '').strip().lower() for x in (runtime_task.get('open_questions') or []) if str(x or '').strip()]
    session_prerequisites = [str(x or '').strip().lower() for x in (session_requirements.get('prerequisites') or []) if str(x or '').strip()]
    precondition_gaps = [p for p in session_prerequisites if any(p in q or q in p for q in task_open_questions)]
    actor_keywords = ('identity', 'identities', 'role', 'roles', 'actor', 'account', 'comparison')
    actor_state_gaps = [q for q in task_open_questions if any(k in q for k in actor_keywords)]
    actor_state_blocking = bool(actor_requirements.get('required') and actor_state_gaps and (bool(actor_requirements.get('differential')) or bool(session_requirements.get('auth_context'))))
    precondition_blocking = bool(session_requirements.get('stateful') and precondition_gaps and ladder_stage in {'state_transition_confirmation', 'bounded_exploit_proof'})
    discovery_goal = evidence_goal in {'surface_expansion', 'endpoint_or_header_inventory', 'novel_endpoint_or_asset'}
    controlled_comparison_goal = evidence_goal == 'controlled_comparison'
    planning_current_stage = str(planning_ladder.get('current_stage') or ladder_stage or '').strip().lower()
    planning_next_stage = str(planning_ladder.get('next_stage') or '').strip().lower()
    recommended_progression = [str(x or '').strip().lower() for x in (planner_rationale.get('recommended_progression') or []) if str(x or '').strip()]
    target_profile_summary = dict(planner_rationale.get('target_profile_summary') or {}) if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
    target_type = str(target_profile_summary.get('target_type') or '').strip().lower()
    surface_keywords = [str(x or '').strip().lower() for x in (planner_rationale.get('planner_preferences') or {}).get('surface_keywords', [])] if isinstance(planner_rationale.get('planner_preferences'), dict) else []
    target_surface_rationale = []
    if target_type in {'api', 'auth', 'integration'}:
        target_surface_rationale.append('authenticated_or_boundary_mapping')
    elif target_type == 'web':
        target_surface_rationale.append('browser_flow_mapping')
    elif target_type in {'static', 'support'}:
        target_surface_rationale.append('artifact_capture')
    target_surface_rationale.extend([x for x in surface_keywords if x in {'admin', 'billing', 'tenant', 'organization', 'api', 'auth', 'account'}])
    target_surface_rationale = list(dict.fromkeys(target_surface_rationale))[:6]
    policy_followup_allowed = bool(promotion_policy.get('followup_allowed', True))
    ladder_followup_bias = bool(
        planning_next_stage
        and planning_current_stage in {'discovery', 'validation', 'control_boundary_confirmation', 'state_transition_confirmation'}
        and planning_next_stage != planning_current_stage
    )
    artifact_capture_bias = bool(
        planning_current_stage == 'report_artifact_capture'
        or planning_next_stage == 'report_artifact_capture'
        or str(planning_ladder.get('proof_strategy') or '').strip().lower() == 'reportable_artifact_capture'
    )
    policy_confirm_preferred = bool(
        promotion_policy.get(
            'confirm_preferred',
            (not signal_contract)
            or workflow_status == 'confirmable'
            or planning_current_stage in {'control_boundary_confirmation', 'state_transition_confirmation', 'bounded_exploit_proof'}
            or planning_next_stage == 'bounded_exploit_proof'
            or any(x in recommended_progression for x in {'control_boundary_confirmation', 'state_transition_confirmation', 'bounded_exploit_proof'})
        )
    )
    if artifact_capture_bias:
        policy_confirm_preferred = False
    family_profile = _family_promotion_profile(
        task_family=task_family_l,
        evidence_goal=evidence_goal,
        ladder_stage=ladder_stage,
        actor_requirements=actor_requirements,
        session_requirements=session_requirements,
        workflow_status=workflow_status,
        finding_status=finding_status,
        success_status=success_l,
        precondition_blocking=precondition_blocking,
        actor_state_blocking=actor_state_blocking,
    )
    blocked = auditor_l in BLOCKED_AUDITOR_DECISIONS
    if family_profile.get('suppress_confirm'):
        policy_confirm_preferred = False
    followup_ok = success_l in {"partial"}

    retry = DecisionOutcome(blockers=[])
    confirm = DecisionOutcome(blockers=[])
    followup = DecisionOutcome(blockers=[])
    precision = DecisionOutcome(blockers=[])

    inputs: Dict[str, Any] = {
        "verdict": q.verdict,
        "confidence": q.confidence,
        "guards_passed": q.guards_passed,
        "auditor_decision": auditor_l,
        "engine_status": engine_l,
        "success_eval_status": success_l,
        "workflow_promotion_status": workflow_status or 'unknown',
        "finding_signal_status": finding_status or 'unknown',
        "task_family": task_family_l or 'generic',
        "mode": mode_l,
    }
    why: list[str] = []
    blockers: list[str] = []
    scores: Dict[str, Any] = {
        "qualification_confidence": round(float(q.confidence), 3),
    }

    if blocked:
        auditor_block = f"auditor_block:{auditor_l}"
        blockers.append(auditor_block)
        confirm.blockers.append(auditor_block)
        followup.blockers.append(auditor_block)
        precision.blockers.append(auditor_block)

    if engine_l in FAILED_ENGINE_STATUSES:
        retry = DecisionOutcome(
            allowed=True,
            reason_code="engine_failed_retry",
            score=1.0,
            blockers=[],
        )
        why.append("engine_status_failed")
        confirm.blockers.append('retry_precedence')
        followup.blockers.append('retry_precedence')
        precision.blockers.append('retry_precedence')
        economics = compute_runtime_economics(
            verdict=q.verdict,
            confidence=q.confidence,
            engine_status=engine_l,
            success_eval_status=success_l,
            mode=mode_l,
            blocked=blocked,
        )
        scores.update(economics)
        provisional = RuntimeDecisionRecord(
            retry=retry,
            confirm=confirm,
            followup=followup,
            precision=precision,
            blocked=blocked,
            blocked_reason="auditor_block" if blocked else "",
            mode=mode_l,
            verdict=q.verdict,
            engine_status=engine_l,
            auditor_decision=auditor_l,
            success_eval_status=success_l,
            economics=economics,
            explain={},
        )
        selected_action, selection_reason = _selected_action(provisional)
        explain = build_compact_explain(
            why=why,
            blockers=blockers,
            inputs=inputs,
            scores=scores,
            flags={"retry": True, "confirm": False, "followup": False, "precision": False},
        )
        explain['requested_action'] = selected_action
        explain['requested_reason'] = selection_reason
        explain['selected_primary_action'] = selected_action
        explain['selection_reason'] = selection_reason
        provisional.explain = explain
        provisional.requested_action = selected_action
        provisional.requested_reason = selection_reason
        provisional.selected_primary_action = selected_action
        provisional.selection_reason = selection_reason
        return provisional

    confirmable_by_contract = workflow_status == 'confirmable'
    promotable_by_contract = workflow_status in {'promotable', 'confirmable'}
    evidence_bearing_followup_enabled = bool(toggles.get('evidence_bearing_followup_bridge', True))
    evidence_bearing_followup_bridge = bool(
        signal_contract
        and evidence_bearing_followup_enabled
        and not followup_ok
        and not blocked
        and mode_l != 'followup'
        and promotable_by_contract
        and _signal_evidence_bearing(signal_contract)
        and finding_status in {'weak', 'moderate', 'strong'}
        and q.guards_passed
        and engine_l not in FAILED_ENGINE_STATUSES
    )
    artifact_capture_precision_enabled = bool(toggles.get('artifact_capture_precision_bias', True))
    artifact_capture_precision = bool(
        signal_contract
        and artifact_capture_precision_enabled
        and not blocked
        and mode_l != 'followup'
        and artifact_capture_bias
        and policy_followup_allowed
        and _signal_evidence_bearing(signal_contract)
        and finding_status in {'moderate', 'strong'}
        and q.guards_passed
        and engine_l not in FAILED_ENGINE_STATUSES
        and success_l in {'partial', 'met'}
        and not precondition_blocking
        and not actor_state_blocking
    )
    early_precision_enabled = bool(toggles.get('early_precision_for_high_leverage_families', True))
    early_precision_families = _high_leverage_precision_families(toggles)
    high_leverage_candidate_precision = bool(
        signal_contract
        and early_precision_enabled
        and not blocked
        and mode_l != 'followup'
        and workflow_status == 'candidate'
        and task_family_l in early_precision_families
        and _signal_evidence_bearing(signal_contract)
        and finding_status in {'weak', 'moderate', 'strong'}
        and q.guards_passed
        and engine_l not in FAILED_ENGINE_STATUSES
        and success_l in {'partial', 'met'}
    )
    candidate_partial_bridge_enabled = bool(toggles.get("candidate_partial_followup_bridge", True))
    candidate_partial_bridge = bool(
        signal_contract
        and candidate_partial_bridge_enabled
        and workflow_status == 'candidate'
        and followup_ok
        and not blocked
        and mode_l != 'followup'
        and finding_status in {'weak', 'moderate', 'strong'}
        and engine_l not in FAILED_ENGINE_STATUSES
        and not high_leverage_candidate_precision
    )
    wants_confirm = bool(toggles.get("enable_confirm_jobs", True)) and not blocked and (
        confirmable_by_contract
        or (signal_contract and promotable_by_contract and not policy_followup_allowed)
        or (not signal_contract and q.verdict == "probable")
    )
    wants_followup = False
    wants_precision = False

    if bool(toggles.get("enable_followups", True)) and not blocked:
        threshold = str(toggles.get("qualification_followup_threshold", "probable") or "probable")
        if mode_l == "followup":
            wants_precision = True
        elif artifact_capture_precision:
            wants_precision = True
        elif high_leverage_candidate_precision:
            wants_precision = True
        else:
            if signal_contract:
                wants_followup = policy_followup_allowed and (promotable_by_contract or family_profile.get('prefer_followup') or ladder_followup_bias or artifact_capture_bias or (workflow_status == 'confirmable' and (not policy_confirm_preferred or controlled_comparison_goal)) or candidate_partial_bridge or evidence_bearing_followup_bridge or precondition_blocking)
                followup.threshold = threshold
                if candidate_partial_bridge:
                    followup.reason_code = 'candidate_partial_followup_bridge'
                elif evidence_bearing_followup_bridge:
                    followup.reason_code = 'evidence_bearing_followup_bridge'
                if not wants_followup:
                    if not followup_ok and not evidence_bearing_followup_bridge:
                        followup.blockers.append(f'success_eval:{success_l or "unknown"}')
                    if not policy_followup_allowed:
                        followup.blockers.append('followup_policy_disabled')
                        blockers.append('followup_policy_disabled')
                    if precondition_blocking:
                        followup.blockers.append('preconditions_unresolved')
                    if actor_state_blocking:
                        followup.blockers.append('actor_state_unresolved')
                        blockers.append('actor_state_unresolved')
                    followup.blockers.append(f'workflow_not_promotable:{workflow_status or "none"}')
            else:
                if followup_ok:
                    wants_followup = vq.verdict_at_least(q.verdict, threshold)
                followup.threshold = threshold
                if not wants_followup:
                    if not followup_ok:
                        followup.blockers.append(f'success_eval:{success_l or "unknown"}')
                    followup.blockers.append(f'verdict_below_threshold:{threshold}')
    else:
        if not bool(toggles.get("enable_followups", True)):
            blockers.append("followups_disabled")
            followup.blockers.append('followups_disabled')
        if blocked:
            blockers.append("followups_blocked_by_auditor")

    if wants_confirm and (policy_confirm_preferred or not wants_followup):
        confirm = DecisionOutcome(
            allowed=True,
            reason_code=("workflow_confirmable" if signal_contract else "probable_verdict_confirm"),
            score=max(0.6, float(q.confidence)),
            blockers=[],
        )
        why.append("confirm_selected_for_confirmable_workflow" if signal_contract else "confirm_selected_for_probable_verdict")
        followup.blockers.append('confirm_precedence')
        precision.blockers.append('confirm_precedence')
        blockers.append("followup_skipped_because_confirm_selected")
    elif artifact_capture_precision:
        precision = DecisionOutcome(
            allowed=True,
            reason_code='artifact_capture_precision_bias',
            score=max(0.38, float(q.confidence)),
            blockers=[],
        )
        why.append('precision_selected_for_artifact_capture')
        followup.blockers.append('precision_preferred_for_artifact_capture')
    elif ((high_leverage_candidate_precision and policy_followup_allowed and not precondition_blocking) or family_profile.get('prefer_precision')):
        precision = DecisionOutcome(
            allowed=True,
            reason_code=('state_transition_precision_bias' if ladder_stage == 'state_transition_confirmation' else 'high_leverage_candidate_precision'),
            score=max(0.34, float(q.confidence)),
            blockers=[],
        )
    elif high_leverage_candidate_precision and not policy_followup_allowed:
        precision.blockers.append('followup_policy_disabled')
    elif high_leverage_candidate_precision and precondition_blocking:
        precision.blockers.append('preconditions_unresolved')
    elif high_leverage_candidate_precision and actor_state_blocking:
        precision.blockers.append('actor_state_unresolved')
        why.append('precision_selected_for_high_leverage_candidate_signal')
        followup.blockers.append('precision_preferred_for_high_leverage_candidate')
    elif signal_contract and workflow_status == 'candidate' and not candidate_partial_bridge:
        followup.blockers.append('candidate_requires_promotion')
        blockers.append('candidate_signal_requires_promotion')
    elif wants_followup:
        followup.allowed = True
        if str(followup.reason_code or '').strip().lower() in {'', 'not_applicable'}:
            followup.reason_code = 'followup_threshold_met'
        else:
            followup.reason_code = str(followup.reason_code)
        followup.score = max(0.3, float(q.confidence))
        if followup.reason_code == 'candidate_partial_followup_bridge':
            why.append('followup_selected_from_candidate_partial_bridge')
        elif followup.reason_code == 'evidence_bearing_followup_bridge':
            why.append('followup_selected_from_evidence_bearing_bridge')
        else:
            why.append("followup_selected_from_threshold")
        precision.blockers.append('followup_precedence')
    elif wants_precision:
        precision = DecisionOutcome(
            allowed=True,
            reason_code="followup_mode_precision",
            score=max(0.3, float(q.confidence)),
            blockers=[],
        )
        why.append("precision_selected_after_followup_mode")
    else:
        if signal_contract:
            if workflow_status != 'confirmable':
                confirm.blockers.append(f'confirm_requires_confirmable_workflow:{workflow_status or "none"}')
        elif q.verdict != 'probable':
            confirm.blockers.append(f'confirm_requires_probable:{q.verdict}')
        if mode_l != 'followup':
            precision.blockers.append(f'precision_requires_followup_mode:{mode_l or "fast"}')

    economics = compute_runtime_economics(
        verdict=q.verdict,
        confidence=q.confidence,
        engine_status=engine_l,
        success_eval_status=success_l,
        mode=mode_l,
        blocked=blocked,
    )
    scores.update(economics)
    provisional = RuntimeDecisionRecord(
        retry=retry,
        confirm=confirm,
        followup=followup,
        precision=precision,
        blocked=blocked,
        blocked_reason="auditor_block" if blocked else "",
        mode=mode_l,
        verdict=q.verdict,
        engine_status=engine_l,
        auditor_decision=auditor_l,
        success_eval_status=success_l,
        economics=economics,
        explain={},
    )
    selected_action, selection_reason = _selected_action(provisional)
    flags = provisional.action_flags()
    explain = build_compact_explain(why=why, blockers=blockers, inputs=inputs, scores=scores, flags=flags)
    explain['requested_action'] = selected_action
    explain['exploit_ladder'] = exploit_ladder
    explain['actor_requirements'] = actor_requirements
    explain['session_requirements'] = session_requirements
    explain['promotion_policy'] = promotion_policy
    explain['approval_sensitivity'] = approval_sensitivity
    explain['precondition_gaps'] = list(precondition_gaps)
    explain['actor_state_gaps'] = list(actor_state_gaps)
    explain['precondition_blocking'] = precondition_blocking
    explain['actor_state_blocking'] = actor_state_blocking
    explain['family_promotion_profile'] = dict(family_profile)
    explain['planning_ladder'] = dict(planning_ladder)
    explain['recommended_progression'] = list(recommended_progression)
    explain['target_profile_summary'] = dict(target_profile_summary)
    explain['target_surface_rationale'] = list(target_surface_rationale)
    explain['ladder_followup_bias'] = ladder_followup_bias
    explain['artifact_capture_bias'] = artifact_capture_bias
    explain['requested_reason'] = selection_reason
    explain['selected_primary_action'] = selected_action
    explain['selection_reason'] = selection_reason
    secondary_action = ''
    secondary_reason = ''
    dual_action_enabled = bool(toggles.get('safe_dual_action_enabled', True))
    dual_action_families = _dual_action_families(toggles)
    dual_action_allowed = bool(
        dual_action_enabled
        and not blocked
        and task_family_l in dual_action_families
        and q.guards_passed
        and engine_l not in FAILED_ENGINE_STATUSES
        and success_l in {'partial', 'met'}
        and finding_status in {'moderate', 'strong'}
    )
    if dual_action_allowed:
        if selected_action == 'confirm' and promotable_by_contract:
            secondary_action = 'followup'
            secondary_reason = 'dual_action_confirm_followup'
        elif selected_action == 'followup' and workflow_status in {'promotable', 'confirmable'}:
            secondary_action = 'precision'
            secondary_reason = 'dual_action_followup_precision'

    if secondary_action:
        explain['selected_secondary_action'] = secondary_action
        explain['secondary_selection_reason'] = secondary_reason
    provisional.explain = explain
    provisional.requested_action = selected_action
    provisional.requested_reason = selection_reason
    provisional.selected_primary_action = selected_action
    provisional.selection_reason = selection_reason
    provisional.selected_secondary_action = secondary_action
    provisional.secondary_selection_reason = secondary_reason
    return provisional
