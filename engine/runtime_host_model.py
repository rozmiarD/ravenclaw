from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class HostUpdateResult:
    host: str
    family: str
    state: Dict[str, Any]
    regeneration_reason: str = ""
    previous_state: str = "active"
    previous_state_band: str = "active"
    current_state: str = "active"
    current_state_band: str = "active"
    state_changed: bool = False
    reasons: List[str] = field(default_factory=list)
    deltas: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _promise_band(score: float) -> str:
    if score >= 1.18:
        return 'high'
    if score >= 1.0:
        return 'steady'
    return 'low'


def _noise_band(score: float) -> str:
    if score < 0.82:
        return 'high'
    if score < 0.92:
        return 'elevated'
    return 'normal'


def _host_semantics(*, state_band: str, promise_score: float, noise_score: float) -> Dict[str, str]:
    promise_band = _promise_band(promise_score)
    noise_band = _noise_band(noise_score)
    capability_state = 'normal'
    risk_band = 'normal'
    if state_band == 'exploitation':
        capability_state = 'exploit'
        risk_band = 'focused'
    elif state_band == 'promising':
        capability_state = 'preferred'
        risk_band = 'low'
    elif state_band == 'warmup':
        capability_state = 'warmup'
        risk_band = 'guarded'
    elif state_band == 'degraded':
        capability_state = 'constrained'
        risk_band = 'elevated'
    return {
        'promise_band': promise_band,
        'noise_band': noise_band,
        'capability_state': capability_state,
        'risk_band': risk_band,
    }


def default_host_state() -> Dict[str, Any]:
    return {
        'runs': 0,
        'promise_score': 1.0,
        'noise_score': 1.0,
        'evidence_density': 0.5,
        'novelty_score': 0.5,
        'preferred_families': [],
        'deprioritized_families': [],
        'suppressed_families': [],
        'last_success_family': '',
        'exploit_focus_family': '',
        'preferred_stages': [],
        'target_types_seen': [],
        'target_surface_rationale': [],
        'last_planning_stage': '',
        'last_next_stage': '',
        'exploitation_score': 0.0,
        'state': 'active',
        'state_band': 'active',
        'promise_band': 'steady',
        'noise_band': 'normal',
        'capability_state': 'normal',
        'risk_band': 'normal',
        'cooldown_until': None,
        'last_transition_reason': '',
        'last_transition_at_runs': 0,
    }


def _bounded(value: float, lower: float, upper: float) -> float:
    return round(min(upper, max(lower, value)), 3)


def _append_unique(items: list[str], value: str, *, limit: int = 6) -> list[str]:
    out = [str(x) for x in (items or []) if str(x).strip()]
    if value and value not in out:
        out.append(value)
    return out[:limit]


