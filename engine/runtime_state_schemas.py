from __future__ import annotations

from typing import Any, Dict


def _require_object(data: Any, name: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f'{name}_must_be_object')
    return dict(data)


def _normalize_request_decoration_cfg(value: Any) -> Dict[str, Any]:
    raw = dict(value or {}) if isinstance(value, dict) else {}
    headers_in = raw.get('headers') if isinstance(raw.get('headers'), list) else []
    cookies_in = raw.get('cookies') if isinstance(raw.get('cookies'), list) else []
    notes_in = raw.get('provenance_notes') if isinstance(raw.get('provenance_notes'), list) else []

    headers = []
    for item in headers_in:
        if isinstance(item, dict):
            headers.append({
                'name': str(item.get('name') or '').strip(),
                'value': str(item.get('value') or ''),
                'source': str(item.get('source') or 'operator_supplied').strip() or 'operator_supplied',
            })
        elif str(item).strip():
            text = str(item).strip()
            if ':' in text:
                name, val = text.split(':', 1)
                headers.append({'name': name.strip(), 'value': val.strip(), 'source': 'operator_supplied'})
            else:
                headers.append({'name': text, 'value': '', 'source': 'operator_supplied'})

    cookies = []
    for item in cookies_in:
        if isinstance(item, dict):
            cookies.append({
                'name': str(item.get('name') or '').strip(),
                'value': str(item.get('value') or ''),
                'source': str(item.get('source') or 'operator_supplied').strip() or 'operator_supplied',
            })
        elif str(item).strip():
            text = str(item).strip()
            if '=' in text:
                name, val = text.split('=', 1)
                cookies.append({'name': name.strip(), 'value': val.strip(), 'source': 'operator_supplied'})
            else:
                cookies.append({'name': text, 'value': '', 'source': 'operator_supplied'})

    basic_auth_in = raw.get('basic_auth') if isinstance(raw.get('basic_auth'), dict) else {}
    basic_auth = {
        'enabled': bool(basic_auth_in.get('enabled', False)),
        'username': str(basic_auth_in.get('username') or ''),
        'password': str(basic_auth_in.get('password') or ''),
        'password_ref': str(basic_auth_in.get('password_ref') or ''),
    }

    mode = str(raw.get('mode') or '').strip().lower()
    if mode not in {'none', 'campaign_required', 'operator_supplied', 'mixed'}:
        mode = 'operator_supplied' if (headers or cookies or basic_auth['enabled']) else 'none'

    return {
        'mode': mode,
        'headers': headers,
        'cookies': cookies,
        'basic_auth': basic_auth,
        'provenance_notes': [str(x) for x in notes_in if str(x).strip()],
    }


def _normalize_campaign_cfg(cfg: Any) -> Dict[str, Any]:
    out = dict(cfg or {}) if isinstance(cfg, dict) else {}
    out['request_decoration'] = _normalize_request_decoration_cfg(out.get('request_decoration'))
    out['credentials_required'] = bool(out.get('credentials_required', False))
    out['allow_auth_header'] = bool(out.get('allow_auth_header', False))
    out['allow_cookie_header'] = bool(out.get('allow_cookie_header', False))
    out['allow_basic_auth'] = bool(out.get('allow_basic_auth', False))
    out['credentials_owner_approved'] = bool(out.get('credentials_owner_approved', False))
    out['bug_bounty_username'] = str(out.get('bug_bounty_username') or '')
    out['test_account_email'] = str(out.get('test_account_email') or '')
    out['max_runs'] = max(1, min(500, int(out.get('max_runs', 300) or 300)))
    out['target_load_limit'] = max(1, min(2000, int(out.get('target_load_limit', out['max_runs'] * 2) or (out['max_runs'] * 2))))
    out['time_budget_min'] = max(5, min(240, int(out.get('time_budget_min', 60) or 60)))
    retry_policy = str(out.get('retry_policy', 'balanced') or 'balanced').strip().lower()
    out['retry_policy'] = retry_policy if retry_policy in {'strict', 'balanced', 'aggressive'} else 'balanced'
    if out.get('aggression_override') not in (None, ''):
        out['aggression_override'] = max(1, min(10, int(out.get('aggression_override') or 1)))
    else:
        out['aggression_override'] = None
    if out.get('aggression_effective') not in (None, ''):
        out['aggression_effective'] = max(1, min(10, int(out.get('aggression_effective') or 1)))
    else:
        out['aggression_effective'] = None
    if 'owner_override' in out:
        out['owner_override'] = bool(out.get('owner_override'))
    return out


