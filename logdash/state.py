from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from planner_registry_loader import load_json_file, load_latest_registry_meta  # type: ignore


def build_initial_state() -> Dict[str, object]:
    return {
        "owner_override": False,
        "state": "idle",
        "pid": "-",
        "selected_campaign_key": "",
        "selected_campaign_name": "-",
        "planner_scope_targets": 0,
        "prepared_attacks": 0,
        "runtime_plan_ok": False,
        "runtime_plan_error_preview": "-",
        "credentials_required": False,
        "allow_auth_header": False,
        "allow_cookie_header": False,
        "allow_basic_auth": False,
        "credentials_owner_approved": False,
        "bug_bounty_username": "",
        "test_account_email": "",
        "request_decoration": {"mode": "none", "headers": [], "cookies": [], "basic_auth": {"enabled": False, "username": "", "password": "", "password_ref": ""}, "provenance_notes": []},
    }


def seed_credentials_from_store(STATE: Dict[str, object], load_campaign_settings: Callable[[], Dict[str, object]]) -> None:
    store = load_campaign_settings()
    global_cfg = store.get("global", {}) if isinstance(store.get("global"), dict) else {}
    if isinstance(global_cfg, dict):
        for key in (
            "credentials_required",
            "allow_auth_header",
            "allow_cookie_header",
            "allow_basic_auth",
            "credentials_owner_approved",
            "bug_bounty_username",
            "test_account_email",
            "request_decoration",
        ):
            if key in global_cfg:
                STATE[key] = global_cfg.get(key)


def seed_selected_campaign_state(
    STATE: Dict[str, object],
    *,
    load_orchestrator_state: Callable[[], Dict[str, object]],
    planner_ui_state_path: Path,
    planner_registry_root: Path,
) -> None:
    key = ""
    try:
        o = load_orchestrator_state()
        if isinstance(o, dict):
            key = str(o.get("selected_campaign_key") or "").strip()
    except Exception:
        key = ""
    if not key:
        try:
            ui, _ui_source = load_json_file(planner_ui_state_path, description='planner_ui_state')
            if isinstance(ui, dict):
                key = str(ui.get("selected_campaign_key") or "").strip()
        except Exception:
            key = ""
    if key:
        STATE["selected_campaign_key"] = key
        meta, _meta_source = load_latest_registry_meta(planner_registry_root, key)
        if meta:
            STATE["selected_campaign_name"] = str(meta.get("campaign_name") or key)
        else:
            STATE["selected_campaign_name"] = key
