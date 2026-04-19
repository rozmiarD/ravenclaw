from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from auto_campaign_targets import attack_family, host_from_target, is_resolvable_host  # type: ignore
from runtime_admission_policy import planner_gate_context, planner_runtime_admission_decision  # type: ignore


@dataclass
class HostExecutionGate:
    allowed: bool
    host: str
    family: str
    reason_code: str = "allowed"
    detail: str = ""
    cooldown_until: float | None = None
    state_band: str = ""
    blockers: list[str] = field(default_factory=list)
    activation_phase: int = 1
    activation_mode: str = "immediate"
    conditional_gate: str = ""
    surface_role: str = "primary"
    target_cluster: str = "general"
    expected_depth: str = "medium"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def family_allowed_for_host_stage(host_state: dict, target: str, family: str, *, is_sensitive_host: Callable[[str], bool], host_warmup_complete: Callable[[dict, str], bool]) -> bool:
    fam = str(family or '').strip().lower()
    if not is_sensitive_host(target):
        return True
    if fam in {'tls_assessment', 'recon', 'historical_url_mining'}:
        return True
    if host_warmup_complete(host_state, target):
        return True
    try:
        host = host_from_target(target)
        hs = ((host_state or {}).get('hosts') or {}).get(host) or {}
        if not isinstance(hs, dict):
            hs = {}
    except Exception:
        hs = {}
    preferred_stages = {str(x or '').strip().lower() for x in (hs.get('preferred_stages') or []) if str(x or '').strip()}
    target_types_seen = {str(x or '').strip().lower() for x in (hs.get('target_types_seen') or []) if str(x or '').strip()}
    target_surface = {str(x or '').strip().lower() for x in (hs.get('target_surface_rationale') or []) if str(x or '').strip()}
    if fam in {'authz', 'idor'} and (
        'control_boundary_confirmation' in preferred_stages
        or 'bounded_exploit_proof' in preferred_stages
        or 'authenticated_or_boundary_mapping' in target_surface
        or bool(target_types_seen & {'api', 'auth', 'integration'})
    ):
        return True
    if fam in {'auth_flow', 'workflow', 'logic', 'state_transition'} and (
        'state_transition_confirmation' in preferred_stages
        or 'bounded_exploit_proof' in preferred_stages
        or bool(target_types_seen & {'web', 'api', 'auth', 'integration'})
    ):
        return True
    if fam in {'tls_assessment', 'content_discovery'} and (
        'report_artifact_capture' in preferred_stages
        or 'artifact_capture' in target_surface
        or bool(target_types_seen & {'static', 'support'})
    ):
        return True
    return False


def host_health_blocked(host: str, mode: str, host_success_count: dict[str, int], host_fail_count: dict[str, int]) -> bool:
    h = str(host or '')
    if not h:
        return False
    if str(mode).lower() not in {'deep', 'followup'}:
        return False
    succ = host_success_count.get(h, 0)
    fail = host_fail_count.get(h, 0)
    total = succ + fail
    if total < 6:
        return False
    fail_rate = fail / max(1, total)
    return fail_rate >= 0.75 and succ <= 1




