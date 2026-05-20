from __future__ import annotations

from typing import Any, Mapping

from govengine.runtime_shell import CONTROL_ACTIONS, control_action_from_host_action, queue_snapshot_from_lanes, validate_runtime_snapshot


RAVENCLAW_TO_GOVENGINE_RUN_STATE = {
    'idle': 'idle',
    'ready': 'idle',
    'running': 'running',
    'in_progress': 'running',
    'active': 'running',
    'paused': 'paused',
    'stopped': 'stopped',
    'cancelled': 'cancelled',
    'canceled': 'cancelled',
    'cooldown': 'cooldown',
    'blocked': 'blocked',
    'completed': 'completed',
}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: Any, default: str = '') -> str:
    out = str(value if value is not None else '').strip()
    return out if out else default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _selected_campaign_key(*, explicit: str = '', runtime_snapshot: Mapping[str, Any] | None = None, orchestrator_state: Mapping[str, Any] | None = None) -> str:
    if _text(explicit):
        return _text(explicit)
    snapshot = _mapping(runtime_snapshot)
    campaign = _mapping(snapshot.get('campaign'))
    if _text(campaign.get('campaign_key')):
        return _text(campaign.get('campaign_key'))
    orchestrator = _mapping(orchestrator_state)
    return _text(orchestrator.get('selected_campaign_key'))


def _run_id(selected_campaign_key: str, runtime_snapshot: Mapping[str, Any] | None = None) -> str:
    snapshot = _mapping(runtime_snapshot)
    campaign = _mapping(snapshot.get('campaign'))
    for value in (
        campaign.get('run_id'),
        campaign.get('campaign_key'),
        selected_campaign_key,
    ):
        if _text(value):
            return _text(value)
    return 'ravenclaw-runtime'


def _gov_state_for_runtime_state(runtime_state: str) -> tuple[str, tuple[str, ...]]:
    normalized = _text(runtime_state, 'idle').lower()
    gov_state = RAVENCLAW_TO_GOVENGINE_RUN_STATE.get(normalized, 'idle')
    gaps: tuple[str, ...] = ()
    if normalized not in RAVENCLAW_TO_GOVENGINE_RUN_STATE:
        gaps = ('unknown_ravenclaw_runtime_state_mapped_to_new',)
    return gov_state, gaps


def build_gov_run_state_projection(
    *,
    runtime_campaign_state: Mapping[str, Any] | None = None,
    selected_campaign_key: str = '',
    runtime_snapshot: Mapping[str, Any] | None = None,
    process_alive: bool | None = None,
) -> dict[str, Any]:
    """Project Ravenclaw runtime state into the GovEngine 0.3 runtime-shell shape.

    This is a host-owned compatibility projection. It intentionally preserves
    Ravenclaw's original state in metadata and records unknown-state gaps
    without moving runtime persistence or process control into GovEngine.
    """

    state = _mapping(runtime_campaign_state)
    snapshot = _mapping(runtime_snapshot)
    campaign = _mapping(snapshot.get('campaign'))
    selected_key = _selected_campaign_key(explicit=selected_campaign_key, runtime_snapshot=snapshot)
    runtime_state = _text(state.get('state') or campaign.get('state') or ('running' if process_alive else 'idle'), 'idle').lower()
    gov_state, gaps = _gov_state_for_runtime_state(runtime_state)
    metadata = {
        'source': 'ravenclaw_state_control_projection',
        'ravenclaw_runtime_state': runtime_state,
        'selected_campaign_key': selected_key,
        'process_alive': _bool_or_none(process_alive),
        'owner_override': bool(state.get('owner_override', False)),
        'updated_at': _text(state.get('updated_at') or campaign.get('updated_at')),
    }
    out = {
        'run_id': _run_id(selected_key, snapshot),
        'state': gov_state,
        'profile': 'ravenclaw-security',
        'metadata': metadata,
    }
    out['projection_gaps'] = list(gaps)
    return out


