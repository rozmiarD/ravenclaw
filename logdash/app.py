from __future__ import annotations

import argparse
import json
import hashlib
import importlib.util
import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, render_template, request

from db import fetch_logs, get_conn, init_db
from pages import register_page_routes
from api_supplemental import register_supplemental_api
from api_planner import register_planner_api
from api_runtime import register_runtime_api
from state import build_initial_state, seed_credentials_from_store, seed_selected_campaign_state
from services import (
    build_agents_status_payload as svc_build_agents_status_payload,
    build_campaign_info_payload as svc_build_campaign_info_payload,
    build_runtime_health_payload as svc_build_runtime_health_payload,
    build_selected_campaign_projection as svc_build_selected_campaign_projection,
    projection_source_label as svc_projection_source_label,
    compute_plan_counts,
    load_pipeline_config_effective_posture as svc_load_pipeline_config_effective_posture,
    fetch_filtered_logs as svc_fetch_filtered_logs,
    list_campaign_registry_items as svc_list_campaign_registry_items,
    load_host_state as svc_load_host_state,
    load_latest_blueprint as svc_load_latest_blueprint,
    load_owner_approval_actions as svc_load_owner_approval_actions,
    load_queue_state as svc_load_queue_state,
    load_runtime_snapshot as svc_load_runtime_snapshot,
    load_runtime_state as svc_load_runtime_state,
    owner_approval_row_ids as svc_owner_approval_row_ids,
    read_tail as svc_read_tail,
    refresh_runtime_state as svc_refresh_runtime_state,
    runtime_plan_status as svc_runtime_plan_status,
    save_owner_approval_actions as svc_save_owner_approval_actions,
    selected_runtime_snapshot_view as svc_selected_runtime_snapshot_view,
    write_runtime_state_file as svc_write_runtime_state_file,
)

init_db()
app = Flask(__name__, template_folder="templates", static_folder="static")

def _detect_app_version() -> str:
    cl = WORKSPACE_ROOT / "CHANGELOG.md"
    try:
        if cl.exists():
            for line in cl.read_text(encoding="utf-8", errors="ignore").splitlines():
                line=line.strip()
                if line.startswith("## "):
                    part=line[3:].split("/",1)[0].strip()
                    if part and part[0].isdigit():
                        return part
    except Exception:
        pass
    return "0.0.0"

