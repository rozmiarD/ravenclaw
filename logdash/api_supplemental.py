from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

from flask import Flask, jsonify, request

_ENGINE_DIR = Path(__file__).resolve().parents[1] / 'engine'
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))
from evaluation_bundle import build_replay_bundle  # type: ignore
from evaluation_replay import replay_decision_bundle  # type: ignore
from runtime_economics_aggregate import aggregate_runtime_economics  # type: ignore
from runtime_trace_normalization import flatten_reason_map as normalize_trace_reason_map, list_preview as normalize_trace_list_preview, resolve_trace_decision, resolve_trace_ladder  # type: ignore
from semantic_lineage import ensure_semantic_lineage_summary  # type: ignore
from tool_registry import get_active_planner_profile_state, get_planner_visible_tools, get_tool_catalog, get_tool_registry_ui_state, save_tool_registry_state  # type: ignore
from policy_core import get_runtime_tool_policy  # type: ignore
from services import build_evaluation_summary_payload  # type: ignore
from context_contract import require_ctx
from json_state_io import safe_load_json_object  # type: ignore


_SUPPLEMENTAL_API_CTX_KEYS = (
    "STATE",
    "STATUS_CLASSES",
    "fetch_logs",
    "get_conn",
    "refresh_runtime_state",
    "load_runtime_state",
    "load_queue_state",
    "load_campaign_settings",
    "save_campaign_settings",
    "load_pipeline_config",
    "save_pipeline_config",
    "pipeline_config_meta",
    "load_latest_blueprint",
    "selected_campaign_key",
    "_list_campaign_registry_items",
    "load_host_state",
    "read_tail",
    "RUNTIME_STDOUT_PATH",
    "RUNTIME_STDERR_PATH",
    "_load_owner_approval_actions",
    "_save_owner_approval_actions",
    "_owner_approval_row_ids",
    "fetch_filtered_logs",
    "save_planner_ui_state",
    "load_planner_ui_state",
    "HOST_STATE_PATH",
    "save_orchestrator_state",
    "RUNTIME_PLAN_META_PATH",
    "PLANNER_REGISTRY_ROOT",
    "selected_runtime_snapshot_view",
    "build_campaign_info_payload",
    "build_runtime_health_payload",
    "build_selected_campaign_projection",
    "projection_source_label",
    "RUNTIME_SNAPSHOT_PATH",
    "RUNTIME_STATE_PATH",
    "RUNTIME_PID_PATH",
    "ENGINE_DIR",
    "WORKSPACE_DIR",
    "write_runtime_state_file",
)


