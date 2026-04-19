from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from runtime_plan_control import recon_to_exploit_synthesis  # type: ignore


LATE_PHASE_ORDER = {
    'discovery': 1,
    'validation': 1,
    'control_boundary_confirmation': 2,
    'state_transition_confirmation': 2,
    'bounded_exploit_proof': 3,
    'report_artifact_capture': 4,
}
MODE_DEPTH_RANK = {
    'fast': 1,
    'confirm': 2,
    'followup': 2,
    'precision': 3,
    'deep': 3,
}
EXPECTED_DEPTH_LIMIT = {
    'light': 1,
    'medium': 2,
    'deep': 3,
}
CLUSTER_SHALLOW_TOKENS = ('edge', 'support', 'static', 'cdn', 'infra')
DEEP_SURFACE_ROLES = {'background', 'supporting', 'secondary'}


@dataclass
class PlannerRuntimeAdmissionDecision:
    allowed: bool
    reason_code: str = 'allowed'
    detail: str = ''
    blockers: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    signal: dict[str, Any] = field(default_factory=dict)
    explainability: dict[str, Any] = field(default_factory=dict)


def normalize_activation_phase(value: Any) -> int:
    raw = str(value or '').strip().lower()
    if not raw:
        return 1
    if raw.isdigit():
        return max(1, min(3, int(raw)))
    rank = LATE_PHASE_ORDER.get(raw, 1)
    if rank >= 3:
        return 3
    if rank >= 2:
        return 2
    return 1


def planner_gate_context(runtime_task: dict[str, Any] | None) -> dict[str, Any]:
    rt = runtime_task if isinstance(runtime_task, dict) else {}
    activation_mode = str(rt.get('activation_mode') or 'immediate').strip().lower() or 'immediate'
    conditional_gate = str(rt.get('conditional_gate') or '').strip().lower()
    surface_role = str(rt.get('surface_role') or 'primary').strip().lower() or 'primary'
    target_cluster = str(rt.get('target_cluster') or 'general').strip().lower() or 'general'
    expected_depth = str(rt.get('expected_depth') or 'medium').strip().lower() or 'medium'
    if expected_depth not in EXPECTED_DEPTH_LIMIT:
        expected_depth = 'medium'
    return {
        'activation_phase': normalize_activation_phase(rt.get('activation_phase')),
        'activation_mode': activation_mode,
        'conditional_gate': conditional_gate,
        'surface_role': surface_role,
        'target_cluster': target_cluster,
        'expected_depth': expected_depth,
    }


def mode_depth_rank(mode: str) -> int:
    normalized = str(mode or '').strip().lower()
    if normalized.startswith('retry_'):
        normalized = normalized[len('retry_'):]
    return MODE_DEPTH_RANK.get(normalized, 1)


def planner_signal_snapshot(host_state: dict, host: str, host_success_count: dict[str, int] | None = None) -> dict[str, Any]:
    hs = ((host_state or {}).get('hosts') or {}).get(host) or {}
    if not isinstance(hs, dict):
        hs = {}
    preferred_stages = {str(x or '').strip().lower() for x in (hs.get('preferred_stages') or []) if str(x or '').strip()}
    target_types_seen = {str(x or '').strip().lower() for x in (hs.get('target_types_seen') or []) if str(x or '').strip()}
    target_surface = {str(x or '').strip().lower() for x in (hs.get('target_surface_rationale') or []) if str(x or '').strip()}
    state_band = str(hs.get('state_band') or hs.get('state') or '').strip().lower()
    success_count = int((host_success_count or {}).get(host, hs.get('success_count') or 0) or 0)
    authenticated = bool(hs.get('authenticated') or hs.get('auth_available'))
    boundary = bool(hs.get('boundary_mapping_ready') or hs.get('control_boundary_confirmed') or hs.get('object_boundary_mapped'))
    stateful = bool(hs.get('stateful_signal') or hs.get('state_transition_ready'))
    explicit_primary = bool(hs.get('primary_signal') or hs.get('promising_signal'))
    explicit_confirmed = bool(hs.get('confirmed_signal'))
    chainable = bool(hs.get('chainable_impact') or hs.get('impact_confirmed') or explicit_confirmed)
    surface_promoted = bool(hs.get('surface_promoted'))
    observed_stage = str(hs.get('max_ladder_stage') or hs.get('last_confirmed_stage') or '').strip().lower()
    observed_stage_rank = LATE_PHASE_ORDER.get(observed_stage, 0)
    has_boundary_signal = bool(
        boundary
        or preferred_stages & {'control_boundary_confirmation', 'state_transition_confirmation', 'bounded_exploit_proof', 'report_artifact_capture'}
        or target_types_seen & {'api', 'auth', 'integration', 'web'}
        or target_surface & {'authenticated_or_boundary_mapping', 'artifact_capture'}
        or observed_stage_rank >= 2
    )
    has_primary_signal = bool(explicit_primary or success_count > 0 or state_band in {'promising', 'exploitation'} or has_boundary_signal)
    has_confirmed_signal = bool(explicit_confirmed or success_count >= 2 or state_band == 'exploitation' or observed_stage_rank >= 3 or preferred_stages & {'bounded_exploit_proof', 'report_artifact_capture'})
    has_surface_promotion = bool(surface_promoted or has_primary_signal or has_confirmed_signal)
    return {
        'state_band': state_band,
        'preferred_stages': preferred_stages,
        'target_types_seen': target_types_seen,
        'target_surface': target_surface,
        'success_count': success_count,
        'authenticated': authenticated,
        'boundary': boundary,
        'stateful': stateful,
        'chainable': chainable,
        'observed_stage': observed_stage,
        'observed_stage_rank': observed_stage_rank,
        'has_boundary_signal': has_boundary_signal,
        'has_primary_signal': has_primary_signal,
        'has_confirmed_signal': has_confirmed_signal,
        'has_surface_promotion': has_surface_promotion,
    }


