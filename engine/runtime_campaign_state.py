from __future__ import annotations

import os
from typing import Any, Dict

from aggression_policy import clamp_aggression  # type: ignore
from json_state_io import atomic_write_json, safe_load_json_object  # type: ignore
from paths import REPORTS_DIR  # type: ignore
from runtime_plan_service import load_planner_ui_state, save_planner_ui_state, resolve_selected_campaign_key  # type: ignore
from runtime_state_schemas import normalize_campaign_settings, normalize_orchestrator_state, normalize_runtime_campaign_state  # type: ignore
from time_utils import utc_now_iso

CAMPAIGN_SETTINGS_PATH = REPORTS_DIR / '.campaign.settings.json'
ORCHESTRATOR_STATE_PATH = REPORTS_DIR / '.orchestrator.state.json'
CAMPAIGN_STATE_PATH = REPORTS_DIR / '.auto_campaign.state.json'


def load_campaign_settings() -> Dict[str, object]:
    data, _meta = safe_load_json_object(
        CAMPAIGN_SETTINGS_PATH,
        {'global': {}, 'by_campaign': {}},
        normalizer=normalize_campaign_settings,
        description='campaign_settings',
    )
    return data


def save_campaign_settings(store: Dict[str, object]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(CAMPAIGN_SETTINGS_PATH, normalize_campaign_settings(store), indent=2, sort_keys=True)


def load_orchestrator_state() -> Dict[str, object]:
    data, _meta = safe_load_json_object(
        ORCHESTRATOR_STATE_PATH,
        {},
        normalizer=normalize_orchestrator_state,
        description='orchestrator_state',
    )
    return data


def save_orchestrator_state(data: Dict[str, object]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(ORCHESTRATOR_STATE_PATH, normalize_orchestrator_state(data), indent=2, sort_keys=True)


def load_runtime_campaign_state() -> Dict[str, object]:
    data, _meta = safe_load_json_object(
        CAMPAIGN_STATE_PATH,
        {},
        normalizer=normalize_runtime_campaign_state,
        description='runtime_campaign_state',
    )
    return data


def resolve_campaign_key(explicit: str | None = None, prefer_env: bool = True) -> str:
    key = str(explicit or '').strip()
    if key:
        return key
    if prefer_env:
        env_key = str(os.environ.get('AUTO_CAMPAIGN_KEY') or '').strip()
        if env_key:
            return env_key
    orch = load_orchestrator_state()
    key = str(orch.get('selected_campaign_key') or '').strip()
    if key:
        return key
    return resolve_selected_campaign_key('')


def campaign_settings_for_key(selected_key: str | None = None) -> Dict[str, Any]:
    selected_key = resolve_campaign_key(selected_key)
    store = load_campaign_settings()
    global_cfg = store.get('global', {}) if isinstance(store.get('global'), dict) else {}
    by_campaign = store.get('by_campaign', {}) if isinstance(store.get('by_campaign'), dict) else {}
    cfg: Dict[str, Any] = dict(global_cfg) if isinstance(global_cfg, dict) else {}
    if selected_key and isinstance(by_campaign.get(selected_key), dict):
        cfg.update(by_campaign.get(selected_key) or {})
    cfg['resolved_campaign_key'] = selected_key
    return cfg


def credentials_runtime_policy(selected_key: str | None = None) -> Dict[str, Any]:
    out = {
        'credentials_required': False,
        'allow_auth_header': False,
        'allow_cookie_header': False,
        'allow_basic_auth': False,
        'credentials_owner_approved': False,
        'bug_bounty_username': '',
        'test_account_email': '',
        'request_decoration': {
            'mode': 'none',
            'headers': [],
            'cookies': [],
            'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''},
            'provenance_notes': [],
        },
        'resolved_campaign_key': '',
    }
    cfg = campaign_settings_for_key(selected_key)
    for k in out:
        if k in cfg:
            out[k] = cfg.get(k)
    out['resolved_campaign_key'] = str(cfg.get('resolved_campaign_key') or '')
    return out


def runtime_owner_override(default: bool = False) -> bool:
    state = load_runtime_campaign_state()
    return bool(state.get('owner_override', default)) if isinstance(state, dict) else bool(default)


def runtime_aggression_override(selected_key: str | None = None) -> int | None:
    cfg = campaign_settings_for_key(selected_key)
    raw = cfg.get('aggression_override') if isinstance(cfg, dict) else None
    if raw is None or raw == '':
        return None
    try:
        return clamp_aggression(int(raw))
    except Exception:
        return None


def activate_campaign_key(key: str) -> Dict[str, object]:
    key = str(key or '').strip()
    if not key:
        return {'ok': False, 'error': 'missing_campaign_key'}
    ui = load_planner_ui_state()
    ui.update({'selected_campaign_key': key})
    save_planner_ui_state(ui)
    save_orchestrator_state({'selected_campaign_key': key, 'updated_at': utc_now_iso()})
    return {'ok': True, 'selected_campaign_key': key}
