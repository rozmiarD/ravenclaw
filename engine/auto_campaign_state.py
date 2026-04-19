from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from json_state_io import atomic_write_json  # type: ignore
from runtime_economics_aggregate import aggregate_runtime_economics  # type: ignore
from decision_quality import aggregate_campaign_learning  # type: ignore
from campaign_state_machine import derive_campaign_stage  # type: ignore
from runtime_admission_reporting import execution_gate_summary_payload  # type: ignore
from semantic_lineage import ensure_semantic_lineage, ensure_semantic_lineage_summary  # type: ignore


def _action_type_metrics(runs: list[dict]) -> dict[str, Any]:
    recent = [r for r in (runs or []) if isinstance(r, dict)]
    counts: dict[str, int] = {}
    semantic_loss = 0
    semantic_loss_by_class: dict[str, int] = {}
    semantic_rereview_total = 0
    for run in recent:
        action_type = str((run.get('brain_reasoning_summary') or {}).get('action_type') or (run.get('brain') or {}).get('action_type') or 'single_probe')
        counts[action_type] = counts.get(action_type, 0) + 1
        compiler = run.get('engine_compiler') if isinstance(run.get('engine_compiler'), dict) else {}
        policy = compiler.get('semantic_loss_policy') if isinstance(compiler.get('semantic_loss_policy'), dict) else {}
        if bool(compiler.get('semantic_loss_detected', False)):
            semantic_loss += 1
        loss_class = str(policy.get('loss_class') or '').strip().lower()
        if loss_class and loss_class != 'none':
            semantic_loss_by_class[loss_class] = semantic_loss_by_class.get(loss_class, 0) + 1
        if str(policy.get('policy_response') or '').strip().lower() == 'auditor_rereview' or bool(run.get('semantic_loss_rereview_required', False)):
            semantic_rereview_total += 1
    return {
        'action_type_count': counts,
        'semantic_loss_total': semantic_loss,
        'semantic_loss_by_class': semantic_loss_by_class,
        'semantic_rereview_total': semantic_rereview_total,
    }


def _contamination_metrics(runs: list[dict]) -> dict[str, Any]:
    recent = [r for r in (runs or []) if isinstance(r, dict)]
    status_count: dict[str, int] = {}
    tag_count: dict[str, int] = {}
    request_shape_count: dict[str, int] = {}
    excluded = 0
    for run in recent:
        contamination = run.get('run_contamination') if isinstance(run.get('run_contamination'), dict) else {}
        status = str(contamination.get('status') or 'clean')
        status_count[status] = int(status_count.get(status, 0)) + 1
        if bool(contamination.get('learning_excluded', False)):
            excluded += 1
        for tag in list(contamination.get('tags') or []):
            tag_count[str(tag)] = int(tag_count.get(str(tag), 0)) + 1
        req = run.get('request_shape_hygiene') if isinstance(run.get('request_shape_hygiene'), dict) else {}
        req_status = str(req.get('request_shape_hygiene_status') or 'unknown')
        request_shape_count[req_status] = int(request_shape_count.get(req_status, 0)) + 1
    return {
        'status_count': status_count,
        'tag_count': tag_count,
        'request_shape_hygiene_count': request_shape_count,
        'learning_excluded_total': int(excluded),
    }


