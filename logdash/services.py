from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


PIPELINE_PRESET_FIELDS = {
    'plan_adaptation_mode',
    'planner_reconsult_mode',
    'workflow_escalation_profile',
    'confirm_jobs_profile',
    'family_decay_mode',
}


def load_pipeline_config_effective_posture(config: Dict[str, object] | None) -> Dict[str, object]:
    cfg = config if isinstance(config, dict) else {}
    preset_values = {key: str(cfg.get(key) or '').strip() for key in sorted(PIPELINE_PRESET_FIELDS)}
    preset_map = {
        'exploratory_efficient': {
            'plan_adaptation_mode': 'balanced',
            'planner_reconsult_mode': 'balanced',
            'workflow_escalation_profile': 'conservative',
            'confirm_jobs_profile': 'conservative',
            'family_decay_mode': 'standard',
        },
        'exploratory_max': {
            'plan_adaptation_mode': 'aggressive',
            'planner_reconsult_mode': 'aggressive',
            'workflow_escalation_profile': 'aggressive',
            'confirm_jobs_profile': 'aggressive',
            'family_decay_mode': 'light',
        },
        'confirmation_heavy': {
            'plan_adaptation_mode': 'frozen',
            'planner_reconsult_mode': 'conservative',
            'workflow_escalation_profile': 'balanced',
            'confirm_jobs_profile': 'aggressive',
            'family_decay_mode': 'standard',
        },
    }
    preset_key = ''
    for key, expected in preset_map.items():
        if all(preset_values.get(field, '') == value for field, value in expected.items()):
            preset_key = key
            break
    return {
        'preset_key': preset_key,
        'is_custom': not bool(preset_key),
        'profile_fields': preset_values,
        'source': 'normalized_pipeline_config',
    }

from json_state_io import atomic_write_json, safe_load_json_list, safe_load_json_object
from runtime_state_schemas import normalize_host_state, normalize_runtime_campaign_state, normalize_runtime_plan_meta, normalize_runtime_snapshot
from semantic_lineage import ensure_semantic_lineage_summary  # type: ignore
from time_utils import utc_now_iso


CAMPAIGN_SCOPED_SNAPSHOT_SECTIONS = (
    'campaign',
    'plan',
    'latest_run',
    'queues',
    'telemetry',
    'hosts',
    'economics',
)


def load_runtime_snapshot(runtime_snapshot_path: Path) -> Dict[str, object]:
    data, _meta = safe_load_json_object(
        runtime_snapshot_path,
        {},
        normalizer=normalize_runtime_snapshot,
        description='runtime_snapshot',
    )
    return data



def selected_runtime_snapshot_view(runtime: Dict[str, object] | None, selected_campaign_key: str) -> Dict[str, object]:
    runtime = runtime if isinstance(runtime, dict) else {}
    snapshot = runtime.get('snapshot') if isinstance(runtime.get('snapshot'), dict) else {}
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    snap_campaign = snapshot.get('campaign') if isinstance(snapshot.get('campaign'), dict) else {}
    snap_plan = snapshot.get('plan') if isinstance(snapshot.get('plan'), dict) else {}
    snap_latest = snapshot.get('latest_run') if isinstance(snapshot.get('latest_run'), dict) else {}
    snap_queues = snapshot.get('queues') if isinstance(snapshot.get('queues'), dict) else {}
    snap_telemetry = snapshot.get('telemetry') if isinstance(snapshot.get('telemetry'), dict) else {}
    snap_hosts = snapshot.get('hosts') if isinstance(snapshot.get('hosts'), dict) else {}
    snap_economics = snapshot.get('economics') if isinstance(snapshot.get('economics'), dict) else {}
    selected_key = str(selected_campaign_key or '').strip()
    snapshot_key = str(snap_campaign.get('campaign_key') or '').strip()
    snapshot_matches_selected = bool(selected_key and snapshot_key == selected_key)
    if not snapshot_matches_selected:
        snap_campaign = {}
        snap_plan = {}
        snap_latest = {}
        snap_queues = {}
        snap_telemetry = {}
        snap_hosts = {}
        snap_economics = {}
    filtered_snapshot = dict(snapshot)
    if not snapshot_matches_selected:
        for key in CAMPAIGN_SCOPED_SNAPSHOT_SECTIONS:
            filtered_snapshot[key] = {}
    return {
        'snapshot': snapshot,
        'filtered_snapshot': filtered_snapshot,
        'snap_campaign': snap_campaign,
        'snap_plan': snap_plan,
        'snap_latest': snap_latest,
        'snap_queues': snap_queues,
        'snap_telemetry': snap_telemetry,
        'snap_hosts': snap_hosts,
        'snap_economics': snap_economics,
        'selected_campaign_key': selected_key,
        'snapshot_campaign_key': snapshot_key,
        'snapshot_matches_selected': snapshot_matches_selected,
    }



def projection_source_label(*, snapshot: Dict[str, object] | None = None, fallback: str = 'legacy') -> str:
    snap = snapshot if isinstance(snapshot, dict) else {}
    return 'snapshot' if bool(snap) else fallback