WORKSPACE_ROOT = Path(os.getenv("RAVENCLAW_WORKSPACE") or str(Path(__file__).resolve().parents[1])).resolve()
ENGINE_DIR = WORKSPACE_ROOT / "engine"
REPORTS_DIR = Path(os.getenv("RAVENCLAW_REPORTS_DIR") or str(WORKSPACE_ROOT / "reports")).expanduser().resolve()
SCOPE_DIR = WORKSPACE_ROOT / "scope"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
from paths import OPENCLAW_CONFIG_PATH as PATHS_OPENCLAW_CONFIG_PATH, RUNTIME_PLAN_PATH as PATHS_RUNTIME_PLAN_PATH, LEGACY_RUNTIME_PLAN_PATH, first_existing  # type: ignore
from json_state_io import safe_load_json_object  # type: ignore
APP_VERSION = _detect_app_version()
from runtime_plan_service import (
    load_planner_ui_state as svc_load_planner_ui_state,
    save_planner_ui_state as svc_save_planner_ui_state,
    resolve_selected_campaign_key,
    load_campaign_blueprint_for_key,
    runtime_plan_entries_from_blueprint,
    write_runtime_plan,
    load_runtime_plan_meta as svc_load_runtime_plan_meta,
)
from runtime_campaign_state import (
    load_campaign_settings as svc_load_campaign_settings,
    save_campaign_settings as svc_save_campaign_settings,
    load_orchestrator_state,
    save_orchestrator_state,
    activate_campaign_key,
)
PLANNER_REGISTRY_ROOT = REPORTS_DIR / "campaign_registry"
OPENCLAW_CONFIG_PATH = PATHS_OPENCLAW_CONFIG_PATH
PIPELINE_CONFIG_PATH = Path(os.getenv("RAVENCLAW_PIPELINE_CONFIG") or str(ENGINE_DIR / "pipeline_config.json")).expanduser().resolve()
FEATURE_FLAGS_PATH = ENGINE_DIR / "feature_flags.py"
CAMPAIGN_SETTINGS_PATH = REPORTS_DIR / ".campaign.settings.json"
QUEUE_STATE_PATH = REPORTS_DIR / ".auto_campaign.queues.json"
RUNTIME_STDOUT_PATH = REPORTS_DIR / ".auto_campaign.stdout.log"
RUNTIME_STDERR_PATH = REPORTS_DIR / ".auto_campaign.stderr.log"
RUNTIME_PID_PATH = REPORTS_DIR / ".auto_campaign.pid"
RUNTIME_STATE_PATH = REPORTS_DIR / ".auto_campaign.state.json"
RUNTIME_SNAPSHOT_PATH = REPORTS_DIR / ".runtime_snapshot.json"
BUDGETS_PATH = WORKSPACE_ROOT / "budgets.yaml"
OWNER_APPROVAL_ACTIONS_PATH = REPORTS_DIR / ".owner_approval_actions.json"
PLANNER_UI_STATE_PATH = REPORTS_DIR / ".planner.ui.state.json"
ORCHESTRATOR_STATE_PATH = REPORTS_DIR / ".orchestrator.state.json"
RUNTIME_PLAN_PATH = first_existing(PATHS_RUNTIME_PLAN_PATH, LEGACY_RUNTIME_PLAN_PATH)
RUNTIME_PLAN_META_PATH = REPORTS_DIR / ".runtime_plan.meta.json"
HOST_STATE_PATH = REPORTS_DIR / ".host_state.json"

STATUS_CLASSES = {
    "success": "status-success",
    "ok": "status-success",
    "approved": "status-success",
    "in_progress": "status-warn",
    "running": "status-warn",
    "pending": "status-warn",
    "warning": "status-warn",
    "failed": "status-error",
    "error": "status-error",
    "blocked": "status-error",
}

STATE: Dict[str, object] = build_initial_state()


def render_page(template_name: str, *, page_title: str, active_page: str):
    return render_template(
        template_name,
        app_version=APP_VERSION,
        page_title=page_title,
        active_page=active_page,
    )


register_page_routes(app, render_page)


def _load_feature_flags():
    if not FEATURE_FLAGS_PATH.exists():
        return {}, None
    spec = importlib.util.spec_from_file_location("feature_flags", FEATURE_FLAGS_PATH)
    if spec is None or spec.loader is None:
        return {}, None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    defaults = getattr(module, "PIPELINE_FLAG_DEFAULTS", {})
    normalize = getattr(module, "normalize_pipeline_flags", None)
    return dict(defaults), normalize


def load_pipeline_config() -> Dict[str, object]:
    defaults, normalize = _load_feature_flags()
    data: Dict[str, object] = {}
    if PIPELINE_CONFIG_PATH.exists():
        data, _meta = safe_load_json_object(
            PIPELINE_CONFIG_PATH,
            {},
            description='pipeline_config',
        )
    merged = {**defaults, **(data or {})}
    if normalize:
        merged = normalize(merged)
    if not PIPELINE_CONFIG_PATH.exists():
        save_pipeline_config(merged)
    return merged


def _seed_credentials_from_store() -> None:
    seed_credentials_from_store(STATE, load_campaign_settings)


def _seed_selected_campaign_state() -> None:
    seed_selected_campaign_state(
        STATE,
        load_orchestrator_state=load_orchestrator_state,
        planner_ui_state_path=PLANNER_UI_STATE_PATH,
        planner_registry_root=PLANNER_REGISTRY_ROOT,
    )