def _latest_run_summary(runs: list[dict]) -> dict[str, Any]:
    if not runs:
        return {}
    latest = runs[-1] if isinstance(runs[-1], dict) else {}
    if not isinstance(latest, dict):
        return {}
    brain = latest.get('brain') if isinstance(latest.get('brain'), dict) else {}
    summary = latest.get('brain_reasoning_summary') if isinstance(latest.get('brain_reasoning_summary'), dict) else {}
    runtime_task = latest.get('runtime_task') if isinstance(latest.get('runtime_task'), dict) else {}
    if isinstance(runtime_task, dict):
        runtime_task = dict(runtime_task)
        runtime_task.pop('_queue_lane', None)
        if 'queue_lane' not in runtime_task:
            runtime_task['queue_lane'] = _normalized_queue_lane(latest, default='followup')
    adaptation_signal = latest.get('adaptation_signal') if isinstance(latest.get('adaptation_signal'), dict) else {}
    signal_contract = latest.get('signal_contract') if isinstance(latest.get('signal_contract'), dict) else {}
    semantic_lineage = ensure_semantic_lineage(
        lineage=(latest.get('semantic_lineage') if isinstance(latest.get('semantic_lineage'), dict) else (runtime_task.get('semantic_lineage') if isinstance(runtime_task.get('semantic_lineage'), dict) else {})),
        task=latest,
        runtime_task=runtime_task,
        source='runtime_snapshot_latest_run',
    )
    semantic_lineage_summary = ensure_semantic_lineage_summary(
        summary=(latest.get('semantic_lineage_summary') if isinstance(latest.get('semantic_lineage_summary'), dict) else {}),
        lineage=semantic_lineage,
    )
    return {
        'index': latest.get('index'),
        'objective': latest.get('objective'),
        'target': latest.get('target'),
        'mode': latest.get('mode'),
        'engine_status': latest.get('engine_status'),
        'classification': latest.get('classification'),
        'promising': latest.get('promising'),
        'finding_lifecycle': latest.get('finding_lifecycle'),
        'decision_effective_status': latest.get('decision_effective_status'),
        'decision_effective_summary': latest.get('decision_effective_summary'),
        'decision_selected_action': latest.get('decision_selected_action'),
        'decision_selection_reason': latest.get('decision_selection_reason'),
        'decision_selected_secondary_action': latest.get('decision_selected_secondary_action'),
        'decision_secondary_selection_reason': latest.get('decision_secondary_selection_reason'),
        'decision_effective_secondary_action': latest.get('decision_effective_secondary_action'),
        'runtime_decision': latest.get('runtime_decision') if isinstance(latest.get('runtime_decision'), dict) else {},
        'host_state_band': latest.get('host_state_band'),
        'host_regeneration_reason': latest.get('host_regeneration_reason'),
        'capability': str(brain.get('capability') or summary.get('capability') or ''),
        'capability_lane': str(latest.get('capability_lane') or runtime_task.get('capability_lane') or ''),
        'experiment_intent_id': str(latest.get('experiment_intent_id') or runtime_task.get('experiment_intent_id') or ''),
        'runtime_task': runtime_task,
        'semantic_lineage': semantic_lineage,
        'semantic_lineage_summary': semantic_lineage_summary,
        'execution_gate': latest.get('execution_gate') if isinstance(latest.get('execution_gate'), dict) else {},
        'brain_reasoning_summary': summary,
        'brain': brain,
        'engine_compiler': latest.get('engine_compiler') if isinstance(latest.get('engine_compiler'), dict) else {},
        'analysis_contract': latest.get('analysis_contract') if isinstance(latest.get('analysis_contract'), dict) else {},
        'success_semantics': latest.get('success_semantics') if isinstance(latest.get('success_semantics'), dict) else {},
        'signal_contract': signal_contract,
        'decision_economics': latest.get('decision_economics') if isinstance(latest.get('decision_economics'), dict) else {},
        'runtime_utility': latest.get('runtime_utility') if isinstance(latest.get('runtime_utility'), dict) else {},
        'run_contamination': latest.get('run_contamination') if isinstance(latest.get('run_contamination'), dict) else {},
        'request_shape_hygiene': latest.get('request_shape_hygiene') if isinstance(latest.get('request_shape_hygiene'), dict) else {},
        'adaptation_signal': adaptation_signal,
        'semantic_loss_policy': latest.get('semantic_loss_policy') if isinstance(latest.get('semantic_loss_policy'), dict) else (((latest.get('engine_compiler') or {}).get('semantic_loss_policy') or {}) if isinstance(latest.get('engine_compiler'), dict) else {}),
        'semantic_loss_rereview_required': bool(latest.get('semantic_loss_rereview_required', False)),
        'semantic_loss_rereview_completed': bool(latest.get('semantic_loss_rereview_completed', False)),
        'semantic_loss_rereview_decision': latest.get('semantic_loss_rereview_decision', ''),
        'campaign_state': latest.get('campaign_state') if isinstance(latest.get('campaign_state'), dict) else {},
    }


def _normalized_queue_lane(row: dict[str, Any], default: str = 'followup') -> str:
    lane = str(row.get('queue_lane') or row.get('_queue_lane') or default).strip().lower()
    return lane if lane in {'followup', 'precision'} else default



def _sanitize_queue_item(row: dict[str, Any], *, default_lane: str) -> dict[str, Any]:
    clean = dict(row)
    lane = _normalized_queue_lane(clean, default=default_lane)
    clean['queue_lane'] = lane
    clean.pop('_queue_lane', None)
    runtime_task = clean.get('runtime_task') if isinstance(clean.get('runtime_task'), dict) else None
    if runtime_task is not None:
        task_clean = dict(runtime_task)
        task_clean.pop('_queue_lane', None)
        if 'queue_lane' not in task_clean:
            task_clean['queue_lane'] = lane
        clean['runtime_task'] = task_clean
    return clean