def build_selected_campaign_projection(runtime: Dict[str, object] | None, selected_view: Dict[str, object] | None, state: Dict[str, object] | None = None) -> Dict[str, object]:
    runtime = runtime if isinstance(runtime, dict) else {}
    selected_view = selected_view if isinstance(selected_view, dict) else {}
    state = state if isinstance(state, dict) else {}
    plan = runtime.get("runtime_plan", {}) if isinstance(runtime.get("runtime_plan"), dict) else {}
    selected_key = str(selected_view.get('selected_campaign_key') or '').strip()
    filtered_snapshot = selected_view.get('filtered_snapshot') if isinstance(selected_view.get('filtered_snapshot'), dict) else {}
    snapshot_matches_selected = bool(selected_view.get('snapshot_matches_selected', False))
    snap_plan = selected_view.get('snap_plan') if isinstance(selected_view.get('snap_plan'), dict) else {}
    generated = int(plan.get("generated") or plan.get("prepared_attacks") or state.get("prepared_attacks") or 0) if selected_key else 0
    target_count = int(plan.get("target_count") or plan.get("input_total") or state.get("planner_scope_targets") or 0) if selected_key else 0
    if snap_plan:
        generated = int(snap_plan.get("generated") or snap_plan.get("prepared_attacks") or generated)
        target_count = int(snap_plan.get("target_count") or snap_plan.get("input_total") or target_count)
    return {
        'selected_campaign_key': selected_key,
        'runtime': runtime,
        'snapshot': filtered_snapshot if snapshot_matches_selected else {},
        'filtered_snapshot': filtered_snapshot,
        'runtime_plan': plan,
        'snap_campaign': selected_view.get('snap_campaign') if isinstance(selected_view.get('snap_campaign'), dict) else {},
        'snap_plan': snap_plan,
        'snap_latest': selected_view.get('snap_latest') if isinstance(selected_view.get('snap_latest'), dict) else {},
        'snap_queues': selected_view.get('snap_queues') if isinstance(selected_view.get('snap_queues'), dict) else {},
        'snap_telemetry': selected_view.get('snap_telemetry') if isinstance(selected_view.get('snap_telemetry'), dict) else {},
        'snap_hosts': selected_view.get('snap_hosts') if isinstance(selected_view.get('snap_hosts'), dict) else {},
        'snap_economics': selected_view.get('snap_economics') if isinstance(selected_view.get('snap_economics'), dict) else {},
        'generated': generated,
        'target_count': target_count,
        'snapshot_matches_selected': snapshot_matches_selected,
    }