def normalize_campaign_settings(data: Any) -> Dict[str, Any]:
    raw = _require_object(data, 'campaign_settings')
    global_cfg = _normalize_campaign_cfg(raw.get('global') or {}) if isinstance(raw.get('global'), dict) else _normalize_campaign_cfg({})
    by_campaign_raw = raw.get('by_campaign') if isinstance(raw.get('by_campaign'), dict) else {}
    by_campaign = {str(k): _normalize_campaign_cfg(v) for k, v in by_campaign_raw.items() if isinstance(v, dict)}
    raw['global'] = global_cfg
    raw['by_campaign'] = by_campaign
    return raw


def normalize_orchestrator_state(data: Any) -> Dict[str, Any]:
    raw = _require_object(data, 'orchestrator_state')
    raw['selected_campaign_key'] = str(raw.get('selected_campaign_key') or '').strip()
    if raw.get('updated_at') is not None:
        raw['updated_at'] = str(raw.get('updated_at') or '')
    return raw


def normalize_runtime_campaign_state(data: Any) -> Dict[str, Any]:
    raw = _require_object(data, 'runtime_campaign_state')
    raw['paused'] = bool(raw.get('paused', False))
    raw['stopped'] = bool(raw.get('stopped', False))
    raw['owner_override'] = bool(raw.get('owner_override', False))
    if raw.get('updated_at') is not None:
        raw['updated_at'] = str(raw.get('updated_at') or '')
    return raw


def normalize_planner_ui_state(data: Any) -> Dict[str, Any]:
    raw = _require_object(data, 'planner_ui_state')
    raw['selected_campaign_key'] = str(raw.get('selected_campaign_key') or '').strip()
    return raw


def normalize_runtime_plan_meta(data: Any) -> Dict[str, Any]:
    raw = _require_object(data, 'runtime_plan_meta')
    int_fields = {
        'generated', 'prepared_attacks', 'target_count', 'input_total', 'plan_revision',
        'added_tasks', 'deprecated_tasks'
    }
    bool_fields = {'changed', 'material_change', 'skipped'}
    str_fields = {'campaign_key', 'generated_at', 'plan_hash', 'regeneration_reason', 'diff_reason'}
    for key in int_fields:
        if key in raw and raw.get(key) not in (None, ''):
            raw[key] = int(raw.get(key) or 0)
    for key in bool_fields:
        if key in raw:
            raw[key] = bool(raw.get(key))
    for key in str_fields:
        if key in raw and raw.get(key) is not None:
            raw[key] = str(raw.get(key) or '')
    if 'quality' in raw and not isinstance(raw.get('quality'), dict):
        raw.pop('quality', None)
    return raw


def normalize_host_state(data: Any) -> Dict[str, Any]:
    raw = _require_object(data, 'host_state')
    hosts_raw = raw.get('hosts') if isinstance(raw.get('hosts'), dict) else {}
    raw['hosts'] = {str(k): dict(v) for k, v in hosts_raw.items() if isinstance(v, dict)}
    return raw


def normalize_learning_store(data: Any) -> Dict[str, Any]:
    raw = _require_object(data, 'learning_store')
    for key in (
        'families',
        'hosts',
        'capabilities',
        'family_capabilities',
        'host_capability_pairs',
        'tools',
        'action_types',
        'host_stages',
        'planning_stages',
        'next_stages',
        'target_types',
        'target_surface_signals',
        'transitions',
        'host_transition_pairs',
        'progression_priors',
        'host_progression_priors',
        'branch_priors',
        'host_branch_priors',
    ):
        raw[key] = dict(raw.get(key) or {}) if isinstance(raw.get(key), dict) else {}
    if raw.get('updated_at') is not None:
        raw['updated_at'] = str(raw.get('updated_at') or '')
    else:
        raw['updated_at'] = None
    return raw


def normalize_runtime_snapshot(data: Any) -> Dict[str, Any]:
    raw = _require_object(data, 'runtime_snapshot')
    return raw