def build_gov_orchestrator_state_projection(
    *,
    orchestrator_state: Mapping[str, Any] | None = None,
    runtime_plan: Mapping[str, Any] | None = None,
    selected_campaign_key: str = '',
) -> dict[str, Any]:
    orchestrator = _mapping(orchestrator_state)
    plan = _mapping(runtime_plan)
    selected_key = _selected_campaign_key(explicit=selected_campaign_key, orchestrator_state=orchestrator)
    plan_id = _text(plan.get('plan_id') or plan.get('plan_revision') or plan.get('generated_at'))
    return {
        'artifact_type': 'gov_orchestrator_state_projection',
        'profile': 'ravenclaw-security',
        'selected_work_id': selected_key,
        'active_plan_id': plan_id,
        'active_plan_hash': _text(plan.get('plan_hash') or plan.get('blueprint_hash')),
        'lifecycle': 'selected' if selected_key else 'idle',
        'updated_at': _text(orchestrator.get('updated_at') or plan.get('generated_at')),
        'source': 'ravenclaw_state_control_projection',
        'non_claims': [
            'does_not_move_logdash_ui_into_govengine',
            'does_not_move_runtime_persistence_into_govengine',
        ],
    }


def build_gov_queue_snapshot_projection(
    *,
    queue_state: Mapping[str, Any] | None = None,
    run_id: str = 'ravenclaw-runtime',
    snapshot_id: str = '',
    preview_limit: int = 5,
) -> dict[str, Any]:
    queues = _mapping(queue_state)
    followup = [item for item in list(queues.get('followup_queue') or []) if isinstance(item, Mapping)]
    precision = [item for item in list(queues.get('precision_queue') or []) if isinstance(item, Mapping)]
    snapshot = queue_snapshot_from_lanes(
        snapshot_id=snapshot_id or f'{run_id}:queue',
        run_id=run_id,
        profile='ravenclaw-security',
        saved_at=_text(queues.get('saved_at')),
        lanes={
            'followup': [_queue_preview_item(item, lane='followup') for item in followup[:preview_limit]],
            'precision': [_queue_preview_item(item, lane='precision') for item in precision[:preview_limit]],
        },
        telemetry={
            'precheck_skip_count': _int(queues.get('precheck_skip_count')),
            'dns_skip_count': _mapping(queues.get('dns_skip_count')),
            'host_cooldown_skip_count': _mapping(queues.get('host_cooldown_skip_count')),
            'execution_gate_skip_count': _mapping(queues.get('execution_gate_skip_count')),
        },
        metadata={
            'source': _text(queues.get('source'), 'ravenclaw_queue_state'),
            'target_values_in_preview': False,
            'command_values_in_preview': False,
        },
    )
    return snapshot.as_dict()


def _queue_preview_item(item: Mapping[str, Any], *, lane: str) -> dict[str, Any]:
    row = _mapping(item)
    task = _mapping(row.get('runtime_task'))
    return {
        'lane': _text(row.get('queue_lane') or task.get('queue_lane'), lane),
        'task_family': _text(row.get('task_family') or task.get('task_family'), '-'),
        'capability_lane': _text(row.get('capability_lane') or task.get('capability_lane'), '-'),
        'priority_score': row.get('priority_score') or task.get('priority_score') or 0,
        'utility_score': row.get('utility_score') or task.get('utility_score') or 0,
        'has_target': bool(row.get('target') or task.get('target')),
        'target_redacted': bool(row.get('target') or task.get('target')),
    }