def build_agents_status_payload(*, state: Dict[str, object], runtime: Dict[str, object], selected_campaign_key: str, model_map: Dict[str, str] | None, snap_campaign: Dict[str, object], snap_plan: Dict[str, object], snap_latest: Dict[str, object]) -> Dict[str, object]:
    model_map = model_map if isinstance(model_map, dict) else {}
    run_state = str(state.get('state', 'idle') or 'idle').lower()
    active_state = 'working' if run_state in {'running', 'in_progress', 'active'} else ('idle' if run_state == 'paused' else run_state)
    planner_status = 'ready' if str(selected_campaign_key or '').strip() else 'idle'
    orchestrator_items = int(snap_campaign.get('executed') or 0)
    planner_items = int(snap_plan.get('target_count') or 0)
    if not orchestrator_items:
        auto = runtime.get('auto_campaign') if isinstance(runtime.get('auto_campaign'), dict) else {}
        orchestrator_items = int(auto.get('executed') or state.get('prepared_attacks') or 0)
    if not planner_items:
        plan = runtime.get('runtime_plan') if isinstance(runtime.get('runtime_plan'), dict) else {}
        planner_items = int(plan.get('target_count') or state.get('planner_scope_targets') or 0)
    last_runtime_action = str(snap_latest.get('decision_effective_status') or snap_latest.get('mode') or 'campaign loop')
    using_snapshot = bool(snap_campaign or snap_plan or snap_latest)
    return {
        'orchestrator': {'name': 'ORCHESTRATOR', 'state': run_state or 'idle', 'label': run_state or 'idle', 'model': 'runtime/control-plane', 'description': 'Campaign lifecycle, queue state and runtime coordination.', 'last_action': last_runtime_action, 'items_processed': orchestrator_items, 'failure_count': 0, 'source': projection_source_label(snapshot=(snap_campaign if using_snapshot else {}), fallback='selected_campaign_runtime')},
        'planner': {'name': 'PLANNER', 'state': planner_status, 'label': planner_status, 'model': model_map.get('planner', 'deterministic/blueprint'), 'description': 'Deterministic blueprint and runtime-plan preparation.', 'last_action': 'prepare blueprint/runtime plan', 'items_processed': planner_items, 'failure_count': 0, 'source': projection_source_label(snapshot=(snap_plan if using_snapshot else {}), fallback='selected_campaign_runtime')},
        'brain': {'name': 'BRAIN', 'state': active_state or 'idle', 'label': active_state or 'idle', 'model': model_map.get('brain', 'Qwen/Qwen3-235B-A22B-Instruct-2507-TEE'), 'description': 'Proposes one bounded next action using planning-safe tools.', 'last_action': 'propose next governed step', 'items_processed': 0, 'failure_count': 0},
        'auditor': {'name': 'AUDITOR', 'state': active_state or 'idle', 'label': active_state or 'idle', 'model': model_map.get('auditor', 'openai/gpt-oss-120b-TEE'), 'description': 'Scope, policy, auth and aggression gate before execution.', 'last_action': 'audit action spec', 'items_processed': 0, 'failure_count': 0},
        'execution': {'name': 'EXECUTION', 'state': active_state or 'idle', 'label': active_state or 'idle', 'model': 'python/execution-engine', 'description': 'Builds final argv and runs only allowed commands.', 'last_action': 'execute approved command', 'items_processed': 0, 'failure_count': 0},
        'analysis': {'name': 'ANALYSIS', 'state': active_state or 'idle', 'label': active_state or 'idle', 'model': model_map.get('analysis', 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B'), 'description': 'Interprets artifacts into evidence, signals and findings.', 'last_action': 'summarize observed artifacts', 'items_processed': 0, 'failure_count': 0},
        'light': {'name': 'LIGHT', 'state': active_state or 'idle', 'label': active_state or 'idle', 'model': model_map.get('light', 'NousResearch/Hermes-4-14B'), 'description': 'Formats concise operator-facing summaries without changing meaning.', 'last_action': 'format concise summary', 'items_processed': 0, 'failure_count': 0},
    }



def build_campaign_info_payload(*, state: Dict[str, object], current: Dict[str, object], settings: Dict[str, object] | None, cred_status: str, cred_status_detail: str, latest_payload: Dict[str, object] | None, latest_vectors: List[Dict[str, object]] | None) -> Dict[str, object]:
    state = state if isinstance(state, dict) else {}
    current = current if isinstance(current, dict) else {}
    settings = settings if isinstance(settings, dict) else {}
    latest_payload = latest_payload if isinstance(latest_payload, dict) else {}
    latest_vectors = latest_vectors if isinstance(latest_vectors, list) else []
    snapshot = current.get('snapshot') if isinstance(current.get('snapshot'), dict) else {}
    snap_campaign = current.get('snap_campaign') if isinstance(current.get('snap_campaign'), dict) else {}
    snap_plan = current.get('snap_plan') if isinstance(current.get('snap_plan'), dict) else {}
    snap_latest = current.get('snap_latest') if isinstance(current.get('snap_latest'), dict) else {}
    plan = current.get('runtime_plan') if isinstance(current.get('runtime_plan'), dict) else {}
    quality = plan.get('quality', {}) if isinstance(plan.get('quality'), dict) else {}
    latest_row = latest_vectors[-1] if latest_vectors else {}
    generated = int(current.get('generated') or 0)
    target_count = int(current.get('target_count') or 0)
    selected_campaign_key = str(current.get('selected_campaign_key') or '').strip()
    runtime_ok = bool(selected_campaign_key) and generated > 0
    runtime_err = '-' if runtime_ok else str(state.get('runtime_plan_error_preview') or 'runtime_plan_missing')
    executed = int(snap_campaign.get('executed') or latest_payload.get('executed') or len(latest_vectors) or 0)
    out = dict(state)
    out.update(settings)
    out.update({
        'run_id': str(latest_payload.get('run_id') or plan.get('plan_revision') or plan.get('generated_at') or '-'),
        'aggression_recommended_default': settings.get('aggression_override', out.get('aggression_effective', 3)),
        'aggression_effective': out.get('aggression_effective', settings.get('aggression_override', 3)),
        'credentials_required': bool(out.get('credentials_required', False)),
        'campaign_name': out.get('selected_campaign_name') or '-',
        'executed': executed,
        'session_executed': executed,
        'session_max_runs': int(snap_campaign.get('max_runs') or settings.get('max_runs') or latest_payload.get('max_runs') or 0),
        'current_target': str(snap_latest.get('target') or latest_row.get('target') or '-'),
        'current_agent': str(snap_latest.get('mode') or latest_row.get('mode') or ('runtime' if selected_campaign_key else '-')),
        'started_at': str(snap_campaign.get('started_at') or latest_payload.get('started_at') or (plan.get('generated_at') if selected_campaign_key else '-') or '-'),
        'blueprint_hash': str(snap_plan.get('plan_hash') or plan.get('plan_hash') or plan.get('blueprint_hash') or '-')[:16],
        'planner_scope_targets': target_count,
        'prepared_attacks': generated,
        'runtime_plan_ok': runtime_ok,
        'runtime_plan_error_preview': runtime_err,
        'runtime_plan_revision': snap_plan.get('plan_revision') or plan.get('plan_revision'),
        'runtime_plan_quality_grade': quality.get('grade'),
        'runtime_plan_quality_score': quality.get('score'),
        'runtime_snapshot_source': projection_source_label(snapshot=snapshot, fallback='legacy'),
        'runtime_snapshot_updated': str(snap_campaign.get('updated_at') or '-'),
        'credentials_status': cred_status,
        'credentials_status_detail': cred_status_detail,
    })
    return out



def build_evaluation_summary_payload(*, payload: Dict[str, object], archive_summary: Dict[str, object], metrics: Dict[str, object], replay: Dict[str, object]) -> Dict[str, object]:
    payload = payload if isinstance(payload, dict) else {}
    archive_summary = archive_summary if isinstance(archive_summary, dict) else {}
    summary_eval = payload.get('evaluation') if isinstance(payload.get('evaluation'), dict) else {}
    archive_eval = archive_summary.get('evaluation') if isinstance(archive_summary.get('evaluation'), dict) else {}
    replay_results = replay.get('results') if isinstance(replay.get('results'), list) else []
    excluded_by_reason = ((metrics.get('totals') or {}).get('excluded_by_reason') if isinstance(metrics.get('totals'), dict) else {}) or {}
    top_exclusions = sorted([(str(k), int(v)) for k, v in dict(excluded_by_reason).items()], key=lambda item: (-item[1], item[0]))[:4]
    divergence_examples = []
    for row in replay_results:
        if not isinstance(row, dict) or str(row.get('status') or '') != 'divergent':
            continue
        reasons = [str(x) for x in list(row.get('divergence_reasons') or []) if str(x).strip()]
        run_identity = row.get('run_identity') if isinstance(row.get('run_identity'), dict) else {}
        divergence_examples.append({
            'target': run_identity.get('target') or '-',
            'objective': run_identity.get('objective') or '-',
            'reasons': reasons[:3],
        })
        if len(divergence_examples) >= 3:
            break
    source = 'archive'
    if not metrics and summary_eval:
        metrics = dict(summary_eval.get('metrics') or {}) if isinstance(summary_eval.get('metrics'), dict) else {}
        source = 'summary_payload'
    if not metrics and archive_eval:
        metrics = dict(archive_eval.get('metrics') or {}) if isinstance(archive_eval.get('metrics'), dict) else {}
        source = 'archive_summary'
    status_counts = replay.get('status_counts') if isinstance(replay.get('status_counts'), dict) else (summary_eval.get('status_counts') if isinstance(summary_eval.get('status_counts'), dict) else archive_eval.get('status_counts') if isinstance(archive_eval.get('status_counts'), dict) else {})
    bundle_count = replay.get('bundle_count') if isinstance(replay, dict) else (summary_eval.get('bundle_count') if isinstance(summary_eval, dict) else archive_eval.get('bundle_count') if isinstance(archive_eval, dict) else 0)
    variant = replay.get('variant') if isinstance(replay.get('variant'), dict) else {}
    return {
        'ok': bool(metrics),
        'error': '' if metrics else 'no_evaluation_metrics',
        'source': source,
        'run_id': str(payload.get('run_id') or archive_summary.get('run_id') or ''),
        'dataset_id': summary_eval.get('dataset_id') or archive_eval.get('dataset_id') or replay.get('dataset_id') or '-',
        'bundle_count': int(bundle_count or 0),
        'status_counts': status_counts or {},
        'variant': variant,
        'yield_metrics': dict(metrics.get('yield_metrics') or {}),
        'governance_metrics': dict(metrics.get('governance_metrics') or {}),
        'auth_state_metrics': dict(metrics.get('auth_state_metrics') or {}),
        'semantic_class_metrics': dict(metrics.get('semantic_class_metrics') or {}),
        'queue_metrics': dict(metrics.get('queue_metrics') or {}),
        'totals': dict(metrics.get('totals') or {}),
        'top_exclusions': [{'reason': key, 'count': count} for key, count in top_exclusions],
        'divergence_examples': divergence_examples,
    }


def build_runtime_health_payload(*, runtime: Dict[str, object], snapshot: Dict[str, object], snap_campaign: Dict[str, object], snap_plan: Dict[str, object], snap_queues: Dict[str, object], snap_telemetry: Dict[str, object], snap_latest: Dict[str, object], stdout_bytes: int, stderr_bytes: int) -> Dict[str, object]:
    runtime = runtime if isinstance(runtime, dict) else {}
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    snap_campaign = snap_campaign if isinstance(snap_campaign, dict) else {}
    snap_plan = snap_plan if isinstance(snap_plan, dict) else {}
    snap_queues = snap_queues if isinstance(snap_queues, dict) else {}
    snap_telemetry = snap_telemetry if isinstance(snap_telemetry, dict) else {}
    snap_latest = snap_latest if isinstance(snap_latest, dict) else {}
    lineage_summary = ensure_semantic_lineage_summary(
        summary=(snap_latest.get('semantic_lineage_summary') if isinstance(snap_latest.get('semantic_lineage_summary'), dict) else {}),
        lineage=(snap_latest.get('semantic_lineage') if isinstance(snap_latest.get('semantic_lineage'), dict) else {}),
        task=snap_latest,
        runtime_task=(snap_latest.get('runtime_task') if isinstance(snap_latest.get('runtime_task'), dict) else {}),
        source='runtime_health',
    )
    plan = runtime.get('runtime_plan', {}) if isinstance(runtime.get('runtime_plan'), dict) else {}
    auto = runtime.get('auto_campaign', {}) if isinstance(runtime.get('auto_campaign'), dict) else {}
    return {
        'auto_state_updated': snap_campaign.get('updated_at') or auto.get('updated_at') or '-',
        'runtime_plan_updated': snap_plan.get('generated_at') or plan.get('updated_at') or plan.get('generated_at') or '-',
        'brain_invalid_tool_attempts': 0,
        'brain_fallback_used': 0,
        'analysis_contract_failures': 0,
        'light_fallback_used': 0,
        'auditor_reason_codes': {},
        'stdout_bytes': stdout_bytes,
        'stderr_bytes': stderr_bytes,
        'runtime_snapshot_source': projection_source_label(snapshot=snapshot, fallback='legacy'),
        'runtime_snapshot_updated': snap_campaign.get('updated_at') or '-',
        'queue_followups': int(snap_queues.get('followup_count', 0) or 0),
        'queue_precision': int(snap_queues.get('precision_count', 0) or 0),
        'precheck_skip_count': int(snap_telemetry.get('precheck_skip_count', 0) or 0),
        'dns_skip_total': int(snap_telemetry.get('dns_skip_total', 0) or 0),
        'host_cooldown_skip_total': int(snap_telemetry.get('host_cooldown_skip_total', 0) or 0),
        'execution_gate_skip_total': int(snap_telemetry.get('execution_gate_skip_total', 0) or 0),
        'action_type_count': dict(snap_telemetry.get('action_type_count') or {}),
        'semantic_loss_total': int(snap_telemetry.get('semantic_loss_total', 0) or 0),
        'semantic_loss_by_class': dict(snap_telemetry.get('semantic_loss_by_class') or {}),
        'semantic_rereview_total': int(snap_telemetry.get('semantic_rereview_total', 0) or 0),
        'latest_action_type': lineage_summary.get('action_type') or ((snap_latest.get('brain_reasoning_summary') or {}).get('action_type') if isinstance(snap_latest.get('brain_reasoning_summary'), dict) else '-') or '-',
        'latest_expected_signal_observed': (snap_latest.get('analysis_contract') or {}).get('expected_signal_observed') if isinstance(snap_latest.get('analysis_contract'), dict) else '-',
        'latest_semantic_loss_class': ((snap_latest.get('semantic_loss_policy') or {}).get('loss_class') if isinstance(snap_latest.get('semantic_loss_policy'), dict) else '-'),
        'latest_semantic_loss_response': ((snap_latest.get('semantic_loss_policy') or {}).get('policy_response') if isinstance(snap_latest.get('semantic_loss_policy'), dict) else '-'),
        'latest_approved_under_degradation': ((snap_latest.get('semantic_loss_policy') or {}).get('approved_under_degradation') if isinstance(snap_latest.get('semantic_loss_policy'), dict) else False),
        'latest_semantic_rereview_required': bool(snap_latest.get('semantic_loss_rereview_required', False)),
        'latest_semantic_rereview_completed': bool(snap_latest.get('semantic_loss_rereview_completed', False)),
        'latest_semantic_rereview_decision': snap_latest.get('semantic_loss_rereview_decision') or '-',
        'latest_target': snap_latest.get('target') or '-',
        'latest_mode': snap_latest.get('mode') or '-',
        'latest_capability': lineage_summary.get('capability') or snap_latest.get('capability') or ((snap_latest.get('brain_reasoning_summary') or {}).get('capability') if isinstance(snap_latest.get('brain_reasoning_summary'), dict) else '-') or '-',
        'latest_capability_lane': snap_latest.get('capability_lane') or ((snap_latest.get('runtime_task') or {}).get('capability_lane') if isinstance(snap_latest.get('runtime_task'), dict) else '-') or '-',
        'latest_lineage_hash': lineage_summary.get('lineage_sha256') or '-',
        'latest_lineage_stage': lineage_summary.get('current_stage') or '-',
        'latest_lineage_next_stage': lineage_summary.get('next_stage') or '-',
        'latest_lineage_action_type': lineage_summary.get('action_type') or '-',
        'latest_lineage_capability': lineage_summary.get('capability') or '-',
        'latest_experiment_intent_id': snap_latest.get('experiment_intent_id') or ((snap_latest.get('runtime_task') or {}).get('experiment_intent_id') if isinstance(snap_latest.get('runtime_task'), dict) else '-') or '-',
        'latest_success_model': ((snap_latest.get('success_semantics') or {}).get('success_model') if isinstance(snap_latest.get('success_semantics'), dict) else '-') or '-',
        'latest_adaptation_reason': ((snap_latest.get('adaptation_signal') or {}).get('reason') if isinstance(snap_latest.get('adaptation_signal'), dict) else '-') or '-',
        'latest_decision_effective_status': snap_latest.get('decision_effective_status') or '-',
        'runtime_plan_revision': snap_plan.get('plan_revision') or plan.get('plan_revision') or '-',
        'runtime_plan_hash': str(snap_plan.get('plan_hash') or plan.get('plan_hash') or '-')[:16],
    }


def _state_meta_source(meta: Dict[str, object] | None, *, ok_label: str, missing_label: str, invalid_label: str) -> str:
    status = str((meta or {}).get('status') or '').strip().lower()
    if status == 'missing':
        return missing_label
    if status in {'invalid_json', 'invalid_shape'}:
        return invalid_label
    return ok_label



def load_runtime_state(reports_dir: Path, runtime_snapshot_path: Path | None = None) -> Dict[str, object]:
    out: Dict[str, object] = {
        "auto_campaign": {},
        "runtime_plan": {},
        "snapshot": {},
        "sources": {
            "auto_campaign": "missing",
            "runtime_plan": "missing",
            "runtime_plan_quality": "missing",
            "snapshot": "missing",
            "snapshot_latest_run_lineage": "missing",
        },
    }
    auto_path = reports_dir / ".auto_campaign.state.json"
    plan_meta = reports_dir / ".runtime_plan.meta.json"
    auto_campaign, auto_meta = safe_load_json_object(
        auto_path,
        {},
        normalizer=normalize_runtime_campaign_state,
        description='auto_campaign_state',
    )
    out["auto_campaign"] = auto_campaign if isinstance(auto_campaign, dict) else {}
    out["sources"]["auto_campaign"] = _state_meta_source(auto_meta, ok_label='normalized_auto_campaign_state', missing_label='missing', invalid_label='invalid')

    runtime_plan, runtime_plan_meta = safe_load_json_object(
        plan_meta,
        {},
        normalizer=normalize_runtime_plan_meta,
        description='runtime_plan_meta',
    )
    out["runtime_plan"] = runtime_plan if isinstance(runtime_plan, dict) else {}
    out["sources"]["runtime_plan"] = _state_meta_source(runtime_plan_meta, ok_label='normalized_runtime_plan_meta', missing_label='missing', invalid_label='invalid')
    try:
        rp = out.get("runtime_plan", {}) if isinstance(out.get("runtime_plan"), dict) else {}
        if isinstance(rp, dict):
            quality = rp.get("quality") if isinstance(rp.get("quality"), dict) else {}
            if quality:
                out["sources"]["runtime_plan_quality"] = str(quality.get("source") or "runtime_plan")
            else:
                attacks = int(rp.get("prepared_attacks") or rp.get("generated") or 0)
                targets = int(rp.get("target_count") or rp.get("input_total") or 0)
                score = 0
                if attacks > 0 and targets > 0:
                    density = min(1.0, attacks / max(1, targets * 8))
                    score = int(round(100 * density))
                grade = "A" if score >= 80 else ("B" if score >= 60 else ("C" if score >= 40 else ("D" if score >= 20 else "E")))
                rp["quality"] = {"grade": grade, "score": score, "source": "computed_fallback"}
                out["runtime_plan"] = rp
                out["sources"]["runtime_plan_quality"] = "computed_fallback"
    except Exception:
        pass
    if runtime_snapshot_path is not None:
        out['snapshot'] = load_runtime_snapshot(runtime_snapshot_path)
        out['sources']['snapshot'] = 'normalized_snapshot_file'
        snap = out.get('snapshot') if isinstance(out.get('snapshot'), dict) else {}
        latest = snap.get('latest_run') if isinstance(snap.get('latest_run'), dict) else {}
        if latest:
            latest_lineage = latest.get('semantic_lineage') if isinstance(latest.get('semantic_lineage'), dict) else {}
            latest['semantic_lineage_summary'] = ensure_semantic_lineage_summary(
                summary=(latest.get('semantic_lineage_summary') if isinstance(latest.get('semantic_lineage_summary'), dict) else {}),
                lineage=latest_lineage,
                task=latest,
                runtime_task=(latest.get('runtime_task') if isinstance(latest.get('runtime_task'), dict) else {}),
                source='logdash_runtime_state',
            )
            out['sources']['snapshot_latest_run_lineage'] = 'normalized_lineage_summary'
            snap['latest_run'] = latest
            out['snapshot'] = snap
    return out


def runtime_plan_status(reports_dir: Path) -> Dict[str, object]:
    plan_meta = reports_dir / ".runtime_plan.meta.json"
    meta, load_meta = safe_load_json_object(
        plan_meta,
        {},
        normalizer=normalize_runtime_plan_meta,
        description='runtime_plan_meta',
    )
    status = str(load_meta.get('status') or '').strip().lower()
    if status == 'missing':
        return {"ok": False, "error": "runtime_plan_meta_missing", "source": 'missing'}
    if status in {'invalid_json', 'invalid_shape'} or not isinstance(meta, dict):
        return {"ok": False, "error": "runtime_plan_meta_invalid", "source": 'invalid'}
    generated = meta.get("generated")
    if isinstance(generated, int) and generated <= 0:
        return {"ok": False, "error": "runtime_plan_empty"}
    if generated is None:
        return {"ok": False, "error": "runtime_plan_missing_generated"}
    return {"ok": True, "error": "-", "meta": meta, "source": 'normalized_runtime_plan_meta'}


def compute_plan_counts(runtime_plan_path: Path) -> Dict[str, int]:
    attacks = 0
    hosts = set()
    def _normalize(raw: object) -> list[dict[str, object]]:
        if not isinstance(raw, list):
            raise TypeError('expected list')
        return [row for row in raw if isinstance(row, dict)]
    data, _meta = safe_load_json_list(
        runtime_plan_path,
        [],
        normalizer=_normalize,
        description='runtime_plan_entries',
    )
    if isinstance(data, list):
        attacks = len(data)
        for e in data:
            if not isinstance(e, dict):
                continue
            t = str(e.get("target") or "")
            try:
                from urllib.parse import urlparse
                h = (urlparse(t).hostname or "").strip().lower()
            except Exception:
                h = ""
            if h:
                hosts.add(h)
    return {"prepared_attacks": attacks, "scope_targets": len(hosts)}


def runtime_process_alive(runtime_pid_path: Path) -> tuple[bool, str]:
    if runtime_pid_path.exists():
        try:
            pid = int(str(runtime_pid_path.read_text(encoding="utf-8")).strip())
            if pid > 0:
                os.kill(pid, 0)
                return (True, str(pid))
        except Exception:
            pass
    try:
        for proc_dir in Path('/proc').iterdir():
            name = proc_dir.name
            if not name.isdigit():
                continue
            cmdline = proc_dir / 'cmdline'
            if not cmdline.exists():
                continue
            try:
                raw = cmdline.read_bytes()
            except Exception:
                continue
            txt = raw.replace(b'\x00', b' ').decode('utf-8', errors='ignore').lower()
            if 'auto_campaign_runner.py' in txt:
                return (True, name)
    except Exception:
        pass
    return (False, '-')


def latest_log_for(conn, *, tor: str):
    try:
        return conn.execute("SELECT * FROM logs WHERE tor = ? ORDER BY id DESC LIMIT 1", (tor,)).fetchone()
    except Exception:
        return None


def load_host_state(host_state_path: Path) -> Dict[str, object]:
    data, meta = safe_load_json_object(
        host_state_path,
        {},
        normalizer=normalize_host_state,
        description='host_state',
    )
    status = str(meta.get('status') or '').strip().lower()
    if status == 'missing':
        return {"hosts": {}, "_source": "missing_host_state"}
    if status in {'invalid_json', 'invalid_shape'} or not isinstance(data, dict):
        return {"hosts": {}, "_source": "invalid_host_state"}
    out = dict(data)
    out.setdefault('_source', 'normalized_host_state_file')
    return out


def write_runtime_state_file(reports_dir: Path, runtime_state_path: Path, STATE: Dict[str, object], *, paused: bool | None = None) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    current, _meta = safe_load_json_object(
        runtime_state_path,
        {},
        normalizer=normalize_runtime_campaign_state,
        description='runtime_state_file',
    )
    current = current if isinstance(current, dict) else {}
    if paused is None:
        paused = str(STATE.get("state", "idle")).lower() == "paused"
    current["paused"] = bool(paused)
    current["stopped"] = str(STATE.get("state", "idle")).lower() == "stopped"
    current["owner_override"] = bool(STATE.get("owner_override", False))
    current["updated_at"] = utc_now_iso()
    try:
        runtime_state_path.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        pass


def sync_pid_file(reports_dir: Path, runtime_pid_path: Path, alive: bool, pid: str) -> None:
    try:
        if alive and str(pid).isdigit():
            reports_dir.mkdir(parents=True, exist_ok=True)
            runtime_pid_path.write_text(str(pid), encoding="utf-8")
        elif runtime_pid_path.exists():
            runtime_pid_path.unlink()
    except Exception:
        pass


def refresh_runtime_state(STATE: Dict[str, object], *, get_conn, runtime_state_path: Path, runtime_pid_path: Path, reports_dir: Path) -> None:
    alive, pid = runtime_process_alive(runtime_pid_path)
    paused = False
    stopped_flag = False
    owner_override = bool(STATE.get("owner_override", False))
    st, _meta = safe_load_json_object(
        runtime_state_path,
        {},
        normalizer=normalize_runtime_campaign_state,
        description='runtime_state_file',
    )
    if isinstance(st, dict):
        paused = bool(st.get("paused", False))
        stopped_flag = bool(st.get("stopped", False))
        owner_override = bool(st.get("owner_override", owner_override))
    recent_activity = False
    try:
        conn = get_conn()
        row = latest_log_for(conn, tor="AUTO_CAMPAIGN") or latest_log_for(conn, tor="PIPELINE")
        conn.close()
        if row:
            st = str(row["status"] or "").lower()
            ts = datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))
            age = (datetime.now(ts.tzinfo) - ts).total_seconds()
            if age <= 120 and st in {"in_progress", "running", "active", "pending", "warning", "retry_1", "retry_2", "retry_3"}:
                recent_activity = True
    except Exception:
        pass
    STATE["pid"] = pid
    STATE["owner_override"] = owner_override
    if alive or (recent_activity and not stopped_flag):
        STATE["state"] = "paused" if paused else "running"
    else:
        if stopped_flag:
            STATE["state"] = "stopped"
        elif str(STATE.get("state", "idle")).lower() in {"running", "paused", "in_progress", "active"}:
            STATE["state"] = "idle"
    sync_pid_file(reports_dir, runtime_pid_path, alive, pid)
    write_runtime_state_file(reports_dir, runtime_state_path, STATE, paused=(str(STATE.get("state", "idle")).lower() == "paused"))