def evaluate_host_execution_gate(
    *,
    objective: str,
    target: str,
    mode: str,
    task_family: str,
    unresolved_hosts: set[str],
    host_dns_cache: dict[str, bool],
    host_cooldown_until: dict[str, float],
    autodiscover_deep_skip: bool,
    host_state: dict,
    deep_budget: dict[tuple[str, str], int],
    host_success_count: dict[str, int],
    host_fail_count: dict[str, int],
    family_allowed_fn: Callable[[dict, str, str], bool],
    runtime_task: dict[str, Any] | None = None,
    planner_feedback: dict[str, Any] | None = None,
    host_health_cooldown_sec: int = 900,
    deep_budget_cap_per_host_family: int = 2,
) -> HostExecutionGate:
    h = host_from_target(target)
    fam = str(task_family or '').strip().lower()
    if not fam:
        try:
            fam = attack_family(objective, target, str(task_family or ''))
        except TypeError:
            fam = attack_family(objective, target)
    fam = str(fam or 'generic').strip().lower()
    state_band = ''
    host_risk_band = ''
    host_capability_state = ''
    try:
        hs = ((host_state or {}).get('hosts') or {}).get(h) or {}
        if isinstance(hs, dict):
            state_band = str(hs.get('state_band') or hs.get('state') or '')
            host_risk_band = str(hs.get('risk_band') or '')
            host_capability_state = str(hs.get('capability_state') or '')
    except Exception:
        state_band = ''
        host_risk_band = ''
        host_capability_state = ''

    planner_ctx = planner_gate_context(runtime_task)

    if h in unresolved_hosts:
        return HostExecutionGate(False, h, fam, reason_code='unresolved_host', detail=f'host={h}', state_band=state_band, blockers=['dns_unresolved_cached'], **planner_ctx)

    if not host_dns_cache.get(h, is_resolvable_host(h)):
        unresolved_hosts.add(h)
        return HostExecutionGate(False, h, fam, reason_code='dns_unresolved', detail=f'host={h}', state_band=state_band, blockers=['dns_lookup_failed'], **planner_ctx)

    host_health_cooldown_sec = max(60, int(host_health_cooldown_sec or 900))
    deep_budget_cap_per_host_family = max(1, int(deep_budget_cap_per_host_family or 2))
    now_ts = datetime.now(timezone.utc).timestamp()
    if h in host_cooldown_until and now_ts < float(host_cooldown_until.get(h, 0.0) or 0.0):
        until = float(host_cooldown_until.get(h, 0.0) or 0.0)
        return HostExecutionGate(False, h, fam, reason_code='host_cooldown', detail=f'host={h};mode={mode}', cooldown_until=until, state_band=state_band, blockers=['cooldown_active'], **planner_ctx)

    if autodiscover_deep_skip and 'autodiscover.' in h and str(mode).lower() in {'deep', 'followup'}:
        return HostExecutionGate(False, h, fam, reason_code='autodiscover_deep_skip', detail=f'host={h};mode={mode};reason=high_transport_noise', state_band=state_band, blockers=['autodiscover_transport_noise'], **planner_ctx)

    if host_health_blocked(h, mode, host_success_count, host_fail_count):
        cooldown_until = now_ts + host_health_cooldown_sec
        host_cooldown_until[h] = cooldown_until
        return HostExecutionGate(False, h, fam, reason_code='host_health_skip', detail=f'host={h};mode={mode};reason=high_fail_rate', cooldown_until=cooldown_until, state_band=state_band, blockers=['host_health_fail_rate'], **planner_ctx)

    if not family_allowed_fn(host_state, target, fam):
        return HostExecutionGate(False, h, fam, reason_code='warmup_gate_skip', detail=f'host={h};family={fam};reason=sensitive_host_needs_low_noise_first', state_band=state_band, blockers=['warmup_gate'], **planner_ctx)

    planner_decision = planner_runtime_admission_decision(
        runtime_task=runtime_task,
        host_state=host_state,
        host=h,
        host_success_count=host_success_count,
        mode=mode,
        planner_feedback=planner_feedback,
    )
    planner_ctx = planner_decision.context if isinstance(planner_decision.context, dict) else planner_ctx
    if not planner_decision.allowed:
        return HostExecutionGate(False, h, fam, reason_code=planner_decision.reason_code, detail=f'host={h};family={fam};{planner_decision.detail}', state_band=state_band, blockers=list(planner_decision.blockers or []), **planner_ctx)

    if str(mode).lower() in {'deep', 'followup'}:
        kfb = (h, fam)
        if deep_budget.get(kfb, 0) >= deep_budget_cap_per_host_family:
            return HostExecutionGate(False, h, fam, reason_code='deep_budget_skip', detail=f'host={h};family={fam};budget={deep_budget_cap_per_host_family}', state_band=state_band, blockers=['deep_budget'], **planner_ctx)

    return HostExecutionGate(True, h, fam, reason_code='allowed', detail=f'host={h};family={fam}', state_band=state_band, **planner_ctx)