def save_pipeline_config(payload: Dict[str, object]) -> Dict[str, object]:
    defaults, normalize = _load_feature_flags()
    current: Dict[str, object] = {}
    if PIPELINE_CONFIG_PATH.exists():
        raw, _meta = safe_load_json_object(
            PIPELINE_CONFIG_PATH,
            {},
            description='pipeline_config',
        )
        if isinstance(raw, dict):
            current = raw
    merged = {**defaults, **current, **(payload or {})}
    if normalize:
        merged = normalize(merged)
    PIPELINE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    PIPELINE_CONFIG_PATH.write_text(json.dumps(merged, indent=2, sort_keys=True))
    return merged


def pipeline_config_meta() -> Dict[str, str]:
    if not PIPELINE_CONFIG_PATH.exists():
        return {"last_applied": "-", "checksum": "-"}
    data = PIPELINE_CONFIG_PATH.read_text()
    checksum = sha256(data.encode("utf-8")).hexdigest()[:16]
    mtime = datetime.fromtimestamp(PIPELINE_CONFIG_PATH.stat().st_mtime).isoformat(timespec="seconds")
    return {"last_applied": mtime, "checksum": checksum}


def load_campaign_settings() -> Dict[str, object]:
    return svc_load_campaign_settings()


def save_campaign_settings(store: Dict[str, object]) -> None:
    svc_save_campaign_settings(store)


def load_runtime_state() -> Dict[str, object]:
    return svc_load_runtime_state(REPORTS_DIR, RUNTIME_SNAPSHOT_PATH)


def runtime_plan_status() -> Dict[str, object]:
    return svc_runtime_plan_status(REPORTS_DIR)


def _compute_plan_counts() -> Dict[str, int]:
    return compute_plan_counts(RUNTIME_PLAN_PATH)


def load_host_state() -> Dict[str, object]:
    return svc_load_host_state(HOST_STATE_PATH)


def refresh_runtime_state() -> None:
    return svc_refresh_runtime_state(
        STATE,
        get_conn=get_conn,
        runtime_state_path=RUNTIME_STATE_PATH,
        runtime_pid_path=RUNTIME_PID_PATH,
        reports_dir=REPORTS_DIR,
    )


def _load_owner_approval_actions() -> Dict[str, object]:
    return svc_load_owner_approval_actions(OWNER_APPROVAL_ACTIONS_PATH)


def _save_owner_approval_actions(data: Dict[str, object]) -> None:
    return svc_save_owner_approval_actions(REPORTS_DIR, OWNER_APPROVAL_ACTIONS_PATH, data)


def _owner_approval_row_ids() -> list[int]:
    return svc_owner_approval_row_ids(get_conn, init_db)


def fetch_filtered_logs(page: int, per_page: int, keywords: List[str], exclude_ids: List[int] | None = None) -> Dict[str, object]:
    return svc_fetch_filtered_logs(get_conn, init_db, page, per_page, keywords, exclude_ids)


def load_queue_state() -> Dict[str, object]:
    return svc_load_queue_state(QUEUE_STATE_PATH, RUNTIME_SNAPSHOT_PATH)


def load_planner_ui_state() -> Dict[str, object]:
    return svc_load_planner_ui_state()


def save_planner_ui_state(data: Dict[str, object]) -> None:
    svc_save_planner_ui_state(data)


def selected_campaign_key() -> str:
    return resolve_selected_campaign_key(str(STATE.get("selected_campaign_key") or "").strip())


def load_latest_blueprint() -> Dict[str, object] | None:
    return svc_load_latest_blueprint(selected_campaign_key(), PLANNER_REGISTRY_ROOT)


def load_runtime_snapshot() -> Dict[str, object]:
    return svc_load_runtime_snapshot(RUNTIME_SNAPSHOT_PATH)


def read_tail(path: Path, lines: int = 120) -> str:
    return svc_read_tail(path, lines=lines)


