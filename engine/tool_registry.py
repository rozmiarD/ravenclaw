from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import yaml

from json_state_io import atomic_write_json, safe_load_json_object  # type: ignore
from paths import REPORTS_DIR  # type: ignore

REGISTRY_PATH = Path(__file__).resolve().parent / 'tool_registry.yaml'
TOOL_REGISTRY_STATE_PATH = REPORTS_DIR / '.tool_registry.state.json'
DEFAULT_PLANNER_PROFILE = 'core'
EXTRA_EXEC_PATHS = ['/usr/sbin', '/sbin', '/usr/bin', '/bin', str(Path.home() / '.local' / 'bin')]


def _load_registry_raw() -> Dict[str, Any]:
    try:
        data = yaml.safe_load(REGISTRY_PATH.read_text(encoding='utf-8')) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_tool_registry() -> Dict[str, Any]:
    data = _load_registry_raw()
    tools = data.get('tools') if isinstance(data.get('tools'), dict) else {}
    profiles = data.get('profiles') if isinstance(data.get('profiles'), dict) else {}
    capabilities = data.get('capabilities') if isinstance(data.get('capabilities'), dict) else {}
    task_families = data.get('task_families') if isinstance(data.get('task_families'), dict) else {}
    defaults = data.get('defaults') if isinstance(data.get('defaults'), dict) else {}
    return {
        'version': int(data.get('version') or 1),
        'defaults': defaults,
        'profiles': profiles,
        'capabilities': capabilities,
        'task_families': task_families,
        'tools': tools,
    }


def _find_tool_binary(name: str) -> str | None:
    tool = str(name or '').strip()
    if not tool:
        return None
    hit = shutil.which(tool)
    if hit:
        return hit
    return shutil.which(tool, path=':'.join(EXTRA_EXEC_PATHS))


def _tool_meta(name: str, meta: Any) -> Dict[str, Any]:
    info = meta if isinstance(meta, dict) else {}
    planner_profiles = [str(x).strip().lower() for x in (info.get('planner_profiles') or []) if str(x).strip()]
    capabilities = [str(x).strip().lower() for x in (info.get('capabilities') or []) if str(x).strip()]
    families = [str(x).strip().lower() for x in (info.get('task_families') or []) if str(x).strip()]
    equivalents = [str(x).strip().lower() for x in (info.get('equivalent_tools') or []) if str(x).strip()]
    chain_roles = [str(x).strip().lower() for x in (info.get('supports_chain_role') or []) if str(x).strip()]
    target_kinds = [str(x).strip().lower() for x in (info.get('target_kinds') or []) if str(x).strip()]
    planner_stdin_args = [str(x) for x in (info.get('planner_stdin_args') or []) if str(x).strip()]
    target_validation_mode = str(info.get('target_validation_mode') or 'none').strip().lower() or 'none'
    resolved_bin = _find_tool_binary(str(name).strip())
    return {
        'name': str(name).strip().lower(),
        'enabled': bool(info.get('enabled', True)),
        'execution_allowed': bool(info.get('execution_allowed', True)),
        'category': str(info.get('category') or 'operator_support').strip().lower(),
        'planner_profiles': planner_profiles,
        'risk_level': str(info.get('risk_level') or 'low').strip().lower(),
        'noise_level': str(info.get('noise_level') or 'low').strip().lower(),
        'requires_auth_approval': bool(info.get('requires_auth_approval', False)),
        'supports_chain_role': chain_roles,
        'capabilities': capabilities,
        'task_families': families,
        'target_kinds': target_kinds,
        'equivalent_tools': equivalents,
        'normalization_mode': str(info.get('normalization_mode') or 'allow').strip().lower(),
        'target_validation_mode': target_validation_mode,
        'planner_invocation_mode': str(info.get('planner_invocation_mode') or 'direct_args').strip().lower() or 'direct_args',
        'planner_stdin_args': planner_stdin_args,
        'installed': resolved_bin is not None,
        'resolved_path': resolved_bin or '',
    }


def get_tool_catalog() -> Dict[str, Dict[str, Any]]:
    reg = load_tool_registry()
    tools = reg.get('tools') if isinstance(reg.get('tools'), dict) else {}
    return {str(name).strip().lower(): _tool_meta(str(name), meta) for name, meta in tools.items() if str(name).strip()}


def get_profile_catalog() -> Dict[str, Dict[str, Any]]:
    reg = load_tool_registry()
    profiles = reg.get('profiles') if isinstance(reg.get('profiles'), dict) else {}
    out: Dict[str, Dict[str, Any]] = {}
    for name, meta in profiles.items():
        if not str(name).strip():
            continue
        out[str(name).strip().lower()] = {
            'description': str((meta or {}).get('description') or '').strip(),
            'planner_visible': bool((meta or {}).get('planner_visible', False)),
            'inherits': [str(x).strip().lower() for x in ((meta or {}).get('inherits') or []) if str(x).strip()],
        }
    return out