def planner_runtime_admission_decision(*, runtime_task: dict[str, Any] | None, host_state: dict, host: str, mode: str, host_success_count: dict[str, int] | None = None, planner_feedback: dict[str, Any] | None = None) -> PlannerRuntimeAdmissionDecision:
    ctx = planner_gate_context(runtime_task)
    signal = planner_signal_snapshot(host_state, host, host_success_count)
    rt = runtime_task if isinstance(runtime_task, dict) else {}
    planner_rationale = rt.get('planner_rationale') if isinstance(rt.get('planner_rationale'), dict) else {}
    planning_ladder = rt.get('planning_ladder') if isinstance(rt.get('planning_ladder'), dict) else {}
    target_profile = planner_rationale.get('target_profile_summary') if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
    synthesis = recon_to_exploit_synthesis(
        planner_feedback=planner_feedback if isinstance(planner_feedback, dict) else {},
        next_stage=str(planning_ladder.get('next_stage') or ''),
        target_type=str(target_profile.get('target_type') or ''),
        target_surface_rationale=list(planner_rationale.get('target_surface_rationale') or []),
        current_family=str(rt.get('task_family') or ''),
    )
    synthesis_action = str(synthesis.get('recommended_branch_action') or '').strip().lower()
    synthesis_reason = str(synthesis.get('synthesis_reason') or '').strip().lower()
    synthesis_gate_stage = str(planning_ladder.get('next_stage') or '').strip().lower()
    synthesis_gate_family = str(rt.get('task_family') or '').strip().lower()
    synthesis_gate_relevant = synthesis_gate_stage in {'validation', 'bounded_exploit_proof'} and synthesis_gate_family in {'recon', 'content_discovery', 'historical_url_mining', 'subdomain_expansion'}
    explainability = {
        'synthesis_recommended_action': synthesis_action,
        'synthesis_reason': synthesis_reason,
        'synthesis_next_stage': synthesis_gate_stage,
        'synthesis_gate_family': synthesis_gate_family,
        'synthesis_gate_relevant': synthesis_gate_relevant,
    }
    blockers: list[str] = []
    activation_phase = int(ctx['activation_phase'])
    activation_mode = str(ctx['activation_mode'])
    conditional_gate = str(ctx['conditional_gate'])
    surface_role = str(ctx['surface_role'])
    target_cluster = str(ctx['target_cluster'])
    expected_depth = str(ctx['expected_depth'])
    mode_rank = mode_depth_rank(mode)
    depth_limit = EXPECTED_DEPTH_LIMIT.get(expected_depth, 2)

    if mode_rank > depth_limit:
        blockers.append('planner_expected_depth_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_expected_depth_skip', f'expected_depth={expected_depth};mode={mode}', blockers, ctx, signal)

    if mode_rank > 1 and target_cluster != 'general' and any(token in target_cluster for token in CLUSTER_SHALLOW_TOKENS):
        if mode_rank >= 3 and not signal['has_confirmed_signal']:
            blockers.append('planner_target_cluster_gate')
            return PlannerRuntimeAdmissionDecision(False, 'planner_target_cluster_skip', f'target_cluster={target_cluster};mode={mode};requires=confirmed_signal', blockers, ctx, signal)
        if mode_rank == 2 and not signal['has_primary_signal']:
            blockers.append('planner_target_cluster_gate')
            return PlannerRuntimeAdmissionDecision(False, 'planner_target_cluster_skip', f'target_cluster={target_cluster};mode={mode};requires=primary_signal', blockers, ctx, signal)

    if activation_phase >= 3 and not (signal['has_confirmed_signal'] or signal['observed_stage_rank'] >= 3):
        blockers.append('planner_phase_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_activation_phase_skip', f'phase={activation_phase};requires=confirmed_signal', blockers, ctx, signal)
    if activation_phase >= 2 and not (signal['has_primary_signal'] or signal['observed_stage_rank'] >= 2):
        blockers.append('planner_phase_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_activation_phase_skip', f'phase={activation_phase};requires=primary_signal', blockers, ctx, signal)

    if synthesis_gate_relevant and synthesis_action == 'abandon' and mode_rank > 1:
        blockers.append('planner_synthesis_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_synthesis_skip', f'synthesis={synthesis_reason or synthesis_action};mode={mode}', blockers, ctx, signal, explainability)

    if synthesis_gate_relevant and synthesis_action == 'pivot' and mode_rank >= 3 and not signal['has_primary_signal']:
        blockers.append('planner_synthesis_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_synthesis_skip', f'synthesis={synthesis_reason or synthesis_action};mode={mode};requires=primary_signal_for_deep_execution', blockers, ctx, signal, explainability)

    if activation_mode == 'if_confirmed' and not signal['has_confirmed_signal']:
        blockers.append('planner_activation_mode_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_activation_mode_skip', f'activation_mode={activation_mode};requires=confirmed_signal', blockers, ctx, signal)
    if activation_mode == 'if_signal' and not signal['has_primary_signal']:
        blockers.append('planner_activation_mode_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_activation_mode_skip', f'activation_mode={activation_mode};requires=primary_signal', blockers, ctx, signal)
    if activation_mode == 'background' and surface_role != 'background':
        blockers.append('planner_activation_mode_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_activation_mode_skip', f'activation_mode={activation_mode};surface_role={surface_role}', blockers, ctx, signal)
    if activation_mode == 'background' and mode_rank > 1 and not signal['has_confirmed_signal']:
        blockers.append('planner_activation_mode_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_activation_mode_skip', f'activation_mode={activation_mode};mode={mode};requires=confirmed_signal_for_deeper_execution', blockers, ctx, signal)

    if conditional_gate == 'supporting_surface_only' and surface_role != 'supporting':
        blockers.append('planner_conditional_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_conditional_gate_skip', 'conditional_gate=supporting_surface_only;requires=supporting', blockers, ctx, signal)
    if conditional_gate == 'background_surface_only' and surface_role != 'background':
        blockers.append('planner_conditional_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_conditional_gate_skip', 'conditional_gate=background_surface_only;requires=background', blockers, ctx, signal)
    if conditional_gate == 'authenticated_or_boundary_mapping' and not (signal['authenticated'] or signal['boundary'] or signal['has_boundary_signal']):
        blockers.append('planner_conditional_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_conditional_gate_skip', 'conditional_gate=authenticated_or_boundary_mapping;requires=boundary_or_auth_signal', blockers, ctx, signal)
    if conditional_gate == 'stateful_or_boundary_signal' and not (signal['stateful'] or signal['boundary'] or signal['has_boundary_signal']):
        blockers.append('planner_conditional_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_conditional_gate_skip', 'conditional_gate=stateful_or_boundary_signal;requires=stateful_or_boundary_signal', blockers, ctx, signal)
    if conditional_gate == 'surface_mapping_after_primary_signal' and not signal['has_primary_signal']:
        blockers.append('planner_conditional_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_conditional_gate_skip', 'conditional_gate=surface_mapping_after_primary_signal;requires=primary_signal', blockers, ctx, signal)
    if conditional_gate == 'chainable_impact_or_confirmed_signal' and not (signal['chainable'] or signal['has_confirmed_signal']):
        blockers.append('planner_conditional_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_conditional_gate_skip', 'conditional_gate=chainable_impact_or_confirmed_signal;requires=confirmed_or_chainable_signal', blockers, ctx, signal)

    if surface_role in DEEP_SURFACE_ROLES and mode_rank > 1 and not signal['has_surface_promotion']:
        blockers.append('planner_surface_role_gate')
        return PlannerRuntimeAdmissionDecision(False, 'planner_surface_role_skip', f'surface_role={surface_role};mode={mode};requires=promotion_signal', blockers, ctx, signal)

    return PlannerRuntimeAdmissionDecision(True, 'allowed', '', blockers, ctx, signal, explainability)