def load_agent_models() -> Dict[str, str]:
    if not OPENCLAW_CONFIG_PATH.exists():
        return {}
    data, _meta = safe_load_json_object(
        OPENCLAW_CONFIG_PATH,
        {},
        description='openclaw_config',
    )
    agents = (data.get("agents", {}) or {}).get("list", [])
    out: Dict[str, str] = {}
    if isinstance(agents, list):
        for a in agents:
            if not isinstance(a, dict):
                continue
            aid = str(a.get("id") or "").strip()
            model = str(a.get("model") or "").strip()
            if aid and model:
                out[aid] = model
    return out


def _list_campaign_registry_items() -> List[Dict[str, object]]:
    return svc_list_campaign_registry_items(PLANNER_REGISTRY_ROOT, selected_campaign_key())


def _resolve_scope_path(scope_txt: str) -> Path:
    raw = str(scope_txt or "").strip()
    if not raw:
        raw = "scope/scope.txt"
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = (WORKSPACE_ROOT / p).resolve()
    else:
        p = p.resolve()
    return p


def _runtime_plan_entries_from_blueprint(bp: Dict[str, object]) -> List[Dict[str, object]]:
    return runtime_plan_entries_from_blueprint(bp)


def _persist_blueprint_and_templates(version_dir: Path, bp_path: Path, blueprint: dict) -> None:
    bp_path.write_text(json.dumps(blueprint, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        import yaml  # type: ignore
        (version_dir / "blueprint.yaml").write_text(yaml.safe_dump(blueprint, sort_keys=False, allow_unicode=True), encoding="utf-8")
    except Exception:
        pass
    try:
        if str(ENGINE_DIR) not in sys.path:
            sys.path.insert(0, str(ENGINE_DIR))
        from planer.templates import build_templates  # type: ignore
        templates = build_templates(blueprint)
        tdir = version_dir / 'templates'
        tdir.mkdir(parents=True, exist_ok=True)
        for name, body in templates.items():
            (tdir / name).write_text(body, encoding='utf-8')
    except Exception:
        pass


register_planner_api(
    app,
    {
        "STATE": STATE,
        "selected_campaign_key": selected_campaign_key,
        "load_campaign_blueprint_for_key": load_campaign_blueprint_for_key,
        "runtime_plan_entries_from_blueprint": _runtime_plan_entries_from_blueprint,
        "write_runtime_plan": write_runtime_plan,
        "load_runtime_plan_meta": svc_load_runtime_plan_meta,
        "load_runtime_state": load_runtime_state,
        "load_runtime_snapshot": load_runtime_snapshot,
        "selected_runtime_snapshot_view": lambda runtime=None, selected_key=None: svc_selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else selected_campaign_key())),
        "build_selected_campaign_projection": svc_build_selected_campaign_projection,
        "projection_source_label": svc_projection_source_label,
        "load_planner_ui_state": load_planner_ui_state,
        "load_latest_blueprint": load_latest_blueprint,
        "_list_campaign_registry_items": _list_campaign_registry_items,
        "save_planner_ui_state": save_planner_ui_state,
        "activate_campaign_key": activate_campaign_key,
        "RUNTIME_PLAN_PATH": RUNTIME_PLAN_PATH,
        "ENGINE_DIR": ENGINE_DIR,
        "WORKSPACE_DIR": WORKSPACE_ROOT,
        "SCOPE_DIR": SCOPE_DIR,
        "BUDGETS_PATH": BUDGETS_PATH,
        "PLAN_CAMPAIGN_SCRIPT": ENGINE_DIR / "plan_campaign.py",
        "PLANNER_REGISTRY_ROOT": PLANNER_REGISTRY_ROOT,
    },
)

register_runtime_api(
    app,
    {
        "STATE": STATE,
        "refresh_runtime_state": refresh_runtime_state,
        "load_agent_models": load_agent_models,
        "selected_campaign_key": selected_campaign_key,
        "load_runtime_state": load_runtime_state,
        "load_runtime_snapshot": load_runtime_snapshot,
        "load_pipeline_config": load_pipeline_config,
        "save_pipeline_config": save_pipeline_config,
        "pipeline_config_meta": pipeline_config_meta,
        "selected_runtime_snapshot_view": lambda runtime=None, selected_key=None: svc_selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else selected_campaign_key())),
        "build_agents_status_payload": svc_build_agents_status_payload,
        "build_selected_campaign_projection": svc_build_selected_campaign_projection,
        "projection_source_label": svc_projection_source_label,
        "load_pipeline_config_effective_posture": lambda: svc_load_pipeline_config_effective_posture(load_pipeline_config()),
    },
)