def _expand_profile(profile: str, profiles: Dict[str, Dict[str, Any]], seen: Set[str] | None = None) -> Set[str]:
    p = str(profile or '').strip().lower()
    if not p:
        return set()
    seen = set(seen or set())
    if p in seen:
        return {p}
    seen.add(p)
    meta = profiles.get(p) or {}
    out = {p}
    for parent in meta.get('inherits') or []:
        out |= _expand_profile(str(parent), profiles, seen)
    return out


def _normalize_registry_state(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError('tool_registry_state_must_be_object')
    selected = str(data.get('selected_profile') or '').strip().lower()
    source = str(data.get('source') or '').strip().lower()
    return {
        'selected_profile': selected,
        'source': source,
    }


def load_tool_registry_state() -> Dict[str, Any]:
    data, _meta = safe_load_json_object(
        TOOL_REGISTRY_STATE_PATH,
        {'selected_profile': '', 'source': ''},
        normalizer=_normalize_registry_state,
        description='tool_registry_state',
    )
    return data


def save_tool_registry_state(selected_profile: str) -> Dict[str, Any]:
    profiles = get_profile_catalog()
    profile = str(selected_profile or '').strip().lower()
    meta = profiles.get(profile) or {}
    if not profile or not meta or not bool(meta.get('planner_visible', False)):
        raise ValueError(f'invalid_planner_profile:{profile}')
    TOOL_REGISTRY_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {'selected_profile': profile, 'source': 'config'}
    atomic_write_json(TOOL_REGISTRY_STATE_PATH, payload, indent=2, sort_keys=True)
    return payload


def _requested_profiles_from_value(value: Iterable[str] | str | None) -> List[str]:
    reg = load_tool_registry()
    defaults = reg.get('defaults') if isinstance(reg.get('defaults'), dict) else {}
    env_name = str(defaults.get('planner_profiles_env') or 'RAVENCLAW_BRAIN_TOOL_PROFILES').strip() or 'RAVENCLAW_BRAIN_TOOL_PROFILES'
    if value is None:
        raw = str(os.environ.get(env_name) or '').strip()
        if raw:
            return [x.strip().lower() for x in raw.split(',') if x.strip()]
        state = load_tool_registry_state()
        state_profile = str(state.get('selected_profile') or '').strip().lower()
        if state_profile:
            return [state_profile]
        return [str(defaults.get('planner_profile') or DEFAULT_PLANNER_PROFILE).strip().lower()]
    if isinstance(value, str):
        return [x.strip().lower() for x in value.split(',') if x.strip()]
    return [str(x).strip().lower() for x in value if str(x).strip()]


def resolve_planner_profiles(value: Iterable[str] | str | None = None) -> List[str]:
    requested = _requested_profiles_from_value(value)
    profiles = get_profile_catalog()
    expanded: Set[str] = set()
    for profile in requested:
        expanded |= _expand_profile(profile, profiles)
    if not expanded:
        expanded = {DEFAULT_PLANNER_PROFILE}
    ordered = [name for name in profiles if name in expanded]
    for name in sorted(expanded):
        if name not in ordered:
            ordered.append(name)
    return ordered


def get_active_planner_profile_state() -> Dict[str, Any]:
    profiles = get_profile_catalog()
    reg = load_tool_registry()
    defaults = reg.get('defaults') if isinstance(reg.get('defaults'), dict) else {}
    env_name = str(defaults.get('planner_profiles_env') or 'RAVENCLAW_BRAIN_TOOL_PROFILES').strip() or 'RAVENCLAW_BRAIN_TOOL_PROFILES'
    env_raw = str(os.environ.get(env_name) or '').strip()
    state = load_tool_registry_state()
    selected_profile = str(state.get('selected_profile') or '').strip().lower()
    source = 'default'
    requested_profiles: List[str]
    if env_raw:
        requested_profiles = [x.strip().lower() for x in env_raw.split(',') if x.strip()]
        active_profile = requested_profiles[-1] if requested_profiles else DEFAULT_PLANNER_PROFILE
        source = 'env'
    elif selected_profile:
        requested_profiles = [selected_profile]
        active_profile = selected_profile
        source = 'config'
    else:
        active_profile = str(defaults.get('planner_profile') or DEFAULT_PLANNER_PROFILE).strip().lower()
        requested_profiles = [active_profile]
    if active_profile not in profiles:
        active_profile = DEFAULT_PLANNER_PROFILE
        requested_profiles = [DEFAULT_PLANNER_PROFILE]
        if source != 'env':
            source = 'default'
    resolved_profiles = resolve_planner_profiles(requested_profiles)
    return {
        'active_profile': active_profile,
        'selected_profile': selected_profile,
        'requested_profiles': requested_profiles,
        'resolved_profiles': resolved_profiles,
        'source': source,
        'env_override': bool(env_raw),
        'env_name': env_name,
    }


def get_execution_allowed_tools() -> Set[str]:
    return {
        name for name, meta in get_tool_catalog().items()
        if bool(meta.get('enabled', True)) and bool(meta.get('execution_allowed', True))
    }


def get_planner_visible_tools(profiles: Iterable[str] | str | None = None) -> List[str]:
    active = set(resolve_planner_profiles(profiles))
    tools = []
    for name, meta in get_tool_catalog().items():
        if not bool(meta.get('enabled', True)) or not bool(meta.get('execution_allowed', True)):
            continue
        planner_profiles = set(meta.get('planner_profiles') or [])
        if planner_profiles & active:
            tools.append(name)
    return sorted(tools)


def get_all_planner_visible_tools() -> List[str]:
    profiles = get_profile_catalog()
    visible_profiles = [name for name, meta in profiles.items() if bool(meta.get('planner_visible', False))]
    return get_planner_visible_tools(visible_profiles)


def get_task_family_catalog() -> Dict[str, List[str]]:
    reg = load_tool_registry()
    data = reg.get('task_families') if isinstance(reg.get('task_families'), dict) else {}
    out: Dict[str, List[str]] = {}
    for name, caps in data.items():
        key = str(name).strip().lower()
        if not key:
            continue
        out[key] = [str(x).strip().lower() for x in (caps or []) if str(x).strip()]
    return out


def get_capability_catalog() -> Dict[str, Dict[str, Any]]:
    reg = load_tool_registry()
    data = reg.get('capabilities') if isinstance(reg.get('capabilities'), dict) else {}
    out: Dict[str, Dict[str, Any]] = {}
    for name, meta in data.items():
        key = str(name).strip().lower()
        if not key:
            continue
        out[key] = dict(meta or {})
    return out


def get_family_tool_coverage(profiles: Iterable[str] | str | None = None, *, planner_only: bool = True) -> Dict[str, List[str]]:
    families = get_task_family_catalog()
    tool_catalog = get_tool_catalog()
    if planner_only:
        allowed = set(get_planner_visible_tools(profiles))
    else:
        allowed = get_execution_allowed_tools()
    coverage: Dict[str, List[str]] = {fam: [] for fam in families}
    for tool, meta in tool_catalog.items():
        if tool not in allowed:
            continue
        for fam in meta.get('task_families') or []:
            if fam in coverage:
                coverage[fam].append(tool)
    for fam in coverage:
        coverage[fam] = sorted(dict.fromkeys(coverage[fam]))
    return coverage


def get_capability_tool_coverage(profiles: Iterable[str] | str | None = None, *, planner_only: bool = True) -> Dict[str, List[str]]:
    capabilities = get_capability_catalog()
    tool_catalog = get_tool_catalog()
    if planner_only:
        allowed = set(get_planner_visible_tools(profiles))
    else:
        allowed = get_execution_allowed_tools()
    coverage: Dict[str, List[str]] = {cap: [] for cap in capabilities}
    for tool, meta in tool_catalog.items():
        if tool not in allowed:
            continue
        for cap in meta.get('capabilities') or []:
            if cap in coverage:
                coverage[cap].append(tool)
    for cap in coverage:
        coverage[cap] = sorted(dict.fromkeys(coverage[cap]))
    return coverage


def get_tool_registry_ui_state() -> Dict[str, Any]:
    profile_state = get_active_planner_profile_state()
    profiles = get_profile_catalog()
    tools = get_tool_catalog()
    active_profile = str(profile_state.get('active_profile') or DEFAULT_PLANNER_PROFILE)
    options = []
    for name, meta in profiles.items():
        if not bool(meta.get('planner_visible', False)):
            continue
        visible = get_planner_visible_tools(name)
        options.append({
            'name': name,
            'description': str(meta.get('description') or ''),
            'tool_count': len(visible),
        })
    planner_visible = get_planner_visible_tools(active_profile)
    missing_installed = sorted([name for name in planner_visible if not bool((tools.get(name) or {}).get('installed', False))])
    return {
        'ok': True,
        **profile_state,
        'options': options,
        'planner_visible_count': len(planner_visible),
        'missing_installed_count': len(missing_installed),
    }