def register_supplemental_api(app: Flask, ctx: dict[str, Any]) -> None:
    ctx = require_ctx(ctx, *_SUPPLEMENTAL_API_CTX_KEYS)
    STATE = ctx["STATE"]
    STATUS_CLASSES = ctx["STATUS_CLASSES"]
    fetch_logs = ctx["fetch_logs"]
    get_conn = ctx["get_conn"]
    refresh_runtime_state = ctx["refresh_runtime_state"]
    load_runtime_state = ctx["load_runtime_state"]
    load_queue_state = ctx["load_queue_state"]
    load_campaign_settings = ctx["load_campaign_settings"]
    save_campaign_settings = ctx["save_campaign_settings"]
    load_pipeline_config = ctx["load_pipeline_config"]
    save_pipeline_config = ctx["save_pipeline_config"]
    pipeline_config_meta = ctx["pipeline_config_meta"]
    load_latest_blueprint = ctx["load_latest_blueprint"]
    selected_campaign_key = ctx["selected_campaign_key"]
    _list_campaign_registry_items = ctx["_list_campaign_registry_items"]
    load_host_state = ctx["load_host_state"]
    read_tail = ctx["read_tail"]
    RUNTIME_STDOUT_PATH = ctx["RUNTIME_STDOUT_PATH"]
    RUNTIME_STDERR_PATH = ctx["RUNTIME_STDERR_PATH"]
    _load_owner_approval_actions = ctx["_load_owner_approval_actions"]
    _save_owner_approval_actions = ctx["_save_owner_approval_actions"]
    _owner_approval_row_ids = ctx["_owner_approval_row_ids"]
    fetch_filtered_logs = ctx["fetch_filtered_logs"]
    save_planner_ui_state = ctx["save_planner_ui_state"]
    load_planner_ui_state = ctx["load_planner_ui_state"]
    HOST_STATE_PATH = ctx["HOST_STATE_PATH"]
    save_orchestrator_state = ctx["save_orchestrator_state"]
    RUNTIME_PLAN_META_PATH = Path(ctx["RUNTIME_PLAN_META_PATH"])
    RUNTIME_PLAN_DELETE_PATHS = [Path(p) for p in (ctx.get("RUNTIME_PLAN_DELETE_PATHS") or [])]
    PLANNER_REGISTRY_ROOT = Path(ctx["PLANNER_REGISTRY_ROOT"])
    selected_runtime_snapshot_view = ctx["selected_runtime_snapshot_view"]
    build_campaign_info_payload = ctx["build_campaign_info_payload"]
    build_runtime_health_payload = ctx["build_runtime_health_payload"]
    build_selected_campaign_projection = ctx["build_selected_campaign_projection"]
    projection_source_label = ctx["projection_source_label"]
    RUNTIME_SNAPSHOT_PATH = Path(ctx["RUNTIME_SNAPSHOT_PATH"])
    RUNTIME_STATE_PATH = Path(ctx["RUNTIME_STATE_PATH"])
    RUNTIME_PID_PATH = Path(ctx["RUNTIME_PID_PATH"])
    ENGINE_DIR = Path(ctx["ENGINE_DIR"])
    WORKSPACE_DIR = Path(ctx["WORKSPACE_DIR"])
    PYTHON_BIN = str(ctx.get("PYTHON_BIN") or sys.executable)
    write_runtime_state_file = ctx["write_runtime_state_file"]
    runtime_alive_pid = ctx.get("runtime_alive_pid")
    spawn_runtime_process = ctx.get("spawn_runtime_process")
    terminate_runtime_process = ctx.get("terminate_runtime_process")

    def _runtime_alive_pid_fn() -> tuple[bool, int | None]:
        if callable(runtime_alive_pid):
            try:
                result = runtime_alive_pid()
                if isinstance(result, tuple) and len(result) == 2:
                    alive = bool(result[0])
                    pid_raw = result[1]
                    try:
                        pid_val = int(pid_raw) if pid_raw not in (None, '', '-') else None
                    except Exception:
                        pid_val = None
                    return alive, pid_val
            except Exception:
                pass
        return _runtime_alive_pid()

    def _spawn_runtime_process_fn(campaign_key: str) -> int:
        if callable(spawn_runtime_process):
            try:
                return int(spawn_runtime_process(campaign_key))
            except Exception:
                pass
        return int(_spawn_runtime_process(campaign_key))

    def _terminate_runtime_process_fn(pid: int) -> bool:
        if callable(terminate_runtime_process):
            try:
                return bool(terminate_runtime_process(pid))
            except Exception:
                pass
        return bool(_terminate_runtime_process(pid))

    def _safe_int(v: Any, default: int = 0) -> int:
        try:
            return int(v)
        except Exception:
            return default

    def _coerce_mapping_row(row: Any) -> dict[str, Any]:
        if isinstance(row, dict):
            return dict(row)
        keys = getattr(row, 'keys', None)
        if callable(keys):
            try:
                return {str(key): row[key] for key in list(keys())}
            except Exception:
                return {}
        return {}

    def _latest_log_rows(limit: int = 500):
        rows, _ = fetch_logs(page=1, per_page=limit)
        return [_coerce_mapping_row(row) for row in list(rows or [])]

    def _latest_run_payload() -> dict[str, Any]:
        latest = Path(__file__).resolve().parents[1] / 'reports' / 'auto-campaign-latest.json'
        data, meta = safe_load_json_object(
            latest,
            {},
            description='auto_campaign_latest',
        )
        status = str(meta.get('status') or '').strip().lower()
        if status in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(data, dict):
            return {}
        return data

    def _latest_run_vectors(limit: int = 200) -> list[dict[str, Any]]:
        data = _latest_run_payload()
        vectors = data.get('vectors') if isinstance(data.get('vectors'), list) else []
        if not vectors and isinstance(data.get('runs'), list):
            vectors = data.get('runs') or []
        return [row for row in vectors[:limit] if isinstance(row, dict)]

    def _latest_quality_telemetry() -> dict[str, int]:
        data = _latest_run_payload()
        raw = data.get('quality_telemetry') if isinstance(data.get('quality_telemetry'), dict) else {}
        out = {
            'downgraded_confirm': 0,
            'confirm_queued': 0,
            'confirmed': 0,
            'probable': 0,
        }
        for key in list(out.keys()):
            try:
                out[key] = int(raw.get(key, out[key]))
            except Exception:
                pass
        return out

    def _safe_json_file(path: Path) -> dict[str, Any]:
        data, meta = safe_load_json_object(
            path,
            {},
            description='api_supplemental_json_file',
        )
        status = str(meta.get('status') or '').strip().lower()
        if status in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(data, dict):
            return {}
        return data

    def _latest_archive_dir() -> Path | None:
        reports_root = Path(__file__).resolve().parents[1] / 'reports'
        latest_link = reports_root / 'latest'
        try:
            if latest_link.exists():
                resolved = latest_link.resolve()
                if resolved.exists() and resolved.is_dir():
                    return resolved
        except Exception:
            pass
        payload = _latest_run_payload()
        run_id = str(payload.get('run_id') or '').strip()
        if run_id:
            candidate = reports_root / 'archive' / 'auto' / run_id
            if candidate.exists() and candidate.is_dir():
                return candidate
        return None

    def _latest_archive_summary() -> dict[str, Any]:
        archive_dir = _latest_archive_dir()
        if archive_dir is None:
            return {}
        return _safe_json_file(archive_dir / 'summary.json')

    def _latest_evaluation_metrics() -> dict[str, Any]:
        archive_dir = _latest_archive_dir()
        if archive_dir is not None:
            metrics = _safe_json_file(archive_dir / 'evaluation-metrics.json')
            if metrics:
                return metrics
        payload = _latest_run_payload()
        evaluation = payload.get('evaluation') if isinstance(payload.get('evaluation'), dict) else {}
        metrics = evaluation.get('metrics') if isinstance(evaluation.get('metrics'), dict) else {}
        return dict(metrics) if isinstance(metrics, dict) else {}

    def _latest_evaluation_replay() -> dict[str, Any]:
        archive_dir = _latest_archive_dir()
        if archive_dir is not None:
            replay = _safe_json_file(archive_dir / 'evaluation-replay.json')
            if replay:
                return replay
        return {}

    def _latest_trace_row() -> dict[str, Any]:
        current = _selected_snapshot_context(load_runtime_state())
        latest = current.get('snap_latest') if isinstance(current.get('snap_latest'), dict) else {}
        if latest:
            return latest
        vectors = _latest_run_vectors(250)
        if vectors:
            return vectors[-1]
        return {}

    def _lifecycle_counts(vectors: list[dict[str, Any]]) -> dict[str, int]:
        out = {'signal': 0, 'probable': 0, 'confirm_running': 0, 'confirmed': 0}
        for row in vectors:
            lifecycle = str(row.get('finding_lifecycle') or '').strip().lower()
            qual = row.get('qualification') if isinstance(row.get('qualification'), dict) else {}
            verdict = str(qual.get('verdict') or 'none').strip().lower()
            if lifecycle in out:
                out[lifecycle] += 1
            elif verdict == 'confirmed':
                out['confirmed'] += 1
            elif verdict == 'probable':
                out['probable'] += 1
            else:
                out['signal'] += 1
        return out

    def _decision_flag_totals(vectors: list[dict[str, Any]], key: str) -> dict[str, int]:
        out = {'retry': 0, 'confirm': 0, 'followup': 0, 'precision': 0}
        for row in vectors:
            flags = row.get(key) if isinstance(row.get(key), dict) else {}
            for action in list(out.keys()):
                if bool(flags.get(action, False)):
                    out[action] += 1
        return out

    def _effective_status_counts(vectors: list[dict[str, Any]]) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in vectors:
            status = str(row.get('decision_effective_status') or ((row.get('runtime_decision') or {}).get('effective_status') if isinstance(row.get('runtime_decision'), dict) else '') or 'unknown').strip().lower()
            out[status] = int(out.get(status, 0)) + 1
        return out

    def _runtime_trace_payload() -> dict[str, Any]:
        payload = _latest_run_payload()
        row = _latest_trace_row()
        payload_source = 'latest_trace_row' if row else 'latest_run_payload_fallback'
        if not row:
            return {
                'ok': False,
                'error': 'no_runtime_trace',
                'source': payload_source,
                'run_id': str(payload.get('run_id') or ''),
                'run_identity': {'target': '-', 'objective': '-', 'task_family': '-', 'plan_name': '-', 'mode': '-', 'classification': '-', 'host_state_band': '-'},
                'ladder': {'current_stage': '-', 'next_stage': '-', 'recommended_progression': [], 'target_surface_rationale': []},
                'prerequisites': {'actor_requirements': {}, 'session_requirements': {}, 'auth_prereq_missing': False, 'state_prereq_missing': False},
                'success_semantics': {'success_model': '-', 'expected_signal_type': '-', 'evidence_goal_type': '-', 'success_gap': '-', 'acceptance_checks_eval': [], 'evidence_required_eval': [], 'required_evidence_hits': []},
                'signal_status': {'workflow_status': '-', 'finding_status': '-', 'success_status': '-', 'adaptation_status': '-', 'expected_signal_observed': '-'},
                'decision': {'requested_action': '-', 'effective_action': '-', 'effective_status': '-', 'effective_summary': '-', 'reasons': [], 'blockers': [], 'priority_score': None, 'capability_lane': '-', 'action_type': '-', 'capability': '-'},
                'governance': {'policy_blocked': False, 'owner_gate_pending': False, 'contamination_excluded': False, 'contamination_status': '-', 'metric_exclusion_reasons': [], 'execution_gate': {}, 'fallback_degraded': False, 'lineage_complete': False},
                'lineage': {'lineage_sha256': '-', 'planner_contract_sha256': '-', 'runtime_contract_sha256': '-', 'experiment_intent_id': '-', 'task_family': '-', 'target': '-', 'current_stage': '-', 'next_stage': '-', 'action_type': '-', 'capability': '-'},
                'trace_sources': {
                    'payload_source': payload_source,
                    'ladder': {},
                    'decision': {},
                    'success_gap': 'missing',
                    'acceptance_checks_eval': 'missing',
                    'evidence_required_eval': 'missing',
                    'required_evidence_hits': 'missing',
                    'expected_signal_observed': 'missing',
                },
                'replay': {},
            }
        runtime_task = row.get('runtime_task') if isinstance(row.get('runtime_task'), dict) else {}
        runtime_decision = row.get('runtime_decision') if isinstance(row.get('runtime_decision'), dict) else {}
        signal_contract = row.get('signal_contract') if isinstance(row.get('signal_contract'), dict) else {}
        success_semantics = row.get('success_semantics') if isinstance(row.get('success_semantics'), dict) else {}
        analysis_contract = row.get('analysis_contract') if isinstance(row.get('analysis_contract'), dict) else {}
        lineage_summary = ensure_semantic_lineage_summary(
            summary=(row.get('semantic_lineage_summary') if isinstance(row.get('semantic_lineage_summary'), dict) else {}),
            lineage=(row.get('semantic_lineage') if isinstance(row.get('semantic_lineage'), dict) else {}),
            task=row,
            runtime_task=runtime_task,
            source='phase7_runtime_trace',
        )
        replay_result = replay_decision_bundle(build_replay_bundle(row, run_id=str(payload.get('run_id') or ''), campaign_key=str((payload.get('campaign_validation') or {}).get('campaign_key') or '')))
        planning_ladder = ((row.get('planning_ladder') if isinstance(row.get('planning_ladder'), dict) else {}) or ((row.get('semantic_lineage') or {}).get('planner_contract') or {}).get('planning_ladder') if isinstance((row.get('semantic_lineage') or {}).get('planner_contract'), dict) else {})
        planner_rationale = row.get('planner_rationale') if isinstance(row.get('planner_rationale'), dict) else {}
        execution_gate = row.get('execution_gate') if isinstance(row.get('execution_gate'), dict) else {}
        contamination = row.get('run_contamination') if isinstance(row.get('run_contamination'), dict) else {}
        ladder, ladder_sources = resolve_trace_ladder(
            lineage_summary=lineage_summary,
            planning_ladder=planning_ladder if isinstance(planning_ladder, dict) else {},
            planner_rationale=planner_rationale,
            runtime_task=runtime_task,
        )
        decision, decision_sources = resolve_trace_decision(
            row=row,
            runtime_decision=runtime_decision,
            replay_result=replay_result,
            runtime_task=runtime_task,
            lineage_summary=lineage_summary,
        )
        success_gap = success_semantics.get('success_gap') or ((signal_contract.get('success_outcome') or {}).get('gap') if isinstance(signal_contract.get('success_outcome'), dict) else '-') or '-'
        acceptance_checks_eval = normalize_trace_list_preview(success_semantics.get('acceptance_checks_eval') or success_semantics.get('acceptance_checks'))
        evidence_required_eval = normalize_trace_list_preview(success_semantics.get('evidence_required_eval') or success_semantics.get('evidence_required'))
        required_evidence_hits = normalize_trace_list_preview(success_semantics.get('required_evidence_hits'))
        return {
            'ok': True,
            'source': payload_source,
            'run_id': str(payload.get('run_id') or ''),
            'run_identity': {
                'target': row.get('target') or '-',
                'objective': row.get('objective') or '-',
                'task_family': row.get('task_family') or lineage_summary.get('task_family') or '-',
                'plan_name': row.get('plan_name') or '-',
                'mode': row.get('mode') or '-',
                'classification': row.get('classification') or '-',
                'host_state_band': row.get('host_state_band') or '-',
            },
            'ladder': ladder,
            'prerequisites': {
                'actor_requirements': dict(runtime_task.get('actor_requirements') or {}),
                'session_requirements': dict(runtime_task.get('session_requirements') or {}),
                'auth_prereq_missing': bool(replay_result.get('auth_prereq_missing', False)),
                'state_prereq_missing': bool(replay_result.get('state_prereq_missing', False)),
            },
            'success_semantics': {
                'success_model': success_semantics.get('success_model') or '-',
                'expected_signal_type': success_semantics.get('expected_signal_type') or '-',
                'evidence_goal_type': success_semantics.get('evidence_goal_type') or '-',
                'success_gap': success_gap,
                'acceptance_checks_eval': acceptance_checks_eval,
                'evidence_required_eval': evidence_required_eval,
                'required_evidence_hits': required_evidence_hits,
            },
            'signal_status': {
                'workflow_status': replay_result.get('workflow_status') or '-',
                'finding_status': replay_result.get('finding_status') or '-',
                'success_status': replay_result.get('success_status') or '-',
                'adaptation_status': replay_result.get('adaptation_status') or '-',
                'expected_signal_observed': analysis_contract.get('expected_signal_observed') or '-',
            },
            'decision': decision,
            'governance': {
                'policy_blocked': bool(replay_result.get('policy_blocked', False)),
                'owner_gate_pending': bool(replay_result.get('owner_gate_pending', False)),
                'contamination_excluded': bool(replay_result.get('contamination_excluded', False)),
                'contamination_status': contamination.get('status') or '-',
                'metric_exclusion_reasons': list(replay_result.get('metric_exclusion_reasons') or []),
                'execution_gate': execution_gate,
                'fallback_degraded': bool(replay_result.get('fallback_degraded', False)),
                'lineage_complete': bool(replay_result.get('lineage_complete', False)),
            },
            'lineage': {
                'lineage_sha256': lineage_summary.get('lineage_sha256') or '-',
                'planner_contract_sha256': lineage_summary.get('planner_contract_sha256') or '-',
                'runtime_contract_sha256': lineage_summary.get('runtime_contract_sha256') or '-',
                'experiment_intent_id': lineage_summary.get('experiment_intent_id') or '-',
                'task_family': lineage_summary.get('task_family') or '-',
                'target': lineage_summary.get('target') or row.get('target') or '-',
                'current_stage': lineage_summary.get('current_stage') or '-',
                'next_stage': lineage_summary.get('next_stage') or '-',
                'action_type': lineage_summary.get('action_type') or '-',
                'capability': lineage_summary.get('capability') or '-',
            },
            'trace_sources': {
                'payload_source': payload_source,
                'ladder': ladder_sources,
                'decision': decision_sources,
                'success_gap': 'success_semantics' if success_semantics.get('success_gap') else ('signal_contract.success_outcome' if isinstance(signal_contract.get('success_outcome'), dict) and (signal_contract.get('success_outcome') or {}).get('gap') else 'missing'),
                'acceptance_checks_eval': 'success_semantics.acceptance_checks_eval' if success_semantics.get('acceptance_checks_eval') else ('success_semantics.acceptance_checks' if success_semantics.get('acceptance_checks') else 'missing'),
                'evidence_required_eval': 'success_semantics.evidence_required_eval' if success_semantics.get('evidence_required_eval') else ('success_semantics.evidence_required' if success_semantics.get('evidence_required') else 'missing'),
                'required_evidence_hits': 'success_semantics.required_evidence_hits' if success_semantics.get('required_evidence_hits') else 'missing',
                'expected_signal_observed': 'analysis_contract' if analysis_contract.get('expected_signal_observed') else 'missing',
            },
            'replay': replay_result,
        }

    def _evaluation_summary_payload() -> dict[str, Any]:
        return build_evaluation_summary_payload(
            payload=_latest_run_payload(),
            archive_summary=_latest_archive_summary(),
            metrics=_latest_evaluation_metrics(),
            replay=_latest_evaluation_replay(),
        )

    def _runtime_snapshot(runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        runtime = runtime if isinstance(runtime, dict) else load_runtime_state()
        snapshot = runtime.get('snapshot') if isinstance(runtime.get('snapshot'), dict) else {}
        return snapshot if isinstance(snapshot, dict) else {}

    def _load_campaign_blueprint(key: str) -> dict[str, Any] | None:
        selected = str(key or '').strip()
        if not selected:
            return None
        latest = PLANNER_REGISTRY_ROOT / selected / 'latest.json'
        meta, latest_meta = safe_load_json_object(
            latest,
            {},
            description='planner_registry_latest',
        )
        if str(latest_meta.get('status') or '').strip().lower() in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(meta, dict):
            return None
        version_rel = str(meta.get('path') or 'versions/v0001').strip() or 'versions/v0001'
        bp_path = PLANNER_REGISTRY_ROOT / selected / version_rel / 'blueprint.json'
        bp, bp_meta = safe_load_json_object(
            bp_path,
            {},
            description='planner_blueprint',
        )
        if str(bp_meta.get('status') or '').strip().lower() in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(bp, dict):
            return None
        return bp

    def _campaign_settings_for_selected_key(selected_key: str | None = None) -> dict[str, Any]:
        key = str(selected_key or selected_campaign_key() or '').strip()
        store = load_campaign_settings()
        global_cfg = store.get('global', {}) if isinstance(store.get('global'), dict) else {}
        by_campaign = store.get('by_campaign', {}) if isinstance(store.get('by_campaign'), dict) else {}
        cfg: dict[str, Any] = dict(global_cfg) if isinstance(global_cfg, dict) else {}
        if key and isinstance(by_campaign.get(key), dict):
            cfg.update(by_campaign.get(key) or {})
        cfg['resolved_campaign_key'] = key
        return cfg

    def _upsert_header(headers: list[dict[str, Any]], *, name: str, value: str, source: str) -> tuple[list[dict[str, Any]], bool]:
        changed = False
        out: list[dict[str, Any]] = []
        found = False
        for item in headers:
            if not isinstance(item, dict):
                continue
            item_name = str(item.get('name') or '').strip()
            if item_name.lower() == name.lower():
                found = True
                item_source = str(item.get('source') or 'operator_supplied').strip() or 'operator_supplied'
                item_value = str(item.get('value') or '')
                if item_source == 'campaign_required' and item_value != value:
                    item = {**item, 'name': name, 'value': value, 'source': source}
                    changed = True
                out.append(item)
            else:
                out.append(item)
        if not found and value:
            out.append({'name': name, 'value': value, 'source': source})
            changed = True
        return out, changed

    def _ensure_campaign_credential_defaults(selected_key: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        key = str(selected_key or selected_campaign_key() or '').strip()
        store = load_campaign_settings()
        global_cfg = store.get('global', {}) if isinstance(store.get('global'), dict) else {}
        by_campaign = store.get('by_campaign', {}) if isinstance(store.get('by_campaign'), dict) else {}
        cfg = dict(by_campaign.get(key) or {}) if key and isinstance(by_campaign.get(key), dict) else {}
        bp = _load_campaign_blueprint(key)
        creds_policy = dict((bp or {}).get('credentials_policy') or {}) if isinstance((bp or {}).get('credentials_policy'), dict) else {}
        changed = False

        for field in ('credentials_required', 'allow_auth_header', 'allow_cookie_header', 'allow_basic_auth'):
            if field not in cfg and field in creds_policy:
                cfg[field] = bool(creds_policy.get(field))
                changed = True
        if 'credentials_owner_approved' not in cfg and 'credentials_owner_approved' in global_cfg:
            cfg['credentials_owner_approved'] = bool(global_cfg.get('credentials_owner_approved'))
            changed = True
        if not str(cfg.get('bug_bounty_username') or '').strip() and str(global_cfg.get('bug_bounty_username') or '').strip():
            cfg['bug_bounty_username'] = str(global_cfg.get('bug_bounty_username') or '')
            changed = True
        if not str(cfg.get('test_account_email') or '').strip() and str(global_cfg.get('test_account_email') or '').strip():
            cfg['test_account_email'] = str(global_cfg.get('test_account_email') or '')
            changed = True

        rd = dict(cfg.get('request_decoration') or {}) if isinstance(cfg.get('request_decoration'), dict) else {}
        headers = [dict(item) for item in (rd.get('headers') or []) if isinstance(item, dict)]
        cookies = [dict(item) for item in (rd.get('cookies') or []) if isinstance(item, dict)]
        notes = [str(x).strip() for x in (rd.get('provenance_notes') or []) if str(x).strip()]
        policy_notes = [str(x).strip() for x in (creds_policy.get('notes') or []) if str(x).strip()]
        for note in policy_notes:
            if note not in notes:
                notes.append(note)
                changed = True

        user = str(cfg.get('bug_bounty_username') or '').strip()
        requires_h1 = any('x-hackerone-research' in note.lower() for note in policy_notes)
        if requires_h1:
            new_headers, header_changed = _upsert_header(headers, name='X-HackerOne-Research', value=user, source='campaign_required')
            headers = new_headers
            changed = changed or header_changed

        basic_auth = dict(rd.get('basic_auth') or {}) if isinstance(rd.get('basic_auth'), dict) else {'enabled': False, 'username': '', 'password': '', 'password_ref': ''}
        mode = str(rd.get('mode') or '').strip().lower()
        if mode not in {'none', 'campaign_required', 'operator_supplied', 'mixed'}:
            mode = 'none'
        if mode == 'none' and (headers or cookies or basic_auth.get('enabled') or policy_notes):
            mode = 'campaign_required'
            changed = True
        cfg['request_decoration'] = {
            'mode': mode,
            'headers': headers,
            'cookies': cookies,
            'basic_auth': {
                'enabled': bool(basic_auth.get('enabled', False)),
                'username': str(basic_auth.get('username') or ''),
                'password': str(basic_auth.get('password') or ''),
                'password_ref': str(basic_auth.get('password_ref') or ''),
            },
            'provenance_notes': notes,
        }

        if key:
            by_campaign[key] = cfg
            store['by_campaign'] = by_campaign
            if changed:
                save_campaign_settings(store)

        merged = _campaign_settings_for_selected_key(key)
        return merged, creds_policy

    def _credential_status(cfg: dict[str, Any], creds_policy: dict[str, Any]) -> tuple[str, str]:
        required = bool(cfg.get('credentials_required', False) or creds_policy.get('credentials_required', False))
        if not required:
            return 'ANONYMOUS', 'No program-specific credentials required.'
        if not bool(cfg.get('credentials_owner_approved', False)):
            return 'OWNER APPROVAL REQUIRED', 'Credentials policy is enabled but owner approval is not recorded.'
        rd = dict(cfg.get('request_decoration') or {}) if isinstance(cfg.get('request_decoration'), dict) else {}
        headers = [dict(item) for item in (rd.get('headers') or []) if isinstance(item, dict)]
        notes = [str(x).strip() for x in (rd.get('provenance_notes') or []) if str(x).strip()]
        user = str(cfg.get('bug_bounty_username') or '').strip()
        test_mail = str(cfg.get('test_account_email') or '').strip()
        missing: list[str] = []
        if any('x-hackerone-research' in note.lower() for note in notes):
            if not user:
                missing.append('bug bounty username')
            has_h1 = any(str(item.get('name') or '').strip().lower() == 'x-hackerone-research' and str(item.get('value') or '').strip() for item in headers)
            if not has_h1:
                missing.append('X-HackerOne-Research header')
        if any('test account' in note.lower() or 'hacker email alias' in note.lower() for note in notes) and not test_mail:
            missing.append('test account email')
        if missing:
            return 'INCOMPLETE', 'Missing: ' + ', '.join(missing)
        return 'READY', 'Program-specific credential decoration is configured for this campaign.'

    def _runtime_alive_pid() -> tuple[bool, int | None]:
        refresh_runtime_state()
        pid_raw = str(STATE.get('pid') or '').strip()
        state_raw = str(STATE.get('state') or '').strip().lower()
        if pid_raw.isdigit() and state_raw in {'running', 'paused'}:
            return True, int(pid_raw)
        if RUNTIME_PID_PATH.exists():
            try:
                pid = int(str(RUNTIME_PID_PATH.read_text(encoding='utf-8')).strip())
                if pid > 0:
                    os.kill(pid, 0)
                    return True, pid
            except Exception:
                pass
        return False, None

    def _spawn_runtime_process(campaign_key: str) -> int:
        RUNTIME_STDOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env['AUTO_CAMPAIGN_KEY'] = str(campaign_key or '').strip()
        env['RAVENCLAW_WORKSPACE'] = str(WORKSPACE_DIR)
        env['PYTHONUNBUFFERED'] = '1'
        stdout_handle = open(RUNTIME_STDOUT_PATH, 'ab')
        stderr_handle = open(RUNTIME_STDERR_PATH, 'ab')
        try:
            proc = subprocess.Popen(
                [PYTHON_BIN, str(ENGINE_DIR / 'auto_campaign.py')],
                cwd=str(WORKSPACE_DIR),
                env=env,
                stdout=stdout_handle,
                stderr=stderr_handle,
                start_new_session=True,
            )
        finally:
            stdout_handle.close()
            stderr_handle.close()
        RUNTIME_PID_PATH.write_text(str(proc.pid), encoding='utf-8')
        return int(proc.pid)

    def _terminate_runtime_process(pid: int) -> bool:
        if not int(pid or 0):
            return False
        terminated = False
        try:
            os.killpg(int(pid), signal.SIGTERM)
            terminated = True
        except Exception:
            try:
                os.kill(int(pid), signal.SIGTERM)
                terminated = True
            except Exception:
                terminated = False
        if terminated:
            deadline = time.time() + 2.0
            while time.time() < deadline:
                try:
                    os.kill(int(pid), 0)
                except Exception:
                    break
                time.sleep(0.1)
            else:
                try:
                    os.killpg(int(pid), signal.SIGKILL)
                except Exception:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except Exception:
                        pass
        try:
            if RUNTIME_PID_PATH.exists():
                RUNTIME_PID_PATH.unlink()
        except Exception:
            pass
        return terminated

    def _selected_campaign_runtime_view(runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        runtime = runtime if isinstance(runtime, dict) else load_runtime_state()
        selected_view = selected_runtime_snapshot_view(runtime, selected_campaign_key())
        return build_selected_campaign_projection(runtime, selected_view, STATE)

    def _selected_snapshot_context(runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        runtime = runtime if isinstance(runtime, dict) else load_runtime_state()
        selected_view = selected_runtime_snapshot_view(runtime, selected_campaign_key())
        return build_selected_campaign_projection(runtime, selected_view, STATE)

    def _clear_snapshot_for_campaign(campaign_key: str) -> None:
        key = str(campaign_key or '').strip()
        if not key or not RUNTIME_SNAPSHOT_PATH.exists():
            return
        data, meta = safe_load_json_object(
            RUNTIME_SNAPSHOT_PATH,
            {},
            description='runtime_snapshot',
        )
        if str(meta.get('status') or '').strip().lower() in {'missing', 'invalid_json', 'invalid_shape'} or not isinstance(data, dict):
            return
        campaign = data.get('campaign') if isinstance(data.get('campaign'), dict) else {}
        if str(campaign.get('campaign_key') or '').strip() != key:
            return
        data['campaign'] = {}
        data['plan'] = {}
        data['latest_run'] = {}
        try:
            RUNTIME_SNAPSHOT_PATH.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
        except Exception:
            pass

    def _snapshot_section(snapshot: dict[str, Any], key: str) -> dict[str, Any]:
        section = snapshot.get(key) if isinstance(snapshot.get(key), dict) else {}
        return section if isinstance(section, dict) else {}

    def _snapshot_quality_telemetry(snapshot: dict[str, Any]) -> dict[str, int]:
        telemetry = _snapshot_section(snapshot, 'telemetry')
        raw = telemetry.get('quality_telemetry') if isinstance(telemetry.get('quality_telemetry'), dict) else {}
        out = {'downgraded_confirm': 0, 'confirm_queued': 0, 'confirmed': 0, 'probable': 0}
        for key in list(out.keys()):
            try:
                out[key] = int(raw.get(key, out[key]))
            except Exception:
                pass
        return out

    def _tool_registry_summary_payload() -> dict[str, Any]:
        state = get_tool_registry_ui_state()
        active_profile = str(state.get('active_profile') or 'core')
        tool_catalog = get_tool_catalog()
        runtime_policy = get_runtime_tool_policy(active_profile)
        planner_visible = sorted([str(x) for x in runtime_policy.get('planner_allowed_tools') or []])
        execution_allowed = sorted([str(x) for x in runtime_policy.get('execution_allowed_tools') or []])
        missing_installed = sorted([name for name in planner_visible if not bool((tool_catalog.get(name) or {}).get('installed', False))])
        return {
            **state,
            'planner_visible_tools': planner_visible,
            'planner_visible_count': len(planner_visible),
            'execution_allowed_tools': execution_allowed,
            'execution_allowed_count': len(execution_allowed),
            'runtime_tool_policy_profiles': list(runtime_policy.get('profiles') or []),
            'missing_installed': missing_installed,
        }

    @app.route("/api/logs")
    def api_logs():
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(100, int(request.args.get("per_page", 20))))
        rows, total = fetch_logs(page=page, per_page=per_page)
        items = []
        for row in rows:
            row_obj = dict(row)
            try:
                ts = datetime.fromisoformat(str(row_obj.get("timestamp") or ""))
                date = ts.strftime("%Y-%m-%d")
                time = ts.strftime("%H:%M:%S")
            except Exception:
                date = "-"
                time = "-"
            status = str(row_obj.get("status") or "")
            items.append(
                {
                    "id": row_obj.get("id"),
                    "date": date,
                    "time": time,
                    "agent": row_obj.get("agent"),
                    "decision": row_obj.get("decision"),
                    "status": status,
                    "raw_status": status,
                    "status_class": STATUS_CLASSES.get(status.lower(), "status-neutral"),
                    "result": row_obj.get("result"),
                    "tor": row_obj.get("tor"),
                }
            )
        return jsonify({"page": page, "per_page": per_page, "total": total, "total_pages": max(1, (total + per_page - 1) // per_page), "items": items})

    @app.route("/api/logs/clear", methods=["POST"])
    def api_logs_clear():
        conn = get_conn()
        with conn:
            conn.execute("DELETE FROM logs")
        conn.close()
        return jsonify({"ok": True})

    @app.route("/api/campaign-info")
    def api_campaign_info():
        refresh_runtime_state()
        current = _selected_campaign_runtime_view(load_runtime_state())
        settings, creds_policy = _ensure_campaign_credential_defaults(current.get('selected_campaign_key'))
        use_latest_run = bool(current.get('snapshot_matches_selected'))
        latest_payload = _latest_run_payload() if use_latest_run else {}
        latest_vectors = _latest_run_vectors(250) if use_latest_run else []
        STATE["campaign_name"] = STATE.get("selected_campaign_name") or "-"
        cred_status, cred_status_detail = _credential_status(settings if isinstance(settings, dict) else {}, creds_policy if isinstance(creds_policy, dict) else {})
        return jsonify(build_campaign_info_payload(
            state=STATE,
            current=current,
            settings=(settings if isinstance(settings, dict) else {}),
            cred_status=cred_status,
            cred_status_detail=cred_status_detail,
            latest_payload=(latest_payload if isinstance(latest_payload, dict) else {}),
            latest_vectors=latest_vectors,
        ))

    @app.route("/api/campaign/control", methods=["POST"])
    def api_campaign_control():
        data = request.get_json(silent=True) or {}
        action = str(data.get("action", "")).strip().lower()
        owner_override = bool(data.get("owner_override", STATE.get("owner_override", False)))
        if action == 'resume':
            action = 'start'
        if action not in {'start', 'pause', 'stop'}:
            return jsonify({'ok': False, 'error': 'invalid_action'}), 400
        STATE['owner_override'] = owner_override
        selected_key = str(selected_campaign_key() or '').strip()
        alive, pid = _runtime_alive_pid_fn()
        if action == 'start':
            if not selected_key:
                return jsonify({'ok': False, 'error': 'missing_campaign_key'}), 400
            runtime = load_runtime_state()
            plan = runtime.get('runtime_plan') if isinstance(runtime.get('runtime_plan'), dict) else {}
            generated = int(plan.get('generated') or plan.get('prepared_attacks') or 0)
            plan_campaign_key = str(plan.get('campaign_key') or '').strip()
            if generated <= 0 or (plan_campaign_key and plan_campaign_key != selected_key):
                return jsonify({'ok': False, 'error': 'runtime_plan_missing_for_selected_campaign'}), 400
            STATE['state'] = 'running'
            write_runtime_state_file(STATE, paused=False)
            if alive:
                refresh_runtime_state()
                return jsonify({'ok': True, 'state': STATE.get('state'), 'owner_override': STATE.get('owner_override'), 'selected_campaign_key': selected_key, 'pid': pid, 'started': False, 'resumed': True})
            pid = _spawn_runtime_process_fn(selected_key)
            time.sleep(0.15)
            refresh_runtime_state()
            return jsonify({'ok': True, 'state': STATE.get('state'), 'owner_override': STATE.get('owner_override'), 'selected_campaign_key': selected_key, 'pid': pid, 'started': True, 'resumed': False})
        if action == 'pause':
            if not alive:
                return jsonify({'ok': False, 'error': 'runtime_not_running'}), 400
            STATE['state'] = 'paused'
            write_runtime_state_file(STATE, paused=True)
            refresh_runtime_state()
            return jsonify({'ok': True, 'state': STATE.get('state'), 'owner_override': STATE.get('owner_override'), 'pid': pid, 'paused': True})
        STATE['state'] = 'stopped'
        write_runtime_state_file(STATE, paused=False)
        terminated = _terminate_runtime_process_fn(int(pid or 0)) if alive and pid else False
        refresh_runtime_state()
        return jsonify({'ok': True, 'state': STATE.get('state'), 'owner_override': STATE.get('owner_override'), 'pid': pid, 'stopped': True, 'terminated': terminated})

    @app.route("/api/campaign/owner-override", methods=["POST"])
    def api_owner_override():
        data = request.get_json(silent=True) or {}
        enabled = bool(data.get("enabled", data.get("owner_override", False)))
        STATE["owner_override"] = enabled
        return jsonify({"ok": True, "owner_override": enabled})

    @app.route("/api/campaign/delete-current", methods=["POST"])
    def api_campaign_delete_current():
        key = str(selected_campaign_key() or '').strip()
        deleted_registry = False
        deleted_runtime_plan = False
        deleted_runtime_meta = False
        if key:
            campaign_dir = PLANNER_REGISTRY_ROOT / key
            if campaign_dir.exists():
                shutil.rmtree(campaign_dir, ignore_errors=True)
                deleted_registry = True
            store = load_campaign_settings()
            by_campaign = store.get('by_campaign') if isinstance(store.get('by_campaign'), dict) else {}
            if isinstance(by_campaign, dict) and key in by_campaign:
                del by_campaign[key]
                store['by_campaign'] = by_campaign
                save_campaign_settings(store)
            runtime = load_runtime_state()
            plan = runtime.get('runtime_plan') if isinstance(runtime.get('runtime_plan'), dict) else {}
            plan_campaign_key = str(plan.get('campaign_key') or '').strip()
            if not plan_campaign_key and RUNTIME_PLAN_META_PATH.exists():
                meta, meta_status = safe_load_json_object(
                    RUNTIME_PLAN_META_PATH,
                    {},
                    description='runtime_plan_meta',
                )
                if str(meta_status.get('status') or '').strip().lower() not in {'missing', 'invalid_json', 'invalid_shape'} and isinstance(meta, dict):
                    plan_campaign_key = str(meta.get('campaign_key') or '').strip()
                else:
                    plan_campaign_key = ''
            if plan_campaign_key == key:
                for path in RUNTIME_PLAN_DELETE_PATHS:
                    try:
                        if path.exists():
                            path.unlink()
                            deleted_runtime_plan = True
                    except Exception:
                        pass
                try:
                    if RUNTIME_PLAN_META_PATH.exists():
                        RUNTIME_PLAN_META_PATH.unlink()
                        deleted_runtime_meta = True
                except Exception:
                    pass
            _clear_snapshot_for_campaign(key)
        STATE["selected_campaign_key"] = ""
        STATE["selected_campaign_name"] = "-"
        STATE["state"] = "idle"
        STATE["pid"] = "-"
        STATE["planner_scope_targets"] = 0
        STATE["prepared_attacks"] = 0
        STATE["runtime_plan_ok"] = False
        STATE["runtime_plan_error_preview"] = "runtime_plan_missing"
        ui = load_planner_ui_state()
        if isinstance(ui, dict):
            ui["selected_campaign_key"] = ""
            save_planner_ui_state(ui)
        save_orchestrator_state({"selected_campaign_key": "", "updated_at": datetime.now(timezone.utc).isoformat(timespec='seconds')})
        return jsonify({"ok": True, "deleted_campaign_key": key, "deleted_registry": deleted_registry, "deleted_runtime_plan": deleted_runtime_plan, "deleted_runtime_meta": deleted_runtime_meta})

    @app.route("/api/campaign/settings", methods=["GET", "POST"])
    def api_campaign_settings():
        store = load_campaign_settings()
        selected_key = str(request.args.get('selected_campaign_key') or selected_campaign_key() or '').strip()
        if request.method == "GET":
            _seeded_cfg, creds_policy = _ensure_campaign_credential_defaults(selected_key)
            cfg = _campaign_settings_for_selected_key(selected_key)
            cred_status, cred_status_detail = _credential_status(cfg if isinstance(cfg, dict) else {}, creds_policy if isinstance(creds_policy, dict) else {})
            return jsonify({**cfg, 'credentials_status': cred_status, 'credentials_status_detail': cred_status_detail})
        data = request.get_json(silent=True) or {}
        selected_key = str(data.get('selected_campaign_key') or selected_key or '').strip()
        payload = {k: v for k, v in data.items() if k != 'selected_campaign_key'}
        if selected_key:
            _cfg, _policy = _ensure_campaign_credential_defaults(selected_key)
            store = load_campaign_settings()
            by_campaign = store.get('by_campaign', {}) if isinstance(store.get('by_campaign'), dict) else {}
            campaign_cfg = by_campaign.get(selected_key, {}) if isinstance(by_campaign.get(selected_key), dict) else {}
            campaign_cfg = {**campaign_cfg, **payload}
            by_campaign[selected_key] = campaign_cfg
            store['by_campaign'] = by_campaign
        else:
            global_cfg = store.get("global", {}) if isinstance(store.get("global"), dict) else {}
            global_cfg.update(payload)
            store["global"] = global_cfg
        save_campaign_settings(store)
        merged_preview = _campaign_settings_for_selected_key(selected_key) if selected_key else (store.get('global', {}) if isinstance(store.get('global'), dict) else {})
        for key in (
            "credentials_required", "allow_auth_header", "allow_cookie_header", "allow_basic_auth",
            "credentials_owner_approved", "bug_bounty_username", "test_account_email", "request_decoration",
            "max_runs", "target_load_limit", "time_budget_min", "retry_policy",
            "aggression_override", "aggression_effective", "owner_override",
        ):
            if key in merged_preview:
                STATE[key] = merged_preview.get(key)
        if "owner_override" in data:
            STATE["owner_override"] = bool(data.get("owner_override"))
        _seeded_cfg, creds_policy = _ensure_campaign_credential_defaults(selected_key)
        cfg = _campaign_settings_for_selected_key(selected_key)
        cred_status, cred_status_detail = _credential_status(cfg if isinstance(cfg, dict) else {}, creds_policy if isinstance(creds_policy, dict) else {})
        return jsonify({"ok": True, **cfg, 'credentials_status': cred_status, 'credentials_status_detail': cred_status_detail})

    @app.route("/api/tool-registry/state", methods=["GET", "POST"])
    def api_tool_registry_state():
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            selected = str(data.get('active_profile') or data.get('selected_profile') or '').strip().lower()
            if not selected:
                return jsonify({'ok': False, 'error': 'missing_active_profile'}), 400
            try:
                save_tool_registry_state(selected)
            except Exception as exc:
                return jsonify({'ok': False, 'error': str(exc)}), 400
        return jsonify(_tool_registry_summary_payload())

    @app.route("/api/tool-registry/summary")
    def api_tool_registry_summary():
        return jsonify(_tool_registry_summary_payload())

    @app.route("/api/metrics")
    def api_metrics():
        current = _selected_snapshot_context(load_runtime_state())
        snapshot = current.get('snapshot') if isinstance(current.get('snapshot'), dict) else {}
        snap_telemetry = current.get('snap_telemetry') if isinstance(current.get('snap_telemetry'), dict) else {}
        snap_queues = current.get('snap_queues') if isinstance(current.get('snap_queues'), dict) else {}
        snap_latest = current.get('snap_latest') if isinstance(current.get('snap_latest'), dict) else {}
        snap_quality = _snapshot_quality_telemetry(snapshot)
        rows = _latest_log_rows(500)
        vectors = _latest_run_vectors(250)
        lifecycle = _lifecycle_counts(vectors)
        recent_cls: list[str] = []
        category_distribution: dict[str, int] = {}
        conf_sum = 0.0
        conf_n = 0
        critical = 0
        highest_cvss = 0.0

        if vectors:
            for row in vectors:
                status = str(row.get("engine_status") or "").lower()
                classification = str(row.get('classification') or '').lower()
                qual = row.get('qualification') if isinstance(row.get('qualification'), dict) else {}
                verdict = str(qual.get('verdict') or 'none').lower()
                try:
                    conf_sum += float(qual.get('confidence') or 0.0)
                    conf_n += 1
                except Exception:
                    pass
                if verdict == 'confirmed':
                    highest_cvss = max(highest_cvss, 8.4)
                    critical += 1
                elif verdict == 'probable':
                    highest_cvss = max(highest_cvss, 6.7)
                    critical += 1 if classification in {'critical', 'high'} else 0
                elif status in {'failed', 'error', 'blocked'}:
                    critical += 1
                if classification:
                    if classification not in recent_cls:
                        recent_cls.append(classification)
                    category_distribution[classification] = int(category_distribution.get(classification, 0)) + 1
        else:
            for r in rows:
                status = str(r.get("status") or "").lower()
                if status in {"failed", "error", "blocked"}:
                    critical += 1
                if status and status not in recent_cls:
                    recent_cls.append(status)
                category_distribution[status or 'unknown'] = int(category_distribution.get(status or 'unknown', 0)) + 1

        total = len(vectors) if vectors else len(rows)
        probable = max(int(lifecycle.get('probable', 0) or 0), int(snap_quality.get('probable', 0) or 0))
        confirmed = max(int(lifecycle.get('confirmed', 0) or 0), int(snap_quality.get('confirmed', 0) or 0))
        total = max(total, probable + confirmed)
        raw_signals = max(total - probable - confirmed, 0)
        avg_conf = (conf_sum / max(1, conf_n)) if conf_n else (0.5 if rows else 0.0)
        econ = aggregate_runtime_economics(vectors)
        return jsonify({
            "total_findings": total,
            "critical_findings": critical,
            "avg_confidence": round(avg_conf, 3),
            "highest_cvss": highest_cvss,
            "new_since_last_run": min(5, total),
            "verified": confirmed,
            "unverified": max(total - confirmed, 0),
            "severity_distribution": {"high": critical, "medium": max(probable - critical, 0), "low": max(raw_signals, 0)},
            "category_distribution": category_distribution,
            "raw_signals": raw_signals,
            "promoted_findings": probable,
            "needs_review": probable,
            "confirmed": confirmed,
            "lifecycle_signal": lifecycle.get('signal', 0),
            "lifecycle_probable": probable,
            "lifecycle_confirm_run": lifecycle.get('confirm_running', 0),
            "lifecycle_confirm_ok": confirmed,
            "recent_classifications": recent_cls[:5],
            "economics": econ,
            "runtime_snapshot_source": projection_source_label(snapshot=snapshot, fallback='legacy'),
            "queue_followups": int(snap_queues.get('followup_count', 0) or 0),
            "queue_precision": int(snap_queues.get('precision_count', 0) or 0),
            "execution_gate_skip_total": int(snap_telemetry.get('execution_gate_skip_total', 0) or 0),
            "dns_skip_total": int(snap_telemetry.get('dns_skip_total', 0) or 0),
            "host_cooldown_skip_total": int(snap_telemetry.get('host_cooldown_skip_total', 0) or 0),
            "action_type_count": dict(snap_telemetry.get('action_type_count') or {}),
            "semantic_loss_total": int(snap_telemetry.get('semantic_loss_total', 0) or 0),
            "semantic_loss_by_class": dict(snap_telemetry.get('semantic_loss_by_class') or {}),
            "semantic_rereview_total": int(snap_telemetry.get('semantic_rereview_total', 0) or 0),
            "latest_action_type": (snap_latest.get('brain_reasoning_summary') or {}).get('action_type') if isinstance(snap_latest.get('brain_reasoning_summary'), dict) else '-',
            "latest_semantic_loss_class": ((snap_latest.get('semantic_loss_policy') or {}).get('loss_class') if isinstance(snap_latest.get('semantic_loss_policy'), dict) else '-'),
            "latest_semantic_loss_response": ((snap_latest.get('semantic_loss_policy') or {}).get('policy_response') if isinstance(snap_latest.get('semantic_loss_policy'), dict) else '-'),
            "latest_approved_under_degradation": ((snap_latest.get('semantic_loss_policy') or {}).get('approved_under_degradation') if isinstance(snap_latest.get('semantic_loss_policy'), dict) else False),
            "latest_semantic_rereview_required": bool(snap_latest.get('semantic_loss_rereview_required', False)),
            "latest_semantic_rereview_completed": bool(snap_latest.get('semantic_loss_rereview_completed', False)),
            "latest_semantic_rereview_decision": snap_latest.get('semantic_loss_rereview_decision') or '-',
        })

    @app.route("/api/runtime-state")
    def api_runtime_state():
        current = _selected_campaign_runtime_view(load_runtime_state())
        runtime = dict(current.get('runtime') or {}) if isinstance(current.get('runtime'), dict) else {}
        runtime['snapshot'] = current.get('filtered_snapshot') if isinstance(current.get('filtered_snapshot'), dict) else {}
        return jsonify(runtime)

    @app.route("/api/queue-state")
    def api_queue_state():
        current = _selected_campaign_runtime_view(load_runtime_state())
        if current.get('snapshot_matches_selected'):
            return jsonify(load_queue_state())
        return jsonify({
            'followup_queue': [],
            'precision_queue': [],
            'followup_preview': [],
            'precision_preview': [],
            'followup_count': 0,
            'precision_count': 0,
            'source': 'empty_selected_campaign_queue',
        })

    @app.route("/api/runtime-health")
    def api_runtime_health():
        current = _selected_snapshot_context(load_runtime_state())
        runtime = current.get('runtime') if isinstance(current.get('runtime'), dict) else {}
        snapshot = current.get('snapshot') if isinstance(current.get('snapshot'), dict) else {}
        snap_campaign = current.get('snap_campaign') if isinstance(current.get('snap_campaign'), dict) else {}
        snap_plan = current.get('snap_plan') if isinstance(current.get('snap_plan'), dict) else {}
        snap_queues = current.get('snap_queues') if isinstance(current.get('snap_queues'), dict) else {}
        snap_telemetry = current.get('snap_telemetry') if isinstance(current.get('snap_telemetry'), dict) else {}
        snap_latest = current.get('snap_latest') if isinstance(current.get('snap_latest'), dict) else {}
        stdout_b = RUNTIME_STDOUT_PATH.stat().st_size if RUNTIME_STDOUT_PATH.exists() else 0
        stderr_b = RUNTIME_STDERR_PATH.stat().st_size if RUNTIME_STDERR_PATH.exists() else 0
        return jsonify(build_runtime_health_payload(
            runtime=runtime,
            snapshot=snapshot,
            snap_campaign=snap_campaign,
            snap_plan=snap_plan,
            snap_queues=snap_queues,
            snap_telemetry=snap_telemetry,
            snap_latest=snap_latest,
            stdout_bytes=stdout_b,
            stderr_bytes=stderr_b,
        ))

    @app.route("/api/runtime-trace")
    def api_runtime_trace():
        return jsonify(_runtime_trace_payload())

    @app.route("/api/evaluation-summary")
    def api_evaluation_summary():
        return jsonify(_evaluation_summary_payload())

    @app.route("/api/host-state")
    def api_host_state():
        current = _selected_snapshot_context(load_runtime_state())
        snap_hosts = current.get('snap_hosts') if isinstance(current.get('snap_hosts'), dict) else {}
        snap_items = snap_hosts.get('items') if isinstance(snap_hosts.get('items'), list) else []
        if snap_items:
            enriched = []
            for item in snap_items:
                if not isinstance(item, dict):
                    continue
                meta = dict(item)
                promise = float(meta.get('promise_score', 0) or 0)
                noise = float(meta.get('noise_score', 0) or 0)
                evidence = float(meta.get('evidence_density', 0) or 0)
                novelty = float(meta.get('novelty_score', 0) or 0)
                explain_bits = []
                if evidence >= 0.5:
                    explain_bits.append(f'evidence={round(evidence, 2)}')
                if novelty >= 0.4:
                    explain_bits.append(f'novelty={round(novelty, 2)}')
                if promise > noise:
                    explain_bits.append('promise>noise')
                elif noise > promise:
                    explain_bits.append('noise>promise')
                meta['explain'] = '; '.join(explain_bits[:3]) or 'steady sample'
                enriched.append(meta)
            return jsonify({"ok": True, "items": enriched, "source": "snapshot", "updated_at": snap_hosts.get('updated_at')})
        data = load_host_state()
        source_label = str(data.get('_source') or 'normalized_host_state_file') if isinstance(data, dict) else 'normalized_host_state_file'
        hosts = data.get("hosts", {}) if isinstance(data.get("hosts"), dict) else {}
        items = []
        for host, meta in list(hosts.items())[:50]:
            if not isinstance(meta, dict):
                meta = {}
            promise = float(meta.get("promise_score", 0) or 0)
            noise = float(meta.get("noise_score", 0) or 0)
            evidence = float(meta.get("evidence_density", 0) or 0)
            novelty = float(meta.get("novelty_score", 0) or 0)
            explain_bits = []
            if evidence >= 0.5:
                explain_bits.append(f'evidence={round(evidence, 2)}')
            if novelty >= 0.4:
                explain_bits.append(f'novelty={round(novelty, 2)}')
            if promise > noise:
                explain_bits.append('promise>noise')
            elif noise > promise:
                explain_bits.append('noise>promise')
            items.append({
                "host": host,
                "state": meta.get("state", "active"),
                "state_band": meta.get("state_band", meta.get("state", "active")),
                "promise_score": meta.get("promise_score", 0),
                "noise_score": meta.get("noise_score", 0),
                "evidence_density": meta.get("evidence_density", 0),
                "novelty_score": meta.get("novelty_score", 0),
                "preferred_families": meta.get("preferred_families", []),
                "suppressed_families": meta.get("suppressed_families", []),
                "last_success_family": meta.get("last_success_family", "-"),
                "last_transition_reason": meta.get("last_transition_reason", ""),
                "last_transition_at_runs": meta.get("last_transition_at_runs", 0),
                "explain": '; '.join(explain_bits[:3]) or 'steady sample',
            })
        return jsonify({"ok": True, "items": items, "source": source_label})

    @app.route("/api/host-explain")
    def api_host_explain():
        host = str(request.args.get("host") or "").strip().lower()
        current = _selected_snapshot_context(load_runtime_state())
        snap_hosts = current.get('snap_hosts') if isinstance(current.get('snap_hosts'), dict) else {}
        snap_by_host = snap_hosts.get('by_host') if isinstance(snap_hosts.get('by_host'), dict) else {}
        meta = snap_by_host.get(host, {}) if host and isinstance(snap_by_host, dict) else {}
        source = 'snapshot' if meta else 'normalized_host_state_file'
        if not meta:
            data = load_host_state()
            hosts = data.get("hosts", {}) if isinstance(data.get("hosts"), dict) else {}
            meta = hosts.get(host, {}) if host else {}
        meta = meta if isinstance(meta, dict) else {}
        explanations: list[str] = []
        if not host or not meta:
            explanations.append('No host state found for this host yet.')
        else:
            state_band = str(meta.get('state_band') or meta.get('state') or 'active')
            explanations.append(f"State band: {state_band}")
            explanations.append(
                f"Scores — promise={meta.get('promise_score', 0)}, noise={meta.get('noise_score', 0)}, evidence={meta.get('evidence_density', 0)}, novelty={meta.get('novelty_score', 0)}"
            )
            last_transition_reason = str(meta.get('last_transition_reason') or '').strip()
            if last_transition_reason:
                explanations.append(f"Last transition: {last_transition_reason}")
            preferred = [str(x) for x in (meta.get('preferred_families') or []) if str(x).strip()]
            suppressed = [str(x) for x in (meta.get('suppressed_families') or []) if str(x).strip()]
            if preferred:
                explanations.append(f"Preferred families: {', '.join(preferred[:4])}")
            if suppressed:
                explanations.append(f"Suppressed families: {', '.join(suppressed[:4])}")
            last_success_family = str(meta.get('last_success_family') or '').strip()
            if last_success_family:
                explanations.append(f"Last successful family: {last_success_family}")
        host_state_payload = load_host_state()
        host_state_source = str(host_state_payload.get('_source') or ('snapshot' if source == 'snapshot' else 'normalized_host_state_file')) if isinstance(host_state_payload, dict) else source
        return jsonify({"ok": True, "host": host, "meta": meta, "explanations": explanations, "path": str(HOST_STATE_PATH), "source": host_state_source})

    @app.route("/api/host-yield")
    def api_host_yield():
        current = _selected_snapshot_context(load_runtime_state())
        snap_econ = current.get('snap_economics') if isinstance(current.get('snap_economics'), dict) else {}
        econ = snap_econ if snap_econ else aggregate_runtime_economics(_latest_run_vectors(250))
        items = []
        for row in econ.get('host_efficiency', []) if isinstance(econ, dict) else []:
            items.append({
                'host': row.get('key'),
                'runs': row.get('runs', 0),
                'promising': row.get('promising', 0),
                'probable': row.get('probable', 0),
                'confirmed': row.get('confirmed', 0),
                'yield_score': row.get('avg_priority', 0),
                'avg_value': row.get('avg_value', 0),
                'avg_cost': row.get('avg_cost', 0),
                'avg_utility': row.get('avg_utility', 0),
                'partial_or_better_rate': row.get('partial_or_better_rate', 0),
                'explain': row.get('explain', ''),
            })
        return jsonify({"ok": True, "items": items, 'economics': econ, 'source': projection_source_label(snapshot=snap_econ, fallback='legacy_runtime_vectors')})

    @app.route("/api/family-yield")
    def api_family_yield():
        current = _selected_snapshot_context(load_runtime_state())
        snap_econ = current.get('snap_economics') if isinstance(current.get('snap_economics'), dict) else {}
        econ = snap_econ if snap_econ else aggregate_runtime_economics(_latest_run_vectors(250))
        items = []
        for row in econ.get('family_efficiency', []) if isinstance(econ, dict) else []:
            items.append({
                'family': row.get('key'),
                'runs': row.get('runs', 0),
                'promising': row.get('promising', 0),
                'probable': row.get('probable', 0),
                'confirmed': row.get('confirmed', 0),
                'yield_score': row.get('avg_priority', 0),
                'avg_value': row.get('avg_value', 0),
                'avg_cost': row.get('avg_cost', 0),
                'avg_utility': row.get('avg_utility', 0),
                'explain': row.get('explain', ''),
            })
        return jsonify({"ok": True, "items": items, 'economics': econ, 'source': projection_source_label(snapshot=snap_econ, fallback='legacy_runtime_vectors')})

    @app.route("/api/capability-yield")
    def api_capability_yield():
        current = _selected_snapshot_context(load_runtime_state())
        snap_econ = current.get('snap_economics') if isinstance(current.get('snap_economics'), dict) else {}
        econ = snap_econ if snap_econ else aggregate_runtime_economics(_latest_run_vectors(250))
        items = []
        for row in econ.get('capability_efficiency', []) if isinstance(econ, dict) else []:
            items.append({
                'capability': row.get('key'),
                'runs': row.get('runs', 0),
                'promising': row.get('promising', 0),
                'probable': row.get('probable', 0),
                'confirmed': row.get('confirmed', 0),
                'yield_score': row.get('avg_priority', 0),
                'avg_value': row.get('avg_value', 0),
                'avg_cost': row.get('avg_cost', 0),
                'avg_utility': row.get('avg_utility', 0),
                'explain': row.get('explain', ''),
            })
        return jsonify({"ok": True, "items": items, 'economics': econ, 'source': projection_source_label(snapshot=snap_econ, fallback='legacy_runtime_vectors')})

    @app.route("/api/finding-quality")
    def api_finding_quality():
        current = _selected_snapshot_context(load_runtime_state())
        snapshot = current.get('snapshot') if isinstance(current.get('snapshot'), dict) else {}
        snap_telemetry = current.get('snap_telemetry') if isinstance(current.get('snap_telemetry'), dict) else {}
        snap_queues = current.get('snap_queues') if isinstance(current.get('snap_queues'), dict) else {}
        snap_latest = current.get('snap_latest') if isinstance(current.get('snap_latest'), dict) else {}
        vectors = _latest_run_vectors(250)
        econ = aggregate_runtime_economics(vectors)
        lifecycle = _lifecycle_counts(vectors)
        intent_totals = _decision_flag_totals(vectors, 'decision_intent_flags')
        effective_totals = _decision_flag_totals(vectors, 'decision_flags')
        qt = _latest_quality_telemetry()
        snap_qt = _snapshot_quality_telemetry(snapshot)
        for key in list(qt.keys()):
            qt[key] = max(int(qt.get(key, 0) or 0), int(snap_qt.get(key, 0) or 0))
        qt['confirmed'] = max(int(qt.get('confirmed', 0) or 0), int(lifecycle.get('confirmed', 0) or 0))
        qt['confirm_queued'] = max(int(qt.get('confirm_queued', 0) or 0), int(effective_totals.get('confirm', 0) or 0))
        qt['probable'] = max(int(qt.get('probable', 0) or 0), int(lifecycle.get('probable', 0) or 0))
        return jsonify({
            "ok": True,
            "confirm_rate": econ.get('confirm_conversion_rate', 0.0),
            "reconsult_roi": econ.get('reconsult_roi', 0.0),
            "quality_telemetry": qt,
            "lifecycle": lifecycle,
            "decision_intent_totals": intent_totals,
            "decision_effective_totals": effective_totals,
            "effective_status_counts": _effective_status_counts(vectors),
            "economics": econ,
            "explainability": dict(econ.get('explainability') or {}),
            "runtime_snapshot_source": projection_source_label(snapshot=snapshot, fallback='legacy'),
            "queue_followups": int(snap_queues.get('followup_count', 0) or 0),
            "queue_precision": int(snap_queues.get('precision_count', 0) or 0),
            "skip_telemetry": {
                'precheck_skip_count': int(snap_telemetry.get('precheck_skip_count', 0) or 0),
                'dns_skip_total': int(snap_telemetry.get('dns_skip_total', 0) or 0),
                'host_cooldown_skip_total': int(snap_telemetry.get('host_cooldown_skip_total', 0) or 0),
                'execution_gate_skip_total': int(snap_telemetry.get('execution_gate_skip_total', 0) or 0),
            },
            "latest_run": snap_latest,
        })

    @app.route("/api/findings-table")
    def api_findings_table():
        vectors = _latest_run_vectors(200)
        if vectors:
            items = []
            for idx, row in enumerate(vectors, start=1):
                explain = row.get('decision_explain') if isinstance(row.get('decision_explain'), dict) else {}
                scores = explain.get('scores') if isinstance(explain.get('scores'), dict) else {}
                qual = row.get('qualification') if isinstance(row.get('qualification'), dict) else {}
                runtime_decision = row.get('runtime_decision') if isinstance(row.get('runtime_decision'), dict) else {}
                adaptation_signal = row.get('adaptation_signal') if isinstance(row.get('adaptation_signal'), dict) else {}
                success_semantics = row.get('success_semantics') if isinstance(row.get('success_semantics'), dict) else {}
                decision_intent_flags = row.get('decision_intent_flags') if isinstance(row.get('decision_intent_flags'), dict) else (runtime_decision.get('intent_flags') if isinstance(runtime_decision.get('intent_flags'), dict) else {})
                decision_effective_flags = row.get('decision_flags') if isinstance(row.get('decision_flags'), dict) else (runtime_decision.get('effective_flags') if isinstance(runtime_decision.get('effective_flags'), dict) else {})
                decision_effective_reasons = row.get('decision_effective_reasons') if isinstance(row.get('decision_effective_reasons'), dict) else (runtime_decision.get('effective_reasons') if isinstance(runtime_decision.get('effective_reasons'), dict) else {})
                decision_effective_blockers = row.get('decision_effective_blockers') if isinstance(row.get('decision_effective_blockers'), dict) else (runtime_decision.get('effective_blockers') if isinstance(runtime_decision.get('effective_blockers'), dict) else {})
                items.append({
                    "id": idx,
                    "target": row.get("target") or "-",
                    "status": row.get("engine_status") or "unknown",
                    "classification": row.get("classification") or "unknown",
                    "verdict": qual.get('verdict', 'none'),
                    "confidence": qual.get('confidence', scores.get('qualification_confidence', 0.0)),
                    "summary": (explain.get('summary') or row.get("objective") or "-"),
                    "reason": explain.get('summary') or '-',
                    "task_family": row.get('task_family') or '-',
                    "success_eval": row.get('success_criteria_eval') or row.get('decision_effective_status') or '-',
                    "priority_score": (row.get('decision_economics') or {}).get('priority_score', 0.0) if isinstance(row.get('decision_economics'), dict) else 0.0,
                    "signal_assessment": row.get('signal_assessment') or {},
                    "decision_explain": row.get('decision_explain') or {},
                    "decision_economics": row.get('decision_economics') or {},
                    "decision_intent_flags": decision_intent_flags,
                    "decision_effective_flags": decision_effective_flags,
                    "decision_effective_status": row.get('decision_effective_status') or runtime_decision.get('effective_status') or 'unknown',
                    "decision_effective_summary": row.get('decision_effective_summary') or runtime_decision.get('effective_summary') or '-',
                    "decision_effective_reasons": decision_effective_reasons,
                    "decision_effective_blockers": decision_effective_blockers,
                    "execution_gate": row.get('execution_gate') or {},
                    "host_state_band": row.get('host_state_band') or ((row.get('host_transition') or {}).get('to_band') if isinstance(row.get('host_transition'), dict) else '') or '-',
                    "host_transition": row.get('host_transition') or {},
                    "host_regeneration_reason": row.get('host_regeneration_reason') or '-',
                    "adaptation_signal": adaptation_signal,
                    "analysis_contract": row.get('analysis_contract') or {},
                    "signal_contract": row.get('signal_contract') or {},
                    "success_semantics": success_semantics,
                    "runtime_utility": row.get('runtime_utility') or {},
                    "runtime_decision": runtime_decision,
                    "runtime_task": row.get('runtime_task') or {},
                    "semantic_lineage_summary": row.get('semantic_lineage_summary') or {},
                    "run_contamination": row.get('run_contamination') or {},
                    "request_shape_hygiene": row.get('request_shape_hygiene') or {},
                    "workflow_promotion_status": row.get('workflow_promotion_status') or '-',
                    "finding_signal_status": row.get('finding_signal_status') or '-',
                    "success_outcome_status": row.get('success_outcome_status') or '-',
                    "adaptation_feedback_status": row.get('adaptation_feedback_status') or '-',
                })
            return jsonify({"items": items})
        rows = _latest_log_rows(200)
        items = []
        for idx, row in enumerate(rows, start=1):
            items.append({
                "id": idx,
                "target": row.get("decision") or "-",
                "status": row.get("status") or "unknown",
                "classification": row.get("status") or "unknown",
                "verdict": "none",
                "confidence": 0.0,
                "summary": row.get("result") or "-",
                "decision_intent_flags": {"retry": False, "confirm": False, "followup": False, "precision": False},
                "decision_effective_flags": {"retry": False, "confirm": False, "followup": False, "precision": False},
                "decision_effective_status": "unknown",
                "decision_effective_summary": "-",
                "decision_effective_reasons": {},
                "decision_effective_blockers": {},
                "execution_gate": {},
                "host_state_band": "-",
                "host_transition": {},
                "host_regeneration_reason": "-",
                "runtime_task": {},
                "semantic_lineage_summary": {},
                "signal_contract": {},
                "success_semantics": {},
                "workflow_promotion_status": "-",
                "finding_signal_status": "-",
                "success_outcome_status": "-",
                "adaptation_feedback_status": "-",
            })
        return jsonify({"items": items})

    @app.route("/api/policy-gate-history")
    def api_policy_gate_history():
        return jsonify(fetch_filtered_logs(page=max(1, int(request.args.get("page", 1))), per_page=max(1, min(100, int(request.args.get("per_page", 20)))), keywords=["owner_approval_required", "owner approval", "credentials_require_owner_approval", "out_of_scope", "policy", "blocked"], exclude_ids=[]))

    @app.route("/api/owner-approvals")
    def api_owner_approvals():
        acted = _load_owner_approval_actions()
        acted_ids = set((acted.get("approved_ids") or []) + (acted.get("deleted_ids") or []))
        return jsonify(fetch_filtered_logs(page=max(1, int(request.args.get("page", 1))), per_page=max(1, min(100, int(request.args.get("per_page", 20)))), keywords=["owner_approval_required", "owner approval", "credentials_require_owner_approval"], exclude_ids=list(acted_ids)))

    @app.route("/api/owner-approvals/approve-all", methods=["POST"])
    def api_owner_approvals_approve_all():
        data = _load_owner_approval_actions()
        ids = _owner_approval_row_ids()
        data["approved_ids"] = sorted(set((data.get("approved_ids") or []) + ids))
        _save_owner_approval_actions(data)
        return jsonify({"ok": True, "approved": len(ids)})

    @app.route("/api/owner-approvals/delete-all", methods=["POST"])
    def api_owner_approvals_delete_all():
        data = _load_owner_approval_actions()
        ids = _owner_approval_row_ids()
        data["deleted_ids"] = sorted(set((data.get("deleted_ids") or []) + ids))
        _save_owner_approval_actions(data)
        return jsonify({"ok": True, "deleted": len(ids)})

    @app.route("/api/runtime-logs")
    def api_runtime_logs():
        stream = str(request.args.get("stream") or "stdout").lower()
        lines = max(1, min(500, _safe_int(request.args.get("lines"), 120)))
        path = RUNTIME_STDERR_PATH if stream == "stderr" else RUNTIME_STDOUT_PATH
        return jsonify({"ok": True, "stream": stream, "content": read_tail(path, lines=lines)})