def _sanitize_queue_items(items: list[dict] | None, *, default_lane: str, limit: int = 200) -> list[dict[str, Any]]:
    return [_sanitize_queue_item(row, default_lane=default_lane) for row in [r for r in (items or []) if isinstance(r, dict)][:limit]]



def _queue_preview(items: list[dict] | None, *, default_lane: str, limit: int = 30) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in _sanitize_queue_items(items, default_lane=default_lane, limit=limit):
        runtime_task = row.get('runtime_task') if isinstance(row.get('runtime_task'), dict) else {}
        success_meta = row.get('success_semantics') if isinstance(row.get('success_semantics'), dict) else (runtime_task.get('success_semantics') if isinstance(runtime_task.get('success_semantics'), dict) else {})
        out.append({
            'objective': row.get('objective'),
            'target': row.get('target'),
            'mode': row.get('mode'),
            'queue_lane': row.get('queue_lane') or default_lane,
            'task_family': row.get('task_family') or runtime_task.get('task_family') or '-',
            'capability_lane': row.get('capability_lane') or runtime_task.get('capability_lane') or '-',
            'experiment_intent_id': row.get('experiment_intent_id') or runtime_task.get('experiment_intent_id') or '',
            'success_model': str(success_meta.get('success_model') or ''),
            'priority_score': row.get('priority_score') or runtime_task.get('priority_score') or 0,
            'utility_score': row.get('utility_score') or runtime_task.get('utility_score') or 0,
        })
    return out


def _plan_summary(runtime_plan_meta: dict[str, Any] | None) -> dict[str, Any]:
    meta = runtime_plan_meta if isinstance(runtime_plan_meta, dict) else {}
    return {
        'plan_revision': int(meta.get('plan_revision', 0) or 0),
        'plan_hash': str(meta.get('plan_hash') or ''),
        'generated': int(meta.get('generated') or meta.get('prepared_attacks') or 0),
        'prepared_attacks': int(meta.get('prepared_attacks') or meta.get('generated') or 0),
        'target_count': int(meta.get('target_count') or meta.get('input_total') or 0),
        'input_total': int(meta.get('input_total') or meta.get('target_count') or 0),
        'generated_at': str(meta.get('generated_at') or ''),
        'regeneration_reason': str(meta.get('regeneration_reason') or ''),
        'diff_reason': str(meta.get('diff_reason') or ''),
        'added_tasks': int(meta.get('added_tasks') or 0),
        'deprecated_tasks': int(meta.get('deprecated_tasks') or 0),
        'material_change': bool(meta.get('material_change', False)),
        'skipped': bool(meta.get('skipped', False)),
        'added_examples': list(meta.get('added_examples') or [])[:8],
        'deprecated_examples': list(meta.get('deprecated_examples') or [])[:8],
    }


def _host_summary(host_state: dict[str, Any] | None, now_iso: str) -> dict[str, Any]:
    data = host_state if isinstance(host_state, dict) else {}
    hosts = data.get('hosts') if isinstance(data.get('hosts'), dict) else {}
    clean_hosts: dict[str, dict[str, Any]] = {}
    items: list[dict[str, Any]] = []
    for host, meta in hosts.items():
        if not isinstance(meta, dict):
            continue
        clean = dict(meta)
        clean_hosts[str(host)] = clean
        items.append({
            'host': str(host),
            'state': clean.get('state', 'active'),
            'state_band': clean.get('state_band', clean.get('state', 'active')),
            'promise_score': clean.get('promise_score', 0),
            'noise_score': clean.get('noise_score', 0),
            'evidence_density': clean.get('evidence_density', 0),
            'novelty_score': clean.get('novelty_score', 0),
            'preferred_families': list(clean.get('preferred_families') or []),
            'suppressed_families': list(clean.get('suppressed_families') or []),
            'last_success_family': clean.get('last_success_family', '-'),
            'last_transition_reason': clean.get('last_transition_reason', ''),
            'last_transition_at_runs': clean.get('last_transition_at_runs', 0),
        })
    items.sort(key=lambda row: (-float(row.get('promise_score') or 0), float(row.get('noise_score') or 0), str(row.get('host') or '')))
    return {
        'count': len(clean_hosts),
        'updated_at': now_iso,
        'items': items[:100],
        'by_host': clean_hosts,
    }