register_supplemental_api(
    app,
    {
        "STATE": STATE,
        "STATUS_CLASSES": STATUS_CLASSES,
        "fetch_logs": fetch_logs,
        "get_conn": get_conn,
        "refresh_runtime_state": refresh_runtime_state,
        "load_runtime_state": load_runtime_state,
        "load_queue_state": load_queue_state,
        "load_campaign_settings": load_campaign_settings,
        "save_campaign_settings": save_campaign_settings,
        "load_pipeline_config": load_pipeline_config,
        "save_pipeline_config": save_pipeline_config,
        "pipeline_config_meta": pipeline_config_meta,
        "load_latest_blueprint": load_latest_blueprint,
        "selected_campaign_key": selected_campaign_key,
        "_list_campaign_registry_items": _list_campaign_registry_items,
        "load_host_state": load_host_state,
        "read_tail": read_tail,
        "RUNTIME_STDOUT_PATH": RUNTIME_STDOUT_PATH,
        "RUNTIME_STDERR_PATH": RUNTIME_STDERR_PATH,
        "_load_owner_approval_actions": _load_owner_approval_actions,
        "_save_owner_approval_actions": _save_owner_approval_actions,
        "_owner_approval_row_ids": _owner_approval_row_ids,
        "fetch_filtered_logs": fetch_filtered_logs,
        "save_planner_ui_state": save_planner_ui_state,
        "load_planner_ui_state": load_planner_ui_state,
        "HOST_STATE_PATH": HOST_STATE_PATH,
        "save_orchestrator_state": save_orchestrator_state,
        "RUNTIME_PLAN_META_PATH": RUNTIME_PLAN_META_PATH,
        "RUNTIME_PLAN_DELETE_PATHS": [PATHS_RUNTIME_PLAN_PATH, LEGACY_RUNTIME_PLAN_PATH],
        "PLANNER_REGISTRY_ROOT": PLANNER_REGISTRY_ROOT,
        "selected_runtime_snapshot_view": lambda runtime=None, selected_key=None: svc_selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else selected_campaign_key())),
        "build_campaign_info_payload": svc_build_campaign_info_payload,
        "build_runtime_health_payload": svc_build_runtime_health_payload,
        "build_selected_campaign_projection": svc_build_selected_campaign_projection,
        "projection_source_label": svc_projection_source_label,
        "RUNTIME_SNAPSHOT_PATH": RUNTIME_SNAPSHOT_PATH,
        "RUNTIME_STATE_PATH": RUNTIME_STATE_PATH,
        "RUNTIME_PID_PATH": RUNTIME_PID_PATH,
        "ENGINE_DIR": ENGINE_DIR,
        "WORKSPACE_DIR": WORKSPACE_ROOT,
        "PYTHON_BIN": sys.executable,
        "write_runtime_state_file": lambda state, paused=None: svc_write_runtime_state_file(REPORTS_DIR, RUNTIME_STATE_PATH, state, paused=paused),
        "runtime_alive_pid": lambda: _runtime_alive_pid(),
        "spawn_runtime_process": lambda campaign_key: _spawn_runtime_process(campaign_key),
        "terminate_runtime_process": lambda pid: _terminate_runtime_process(pid),
    },
)


def parse_args():
    parser = argparse.ArgumentParser(description="Log dashboard server")
    parser.add_argument("--port", type=int, default=9091, help="Port to bind (default: 9091)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    return parser.parse_args()


_seed_credentials_from_store()
_seed_selected_campaign_state()


if __name__ == "__main__":
    init_db()
    args = parse_args()
    print(f"[*] Log dashboard running on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