def update_host_state(
    *,
    host: str,
    family: str,
    previous: Dict[str, Any] | None,
    run_info: Dict[str, Any],
) -> HostUpdateResult:
    hs = dict(default_host_state())
    if isinstance(previous, dict):
        hs.update(previous)

    prev_state = str(hs.get('state') or 'active')
    prev_band = str(hs.get('state_band') or prev_state or 'active')
    prev_promise = float(hs.get('promise_score', 1.0) or 1.0)
    prev_noise = float(hs.get('noise_score', 1.0) or 1.0)
    prev_evidence = float(hs.get('evidence_density', 0.5) or 0.5)
    prev_novelty = float(hs.get('novelty_score', 0.5) or 0.5)
    prev_exploitation = float(hs.get('exploitation_score', 0.0) or 0.0)

    hs['runs'] = int(hs.get('runs', 0) or 0) + 1
    promising = bool(run_info.get('host_promise_positive', run_info.get('promising', False)))
    workflow_promotable = bool(run_info.get('workflow_promotable', run_info.get('promising', False)))
    status = str(run_info.get('engine_status') or 'unknown').lower()
    ev = str(run_info.get('success_criteria_eval') or '')
    utility = float(((run_info.get('runtime_utility') or {}).get('net_utility_score', 0.0)) or 0.0) if isinstance(run_info.get('runtime_utility'), dict) else 0.0
    priority = float(((run_info.get('decision_economics') or {}).get('priority_score', 0.0)) or 0.0) if isinstance(run_info.get('decision_economics'), dict) else 0.0
    runtime_task = run_info.get('runtime_task') if isinstance(run_info.get('runtime_task'), dict) else {}
    planner_rationale = run_info.get('planner_rationale') if isinstance(run_info.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
    planning_ladder = run_info.get('planning_ladder') if isinstance(run_info.get('planning_ladder'), dict) else (runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {}))
    target_profile = planner_rationale.get('target_profile_summary') if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
    target_type = str(target_profile.get('target_type') or '').strip().lower()
    target_surface_rationale = [str(x or '').strip().lower() for x in (planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()]
    current_stage = str(planning_ladder.get('current_stage') or '').strip().lower()
    next_stage = str(planning_ladder.get('next_stage') or '').strip().lower()
    reasons: list[str] = []

    if promising:
        hs['promise_score'] = _bounded(prev_promise + 0.08, 0.8, 1.5)
        hs['preferred_families'] = _append_unique(list(hs.get('preferred_families') or []), family)
        if current_stage:
            hs['preferred_stages'] = _append_unique(list(hs.get('preferred_stages') or []), current_stage)
        if next_stage:
            hs['preferred_stages'] = _append_unique(list(hs.get('preferred_stages') or []), next_stage)
        hs['novelty_score'] = _bounded(prev_novelty + 0.05, 0.1, 1.0)
        reasons.append('promising_signal')
    else:
        hs['promise_score'] = _bounded(prev_promise - 0.02, 0.8, 1.5)
        hs['novelty_score'] = _bounded(prev_novelty - 0.02, 0.1, 1.0)
        reasons.append('non_promising_signal')

    if target_type:
        hs['target_types_seen'] = _append_unique(list(hs.get('target_types_seen') or []), target_type)
    for signal in target_surface_rationale[:4]:
        hs['target_surface_rationale'] = _append_unique(list(hs.get('target_surface_rationale') or []), signal)
    hs['last_planning_stage'] = current_stage
    hs['last_next_stage'] = next_stage
    if current_stage or next_stage or target_type or target_surface_rationale:
        reasons.append('planner_runtime_rationale_observed')

    if status in {'failed', 'error', 'timeout', 'blocked'}:
        hs['noise_score'] = _bounded(prev_noise - 0.05, 0.72, 1.15)
        if family and hs['noise_score'] < 0.85:
            hs['suppressed_families'] = _append_unique(list(hs.get('suppressed_families') or []), family)
            reasons.append('family_suppressed_for_noise')
        reasons.append(f'engine_{status}')
    else:
        hs['noise_score'] = _bounded(prev_noise + 0.02, 0.72, 1.15)
        hs['last_success_family'] = family
        hs['suppressed_families'] = [x for x in list(hs.get('suppressed_families') or []) if x != family][:6]
        reasons.append('successful_engine_result')

    evidence = prev_evidence
    if ev == 'met':
        evidence += 0.08
        reasons.append('success_criteria_met')
    elif ev == 'partial':
        evidence += 0.03
        reasons.append('success_criteria_partial')
    else:
        evidence -= 0.03
        reasons.append('success_criteria_unmet')
    hs['evidence_density'] = _bounded(evidence, 0.1, 1.0)

    exploitation = prev_exploitation
    if promising and ev in {'partial', 'met'}:
        exploitation += 0.22
        reasons.append('exploitation_pressure_from_promising_partial_or_better')
    elif workflow_promotable:
        exploitation += 0.1
        reasons.append('exploitation_pressure_from_workflow_promotable')
    elif status in {'failed', 'error', 'timeout', 'blocked'}:
        exploitation -= 0.18
        reasons.append('exploitation_pressure_reduced_by_engine_failure')
    else:
        exploitation -= 0.04
    if utility > 0.45:
        exploitation += 0.08
        reasons.append('exploitation_pressure_from_runtime_utility')
    if priority > 0.3:
        exploitation += 0.05
        reasons.append('exploitation_pressure_from_priority')
    hs['exploitation_score'] = _bounded(exploitation, 0.0, 1.5)

    if hs['exploitation_score'] >= 0.65 and promising and hs['promise_score'] >= 1.12 and hs['noise_score'] >= 0.9:
        state_band = 'exploitation'
        compat_state = 'promising'
        if family:
            hs['exploit_focus_family'] = family
        elif current_stage in {'control_boundary_confirmation', 'bounded_exploit_proof'}:
            hs['exploit_focus_family'] = 'authz'
        elif current_stage == 'state_transition_confirmation':
            hs['exploit_focus_family'] = 'workflow'
        elif current_stage == 'report_artifact_capture':
            hs['exploit_focus_family'] = 'tls_assessment'
        else:
            hs['exploit_focus_family'] = str(hs.get('last_success_family') or '')
        reasons.append('host_entered_exploitation_mode')
    elif promising:
        state_band = 'promising'
        compat_state = 'promising'
        if family:
            hs['exploit_focus_family'] = family
    elif hs['noise_score'] < 0.85:
        state_band = 'degraded'
        compat_state = 'degraded'
    elif hs['runs'] <= 2:
        state_band = 'warmup'
        compat_state = 'active'
    else:
        state_band = 'active'
        compat_state = 'active'
    hs['state'] = compat_state
    hs['state_band'] = state_band
    if state_band not in {'promising', 'exploitation'} and float(hs.get('exploitation_score', 0.0) or 0.0) < 0.35:
        hs['exploit_focus_family'] = ''
    hs.update(_host_semantics(state_band=state_band, promise_score=float(hs['promise_score']), noise_score=float(hs['noise_score'])))

    state_changed = bool(prev_state != compat_state or prev_band != state_band)
    if state_changed:
        reasons.append(f'transition:{prev_band}->{state_band}')
        hs['last_transition_reason'] = reasons[-1]
        hs['last_transition_at_runs'] = int(hs.get('runs', 0) or 0)
    else:
        hs['last_transition_reason'] = str(hs.get('last_transition_reason') or '')
        hs['last_transition_at_runs'] = int(hs.get('last_transition_at_runs', 0) or 0)

    regeneration_reason = ''
    if state_band == 'exploitation' and prev_band != 'exploitation':
        regeneration_reason = 'promising_exploitation_host_shift'
        reasons.append('regeneration:promising_exploitation_host_shift')
    elif promising and hs['promise_score'] >= 1.18:
        regeneration_reason = 'promising_host_shift'
        reasons.append('regeneration:promising_host_shift')
    elif hs['state'] == 'degraded' and hs['noise_score'] < 0.82:
        regeneration_reason = 'degraded_host_shift'
        reasons.append('regeneration:degraded_host_shift')

    deltas = {
        'promise_score': round(hs['promise_score'] - prev_promise, 3),
        'noise_score': round(hs['noise_score'] - prev_noise, 3),
        'evidence_density': round(hs['evidence_density'] - prev_evidence, 3),
        'novelty_score': round(hs['novelty_score'] - prev_novelty, 3),
        'exploitation_score': round(hs['exploitation_score'] - prev_exploitation, 3),
    }

    return HostUpdateResult(
        host=host,
        family=family,
        state=hs,
        regeneration_reason=regeneration_reason,
        previous_state=prev_state,
        previous_state_band=prev_band,
        current_state=compat_state,
        current_state_band=state_band,
        state_changed=state_changed,
        reasons=reasons,
        deltas=deltas,
    )