def build_runtime_snapshot(
    *,
    campaign_key: str,
    campaign_validation: dict,
    run_started,
    max_runs: int,
    time_budget_min: int,
    retry_policy: str,
    runs: list[dict],
    followup_queue: list[dict],
    precision_queue: list[dict],
    precheck_skip_count: int = 0,
    dns_skip_count: dict[str, int] | None = None,
    host_cooldown_skip_count: dict[str, int] | None = None,
    execution_gate_skip_count: dict[str, int] | None = None,
    quality_telemetry: dict[str, int] | None = None,
    runtime_plan_meta: dict[str, Any] | None = None,
    host_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dns_skip_count = dict(dns_skip_count or {})
    host_cooldown_skip_count = dict(host_cooldown_skip_count or {})
    execution_gate_skip_count = dict(execution_gate_skip_count or {})
    quality_telemetry = dict(quality_telemetry or {})
    now_iso = datetime.now(timezone.utc).isoformat()
    latest = _latest_run_summary(runs)
    economics = aggregate_runtime_economics(runs)
    action_metrics = _action_type_metrics(runs)
    learning = aggregate_campaign_learning(runs)
    contamination = _contamination_metrics(runs)
    return {
        'campaign': {
            'campaign_key': campaign_key,
            'campaign_validation': campaign_validation,
            'started_at': run_started.isoformat(),
            'max_runs': int(max_runs),
            'time_budget_min': int(time_budget_min),
            'retry_policy': retry_policy,
            'executed': int(len(runs)),
            'campaign_stage': derive_campaign_stage(runs=runs),
            'updated_at': now_iso,
        },
        'plan': _plan_summary(runtime_plan_meta),
        'queues': {
            'followup_queue': _sanitize_queue_items(followup_queue, default_lane='followup', limit=200),
            'precision_queue': _sanitize_queue_items(precision_queue, default_lane='precision', limit=200),
            'followup_preview': _queue_preview(followup_queue, default_lane='followup', limit=40),
            'precision_preview': _queue_preview(precision_queue, default_lane='precision', limit=40),
            'followup_count': int(len(followup_queue)),
            'precision_count': int(len(precision_queue)),
            'saved_at': now_iso,
        },
        'telemetry': {
            'precheck_skip_count': int(precheck_skip_count or 0),
            'dns_skip_count': dns_skip_count,
            'dns_skip_total': int(sum(int(v) for v in dns_skip_count.values())),
            'host_cooldown_skip_count': host_cooldown_skip_count,
            'host_cooldown_skip_total': int(sum(int(v) for v in host_cooldown_skip_count.values())),
            'execution_gate_skip_count': execution_gate_skip_count,
            'execution_gate_skip_total': int(sum(int(v) for v in execution_gate_skip_count.values())),
            'quality_telemetry': quality_telemetry,
            'contamination': contamination,
            'action_type_count': dict(action_metrics.get('action_type_count') or {}),
            'semantic_loss_total': int(action_metrics.get('semantic_loss_total', 0) or 0),
            'semantic_loss_by_class': dict(action_metrics.get('semantic_loss_by_class') or {}),
            'semantic_rereview_total': int(action_metrics.get('semantic_rereview_total', 0) or 0),
        },
        'economics': economics,
        'learning': learning,
        'hosts': _host_summary(host_state, now_iso),
        'latest_run': latest,
    }


def persist_live_snapshot(
    *,
    out_path: str,
    save_queue_state_fn,
    campaign_key: str,
    campaign_validation: dict,
    run_started,
    max_runs: int,
    time_budget_min: int,
    retry_policy: str,
    runs: list[dict],
    followup_queue: list[dict],
    precision_queue: list[dict],
    precheck_skip_count: int = 0,
    dns_skip_count: dict[str, int] | None = None,
    host_cooldown_skip_count: dict[str, int] | None = None,
    execution_gate_skip_count: dict[str, int] | None = None,
    quality_telemetry: dict[str, int] | None = None,
    runtime_snapshot_path: str | None = None,
    runtime_plan_meta: dict[str, Any] | None = None,
    host_state: dict[str, Any] | None = None,
) -> None:
    live = {
        "run_id": "live",
        "campaign_validation": campaign_validation,
        "started_at": run_started.isoformat(),
        "max_runs": max_runs,
        "time_budget_min": time_budget_min,
        "retry_policy": retry_policy,
        "executed": len(runs),
        "runs": runs,
    }
    atomic_write_json(Path(out_path), live, ensure_ascii=False, indent=2)
    queue_state = {
        "followup_queue": _sanitize_queue_items(followup_queue, default_lane='followup', limit=200),
        "precision_queue": _sanitize_queue_items(precision_queue, default_lane='precision', limit=200),
        "precheck_skip_count": int(precheck_skip_count or 0),
        "dns_skip_count": dict(dns_skip_count or {}),
        "host_cooldown_skip_count": dict(host_cooldown_skip_count or {}),
        "execution_gate_skip_count": dict(execution_gate_skip_count or {}),
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "campaign_key": campaign_key,
    }
    save_queue_state_fn(queue_state)
    if runtime_snapshot_path:
        try:
            snapshot = build_runtime_snapshot(
                campaign_key=campaign_key,
                campaign_validation=campaign_validation,
                run_started=run_started,
                max_runs=max_runs,
                time_budget_min=time_budget_min,
                retry_policy=retry_policy,
                runs=runs,
                followup_queue=followup_queue,
                precision_queue=precision_queue,
                precheck_skip_count=precheck_skip_count,
                dns_skip_count=dns_skip_count,
                host_cooldown_skip_count=host_cooldown_skip_count,
                execution_gate_skip_count=execution_gate_skip_count,
                quality_telemetry=quality_telemetry,
                runtime_plan_meta=runtime_plan_meta,
                host_state=host_state,
            )
            sp = Path(runtime_snapshot_path)
            atomic_write_json(sp, snapshot, ensure_ascii=False, indent=2)
        except Exception:
            pass


def flush_skip_summaries(
    *,
    precheck_skip_count_ref: list[int],
    precheck_skip_examples_ref: list[str],
    dns_skip_count_ref: dict[str, int],
    host_cooldown_skip_count_ref: dict[str, int],
    log_event_fn,
    force: bool = False,
    execution_gate_skip_count_ref: dict[str, int] | None = None,
    execution_gate_skip_examples_ref: dict[str, list[str]] | None = None,
) -> None:
    precheck_skip_count = int(precheck_skip_count_ref[0] if precheck_skip_count_ref else 0)
    if precheck_skip_count > 0 and (force or precheck_skip_count >= 3):
        sample = "; ".join(precheck_skip_examples_ref[:2]) if precheck_skip_examples_ref else "-"
        log_event_fn(
            "AUTO_CAMPAIGN",
            "precheck_dedup_summary",
            "precheck",
            f"Skipped {precheck_skip_count} duplicate vectors in precheck (sample: {sample})",
            actor="auto_campaign",
        )
        precheck_skip_count_ref[0] = 0
        precheck_skip_examples_ref.clear()

    dns_total = sum(int(v) for v in dns_skip_count_ref.values())
    if dns_total > 0 and (force or dns_total >= 4):
        top = sorted(dns_skip_count_ref.items(), key=lambda kv: kv[1], reverse=True)[:3]
        sample = "; ".join(f"{h}:{c}" for h, c in top) if top else "-"
        log_event_fn(
            "AUTO_CAMPAIGN",
            "dns_skip_summary",
            "skipped",
            f"Skipped {dns_total} vectors due to unresolved DNS hosts (top: {sample})",
            actor="auto_campaign",
        )
        dns_skip_count_ref.clear()

    cool_total = sum(int(v) for v in host_cooldown_skip_count_ref.values())
    if cool_total > 0 and (force or cool_total >= 3):
        top = sorted(host_cooldown_skip_count_ref.items(), key=lambda kv: kv[1], reverse=True)[:3]
        sample = "; ".join(f"{h}:{c}" for h, c in top) if top else "-"
        log_event_fn(
            "AUTO_CAMPAIGN",
            "host_cooldown_summary",
            "skipped",
            f"Skipped {cool_total} vectors due to temporary host cooldown (top: {sample})",
            actor="auto_campaign",
        )
        host_cooldown_skip_count_ref.clear()

    gate_counts = execution_gate_skip_count_ref if isinstance(execution_gate_skip_count_ref, dict) else {}
    gate_examples = execution_gate_skip_examples_ref if isinstance(execution_gate_skip_examples_ref, dict) else {}
    gate_summary = execution_gate_summary_payload(gate_counts, gate_examples)
    gate_total = int(gate_summary['total'])
    if gate_total > 0 and (force or gate_total >= 3):
        log_event_fn(
            "AUTO_CAMPAIGN",
            "execution_gate_summary",
            "skipped",
            f"Skipped {gate_total} vectors due to execution gate blocks (top: {gate_summary['top_text']}; sample: {gate_summary['example_text']})",
            actor="auto_campaign",
        )
        gate_counts.clear()
        gate_examples.clear()