def build_gov_runtime_snapshot_projection(
    *,
    runtime_state: Mapping[str, Any] | None = None,
    queue_state: Mapping[str, Any] | None = None,
    selected_campaign_key: str = '',
) -> dict[str, Any]:
    runtime = _mapping(runtime_state)
    snapshot = _mapping(runtime.get('snapshot'))
    campaign = _mapping(snapshot.get('campaign'))
    plan = _mapping(snapshot.get('plan') or runtime.get('runtime_plan'))
    latest = _mapping(snapshot.get('latest_run'))
    auto = _mapping(runtime.get('auto_campaign'))
    selected_key = _selected_campaign_key(explicit=selected_campaign_key, runtime_snapshot=snapshot)
    run_state = build_gov_run_state_projection(
        runtime_campaign_state=auto,
        selected_campaign_key=selected_key,
        runtime_snapshot=snapshot,
    )
    queue_snapshot = build_gov_queue_snapshot_projection(
        queue_state=queue_state,
        run_id=str(run_state['run_id']),
    )
    runtime_shell = validate_runtime_snapshot({
        'snapshot_id': f'{run_state["run_id"]}:runtime',
        'run_id': run_state['run_id'],
        'state': run_state['state'],
        'queue_snapshot': queue_snapshot,
        'updated_at': _text(campaign.get('updated_at') or auto.get('updated_at')),
        'profile': 'ravenclaw-security',
        'non_claims': [
            'does_not_claim_govengine_runtime_storage',
            'does_not_claim_govengine_scheduler_ownership',
            'does_not_expose_raw_targets_or_commands_in_queue_preview',
        ],
        'metadata': {
            'source': 'ravenclaw_state_control_projection',
            'selected_campaign_key': selected_key,
        },
    })
    out = runtime_shell.as_dict()
    out.update({
        'artifact_type': 'gov_runtime_snapshot_projection',
        'selected_campaign_key': selected_key,
        'run_state': run_state,
        'plan_summary': {
            'plan_revision': plan.get('plan_revision'),
            'plan_hash': _text(plan.get('plan_hash')),
            'generated': _int(plan.get('generated') or plan.get('prepared_attacks')),
            'target_count': _int(plan.get('target_count') or plan.get('input_total')),
        },
        'run_summary': {
            'executed': _int(campaign.get('executed') or auto.get('executed')),
            'max_runs': _int(campaign.get('max_runs') or auto.get('max_runs')),
            'updated_at': _text(campaign.get('updated_at') or auto.get('updated_at')),
        },
        'queue_summary': queue_snapshot,
        'latest_transition': {
            'decision_effective_status': _text(latest.get('decision_effective_status')),
            'decision_selected_action': _text(latest.get('decision_selected_action')),
            'target_present': bool(latest.get('target')),
        },
        'sources': _mapping(runtime.get('sources')),
    })
    return out


def build_control_decision_projection(
    *,
    action: str,
    run_state_projection: Mapping[str, Any],
    reason_code: str = 'operator_requested',
) -> dict[str, Any]:
    """Project a Logdash/runtime control action into GovEngine 0.3 runtime shell.

    Known Logdash actions are now first-class `GovControlAction` records. Unknown
    actions are retained as `record_only` with an explicit projection gap.
    """

    requested = _text(action).lower()
    gaps: list[str] = []
    run_id = _text(run_state_projection.get('run_id'), 'ravenclaw-runtime')
    current_state = _mapping(run_state_projection.get('metadata')).get('ravenclaw_runtime_state')
    action_name = requested if requested in CONTROL_ACTIONS else 'record_only'
    if action_name == 'record_only' and requested != 'record_only':
        gaps.append('unknown_ravenclaw_control_action_recorded_only')
    checked = control_action_from_host_action(
        action=action_name,
        run_id=run_id,
        action_id=f'{run_id}:{requested or "unknown"}',
        reason_code=reason_code,
        profile='ravenclaw-security',
        metadata={
            'source': 'ravenclaw_state_control_projection',
            'requested_action': requested,
            'ravenclaw_current_state': _text(current_state),
        },
    )
    return {
        'source_action': requested,
        'control_action': checked.as_dict(),
        'projection_gaps': gaps,
    }
