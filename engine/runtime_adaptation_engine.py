from __future__ import annotations

from typing import Any, Dict


def _run_capability(run: Dict[str, Any] | None) -> str:
    payload = run if isinstance(run, dict) else {}
    brain = payload.get('brain') if isinstance(payload.get('brain'), dict) else {}
    summary = payload.get('brain_reasoning_summary') if isinstance(payload.get('brain_reasoning_summary'), dict) else {}
    return str(brain.get('capability') or summary.get('capability') or '').strip().lower()


def build_adaptation_signal(*, host_update: Dict[str, Any] | None, runs_count: int, run_info: Dict[str, Any] | None = None, recent_runs: list[dict] | None = None) -> Dict[str, Any]:
    update = host_update if isinstance(host_update, dict) else {}
    current_run = run_info if isinstance(run_info, dict) else {}
    recent = [r for r in (recent_runs or []) if isinstance(r, dict)]
    reason = str(update.get('regeneration_reason') or '').strip()
    source = 'host_update' if reason else 'none'
    should_regenerate = bool(reason)
    capability = _run_capability(current_run)
    capability_summary = {'capability': capability, 'recent_runs': 0, 'promising_runs': 0, 'partial_or_better_runs': 0}
    if capability and recent:
        recent_cap_runs = [r for r in recent[-18:] if _run_capability(r) == capability]
        capability_summary['recent_runs'] = len(recent_cap_runs)
        capability_summary['promising_runs'] = sum(1 for r in recent_cap_runs if bool(r.get('workflow_promotable', r.get('promising', False))))
        capability_summary['partial_or_better_runs'] = sum(1 for r in recent_cap_runs if str(((r.get('signal_contract') or {}).get('success_outcome') or {}).get('status') or r.get('success_criteria_eval') or '').strip().lower() in {'met', 'partial'})
        if not should_regenerate and len(recent_cap_runs) >= 3 and capability_summary['promising_runs'] == 0 and capability_summary['partial_or_better_runs'] <= 1:
            reason = f'capability_lane_stalled:{capability}'
            source = 'capability_lane'
            should_regenerate = True
    if not should_regenerate and runs_count > 0 and runs_count % 12 == 0:
        reason = 'periodic_runtime_regen'
        source = 'periodic'
        should_regenerate = True
    return {
        'should_regenerate': should_regenerate,
        'reason': reason,
        'source': source,
        'capability_summary': capability_summary,
    }