def load_owner_approval_actions(owner_approval_actions_path: Path) -> Dict[str, object]:
    d, meta = safe_load_json_object(
        owner_approval_actions_path,
        {"approved_ids": [], "deleted_ids": []},
        description='owner_approval_actions',
    )
    status = str(meta.get('status') or '').strip().lower()
    if status in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(d, dict):
        return {"approved_ids": [], "deleted_ids": []}
    d.setdefault("approved_ids", [])
    d.setdefault("deleted_ids", [])
    return d


def save_owner_approval_actions(reports_dir: Path, owner_approval_actions_path: Path, data: Dict[str, object]) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    owner_approval_actions_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def owner_approval_row_ids(get_conn, init_db) -> list[int]:
    keywords = ["owner_approval_required", "owner approval", "credentials_require_owner_approval"]
    conn = get_conn()
    try:
        like = " OR ".join(["decision LIKE ?", "result LIKE ?"] * len(keywords))
        params=[]
        for k in keywords:
            params.extend([f"%{k}%", f"%{k}%"])
        try:
            rows = conn.execute(f"SELECT id FROM logs WHERE ({like}) ORDER BY id DESC", tuple(params)).fetchall()
        except Exception:
            init_db()
            rows = conn.execute(f"SELECT id FROM logs WHERE ({like}) ORDER BY id DESC", tuple(params)).fetchall()
        return [int(r[0]) for r in rows]
    finally:
        conn.close()


def fetch_filtered_logs(get_conn, init_db, page: int, per_page: int, keywords: List[str], exclude_ids: List[int] | None = None) -> Dict[str, object]:
    conn = get_conn()
    offset = (page - 1) * per_page
    like = " OR ".join(["decision LIKE ?", "result LIKE ?"] * len(keywords))
    params: List[object] = []
    for k in keywords:
        params.extend([f"%{k}%", f"%{k}%"])
    where = f"({like})"
    q_params = list(params)
    if exclude_ids:
        ph = ",".join(["?"] * len(exclude_ids))
        where += f" AND id NOT IN ({ph})"
        q_params.extend(list(exclude_ids))
    try:
        rows = conn.execute(f"SELECT * FROM logs WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?", (*q_params, per_page, offset)).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM logs WHERE {where}", tuple(q_params)).fetchone()[0]
    except Exception:
        init_db()
        rows = []
        total = 0
    conn.close()
    items: List[Dict[str, object]] = []
    for row in rows:
        ts = datetime.fromisoformat(row["timestamp"])
        items.append({"id": int(row["id"]), "date": ts.strftime("%Y-%m-%d"), "time": ts.strftime("%H:%M:%S"), "agent": row["agent"], "decision": row["decision"], "status": row["status"], "raw_status": row["status"], "result": row["result"]})
    return {"page": page, "per_page": per_page, "total": total, "total_pages": max(1, (total + per_page - 1) // per_page), "items": items}


def _normalize_queue_lane_item(row: object, default_lane: str) -> Dict[str, object] | None:
    if not isinstance(row, dict):
        return None
    clean = dict(row)
    lane = str(clean.get('queue_lane') or clean.get('_queue_lane') or default_lane).strip().lower()
    if lane not in {'followup', 'precision'}:
        lane = default_lane
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



def _normalize_queue_lane_items(rows: object, default_lane: str) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    if not isinstance(rows, list):
        return out
    for row in rows:
        clean = _normalize_queue_lane_item(row, default_lane=default_lane)
        if clean is not None:
            out.append(clean)
    return out



def load_queue_state(queue_state_path: Path, runtime_snapshot_path: Path | None = None) -> Dict[str, object]:
    if runtime_snapshot_path is not None and runtime_snapshot_path.exists():
        snapshot = load_runtime_snapshot(runtime_snapshot_path)
        queues = snapshot.get('queues') if isinstance(snapshot.get('queues'), dict) else {}
        telemetry = snapshot.get('telemetry') if isinstance(snapshot.get('telemetry'), dict) else {}
        if queues:
            return {
                'followup_queue': _normalize_queue_lane_items(queues.get('followup_queue'), default_lane='followup'),
                'precision_queue': _normalize_queue_lane_items(queues.get('precision_queue'), default_lane='precision'),
                'precheck_skip_count': int(telemetry.get('precheck_skip_count', 0) or 0),
                'dns_skip_count': dict(telemetry.get('dns_skip_count') or {}),
                'host_cooldown_skip_count': dict(telemetry.get('host_cooldown_skip_count') or {}),
                'execution_gate_skip_count': dict(telemetry.get('execution_gate_skip_count') or {}),
                'saved_at': queues.get('saved_at'),
                'source': 'runtime_snapshot',
            }
    data, meta = safe_load_json_object(
        queue_state_path,
        {"followup_queue": [], "precision_queue": []},
        description='queue_state',
    )
    status = str(meta.get('status') or '').strip().lower()
    if status in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(data, dict):
        return {"followup_queue": [], "precision_queue": []}
    data.setdefault('source', 'normalized_queue_state')
    data['followup_queue'] = _normalize_queue_lane_items(data.get('followup_queue'), default_lane='followup')
    data['precision_queue'] = _normalize_queue_lane_items(data.get('precision_queue'), default_lane='precision')
    return data


def load_latest_blueprint(selected_campaign_key: str, planner_registry_root: Path) -> Dict[str, object] | None:
    if not selected_campaign_key:
        return None
    latest = planner_registry_root / selected_campaign_key / "latest.json"
    meta, load_meta = safe_load_json_object(
        latest,
        {},
        description='planner_registry_latest',
    )
    status = str(load_meta.get('status') or '').strip().lower()
    if status in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(meta, dict):
        return None
    path = meta.get("path")
    if not path:
        return None
    return {"meta": meta, "path": Path(path), "campaign_key": selected_campaign_key}


def read_tail(path: Path, lines: int = 120) -> str:
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(content[-lines:])
    except Exception:
        return ""


def list_campaign_registry_items(planner_registry_root: Path, active_key: str) -> List[Dict[str, object]]:
    items: List[Dict[str, object]] = []
    if not planner_registry_root.exists():
        return items
    for d in sorted([p for p in planner_registry_root.iterdir() if p.is_dir()], key=lambda p: p.name):
        latest = d / "latest.json"
        meta, latest_meta = safe_load_json_object(
            latest,
            {},
            description='planner_registry_latest',
        )
        if str(latest_meta.get('status') or '').strip().lower() in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(meta, dict):
            continue
        try:
            raw_path = Path(str(meta.get("path") or ""))
            resolved = raw_path if raw_path.is_absolute() else (latest.parent / raw_path)
            bp_path = resolved / "blueprint.json"
            approved = False
            version = int(meta.get("version") or 0)
            campaign_name = d.name
            bp, bp_meta = safe_load_json_object(
                bp_path,
                {},
                description='planner_blueprint',
            )
            if str(bp_meta.get('status') or '').strip().lower() not in {'missing', 'invalid_json', 'invalid_shape'} and isinstance(bp, dict):
                op = bp.get("operator_approval") if isinstance(bp.get("operator_approval"), dict) else {}
                approved = bool(op.get("approved", False))
                campaign_name = str(meta.get("campaign_name") or bp.get("campaign_name_template") or campaign_name)
            items.append({"key": d.name, "campaign_name": campaign_name, "version": version, "approved": approved, "active": (d.name == active_key)})
        except Exception:
            continue
    return items
