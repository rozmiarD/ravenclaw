from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from action_schema import ACTION_TYPE_TO_CAPABILITY, DEFAULT_ACTION_TYPE, DEFAULT_CAPABILITY  # type: ignore
from campaign_utils import extract_host_from_url  # type: ignore
from tool_registry import (  # type: ignore
    get_capability_tool_coverage,
    get_profile_catalog,
    get_task_family_catalog,
    get_planner_visible_tools,
    resolve_planner_profiles,
)

RECIPES_PATH = Path(__file__).with_name('capability_recipes.yaml')


def _normalize_text(value: Any) -> str:
    return str(value or '').strip().lower()


@lru_cache(maxsize=1)
def load_capability_recipe_book() -> Dict[str, Any]:
    try:
        data = yaml.safe_load(RECIPES_PATH.read_text(encoding='utf-8')) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_recipe_defaults() -> Dict[str, Any]:
    data = load_capability_recipe_book()
    defaults = data.get('defaults') if isinstance(data.get('defaults'), dict) else {}
    return dict(defaults)


def get_task_family_recipe_catalog() -> Dict[str, Dict[str, Any]]:
    data = load_capability_recipe_book()
    families = data.get('task_families') if isinstance(data.get('task_families'), dict) else {}
    out: Dict[str, Dict[str, Any]] = {}
    for name, meta in families.items():
        key = _normalize_text(name)
        if not key:
            continue
        out[key] = dict(meta or {})
    return out


def get_capability_recipe_catalog() -> Dict[str, Dict[str, Any]]:
    data = load_capability_recipe_book()
    capabilities = data.get('capabilities') if isinstance(data.get('capabilities'), dict) else {}
    out: Dict[str, Dict[str, Any]] = {}
    for name, meta in capabilities.items():
        key = _normalize_text(name)
        if not key:
            continue
        out[key] = dict(meta or {})
    return out


def get_named_recipe_catalog() -> Dict[str, Dict[str, Any]]:
    data = load_capability_recipe_book()
    recipes = data.get('recipes') if isinstance(data.get('recipes'), dict) else {}
    out: Dict[str, Dict[str, Any]] = {}
    for name, meta in recipes.items():
        key = _normalize_text(name)
        if not key:
            continue
        out[key] = dict(meta or {})
    return out


def _extract_target(action_spec: Dict[str, Any]) -> str:
    explicit = str(action_spec.get('target') or '').strip()
    if explicit:
        return explicit
    for token in list(action_spec.get('args') or []):
        s = str(token or '').strip().strip('"').strip("'")
        if s.startswith(('http://', 'https://')):
            return s
    return ''


def _render_recipe_arg(value: Any, *, target: str, target_host: str, selected_tool: str, capability: str) -> str:
    rendered = str(value or '')
    replacements = {
        '{target}': target,
        '{target_host}': target_host,
        '{selected_tool}': selected_tool,
        '{capability}': capability,
    }
    for token, repl in replacements.items():
        rendered = rendered.replace(token, repl)
    return rendered


def build_named_recipe_execution_plan(
    action_spec: Dict[str, Any],
    recipe_name: str,
    *,
    requested_profiles: Iterable[str] | str | None = None,
    allow_lab: bool | None = None,
) -> List[Dict[str, Any]]:
    recipe_key = _normalize_text(recipe_name)
    recipe = get_named_recipe_catalog().get(recipe_key) or {}
    if not recipe:
        return []
    action_type = _normalize_text(action_spec.get('action_type') or DEFAULT_ACTION_TYPE)
    capability = _normalize_text(action_spec.get('capability') or ACTION_TYPE_TO_CAPABILITY.get(action_type) or DEFAULT_CAPABILITY)
    recipe_action_type = _normalize_text(recipe.get('action_type'))
    recipe_capability = _normalize_text(recipe.get('capability'))
    if recipe_action_type and recipe_action_type != action_type:
        raise ValueError(f'recipe_action_type_mismatch:{recipe_key}:{recipe_action_type}:{action_type}')
    if recipe_capability and recipe_capability != capability:
        raise ValueError(f'recipe_capability_mismatch:{recipe_key}:{recipe_capability}:{capability}')

    resolution = resolve_action_tooling(action_spec, requested_profiles=requested_profiles, allow_lab=allow_lab)
    target = _extract_target(action_spec)
    target_host = extract_host_from_url(target) or target
    selected_tool = _normalize_text(resolution.get('selected_tool'))
    steps = recipe.get('steps') if isinstance(recipe.get('steps'), list) else []
    plan: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        tool = _normalize_text(step.get('tool') or selected_tool)
        if not tool:
            raise ValueError(f'recipe_missing_tool:{recipe_key}:{idx}')
        args = [
            _render_recipe_arg(arg, target=target, target_host=target_host, selected_tool=selected_tool, capability=capability)
            for arg in (step.get('args') or [])
        ]
        plan.append({
            'tool': tool,
            'role': _normalize_text(step.get('role') or 'probe') or 'probe',
            'args': args,
        })
    return plan


def _ordered_visible_profiles() -> List[str]:
    profiles = get_profile_catalog()
    return [name for name, meta in profiles.items() if bool(meta.get('planner_visible', False))]


def suggest_capabilities_for_task_family(task_family: str) -> List[str]:
    family = _normalize_text(task_family)
    recipe = get_task_family_recipe_catalog().get(family) or {}
    primary = [_normalize_text(x) for x in (recipe.get('primary_capabilities') or []) if _normalize_text(x)]
    if primary:
        return primary
    return [_normalize_text(x) for x in (get_task_family_catalog().get(family) or []) if _normalize_text(x)]


def resolve_contextual_planner_profiles(
    task_family: str = '',
    requested_profiles: Iterable[str] | str | None = None,
    *,
    allow_lab: bool | None = None,
    require_full_family_coverage: bool = True,
) -> Dict[str, Any]:
    base_profiles = list(resolve_planner_profiles(requested_profiles))
    profiles = list(base_profiles)
    defaults = get_recipe_defaults()
    allow_lab_auto = bool(defaults.get('allow_lab_auto_expand', False)) if allow_lab is None else bool(allow_lab)
    max_profile = _normalize_text(defaults.get('auto_expand_max_profile') or 'specialized')
    ordered = _ordered_visible_profiles()
    if not ordered:
        return {
            'profiles': base_profiles,
            'base_profiles': base_profiles,
            'coverage_complete': True,
            'coverage_gaps': [],
            'auto_expanded': False,
        }
    if max_profile not in ordered:
        max_profile = 'lab' if allow_lab_auto and 'lab' in ordered else ordered[-1]
    max_index = ordered.index(max_profile)
    allowed_growth = set(ordered[: max_index + 1])
    if allow_lab_auto and 'lab' in ordered:
        allowed_growth.add('lab')

    family = _normalize_text(task_family)
    family_recipe = get_task_family_recipe_catalog().get(family) or {}
    for profile in [_normalize_text(x) for x in (family_recipe.get('profile_expansion') or []) if _normalize_text(x)]:
        if profile == 'lab' and not allow_lab_auto:
            continue
        if profile in allowed_growth and profile not in profiles:
            profiles.append(profile)

    caps = suggest_capabilities_for_task_family(family)

    def _coverage_gaps(active_profiles: List[str]) -> List[str]:
        coverage = get_capability_tool_coverage(active_profiles)
        return [cap for cap in caps if not coverage.get(cap)]

    gaps = _coverage_gaps(profiles)
    if require_full_family_coverage and gaps:
        for profile in ordered:
            if profile in profiles:
                continue
            if profile == 'lab' and not allow_lab_auto:
                continue
            if profile not in allowed_growth:
                continue
            profiles.append(profile)
            gaps = _coverage_gaps(profiles)
            if not gaps:
                break

    return {
        'profiles': profiles,
        'base_profiles': base_profiles,
        'coverage_complete': not bool(gaps),
        'coverage_gaps': gaps,
        'auto_expanded': profiles != base_profiles,
    }


def list_candidate_tools_for_capability(
    capability: str,
    *,
    action_type: str = '',
    task_family: str = '',
    requested_profiles: Iterable[str] | str | None = None,
    allow_lab: bool | None = None,
    preferred_tool: str = '',
    tool_candidates: Iterable[Any] | None = None,
) -> List[str]:
    cap = _normalize_text(capability)
    action = _normalize_text(action_type)
    context = resolve_contextual_planner_profiles(task_family, requested_profiles, allow_lab=allow_lab)
    allowed = set(get_planner_visible_tools(context.get('profiles') or None))
    if not cap:
        return []
    recipe = get_capability_recipe_catalog().get(cap) or {}
    action_tools = recipe.get('action_type_tools') if isinstance(recipe.get('action_type_tools'), dict) else {}
    ordered: List[str] = []

    def _add(tool: Any) -> None:
        name = _normalize_text(tool)
        if name and name in allowed and name not in ordered:
            ordered.append(name)

    _add(preferred_tool)
    for item in (tool_candidates or []):
        _add(item)
    for item in (action_tools.get(action) or []):
        _add(item)
    for item in (recipe.get('tools') or []):
        _add(item)
    for item in (get_capability_tool_coverage(context.get('profiles') or None).get(cap) or []):
        _add(item)
    return ordered


def get_preferred_tools_for_task_family(
    task_family: str,
    *,
    objective: str = '',
    recent_context: List[Dict[str, Any]] | None = None,
    requested_profiles: Iterable[str] | str | None = None,
    allow_lab: bool | None = None,
    limit: int = 6,
) -> List[str]:
    recent_blob = ''
    if isinstance(recent_context, list) and recent_context:
        try:
            import json
            recent_blob = json.dumps(recent_context[-5:], ensure_ascii=False).lower()
        except Exception:
            recent_blob = ''
    objective_l = _normalize_text(objective)
    capabilities = suggest_capabilities_for_task_family(task_family)
    if 'parameter' in recent_blob or 'query' in recent_blob or 'form' in recent_blob or 'input' in recent_blob:
        if 'parameter_mining' in capabilities:
            capabilities = ['parameter_mining'] + [c for c in capabilities if c != 'parameter_mining']
    if 'javascript' in recent_blob or 'route' in recent_blob or 'endpoint' in recent_blob:
        if 'crawler_route_discovery' in capabilities:
            capabilities = ['crawler_route_discovery'] + [c for c in capabilities if c != 'crawler_route_discovery']
    if any(tok in objective_l for tok in ['tls', 'ssl', 'cipher', 'certificate', 'https']):
        for cap in ['transport_tls_handshake', 'tls_posture_check']:
            if cap in capabilities:
                capabilities = [cap] + [c for c in capabilities if c != cap]
    ordered: List[str] = []
    for cap in capabilities:
        for tool in list_candidate_tools_for_capability(
            cap,
            action_type='',
            task_family=task_family,
            requested_profiles=requested_profiles,
            allow_lab=allow_lab,
        ):
            if tool not in ordered:
                ordered.append(tool)
    return ordered[: max(1, int(limit))]


def resolve_action_tooling(
    action_spec: Dict[str, Any],
    *,
    requested_profiles: Iterable[str] | str | None = None,
    allow_lab: bool | None = None,
) -> Dict[str, Any]:
    spec = dict(action_spec or {})
    action_type = _normalize_text(spec.get('action_type') or DEFAULT_ACTION_TYPE)
    capability = _normalize_text(spec.get('capability') or ACTION_TYPE_TO_CAPABILITY.get(action_type) or DEFAULT_CAPABILITY)
    task_family = _normalize_text(spec.get('task_family') or spec.get('intent_class') or '')
    tool_preferences = spec.get('tool_preferences') if isinstance(spec.get('tool_preferences'), dict) else {}
    preferred_tool = _normalize_text(tool_preferences.get('prefer_tool'))
    explicit_tool = _normalize_text(spec.get('tool'))
    explicit_candidates = spec.get('tool_candidates') if isinstance(spec.get('tool_candidates'), list) else []
    context = resolve_contextual_planner_profiles(task_family, requested_profiles or spec.get('resolved_planner_profiles'), allow_lab=allow_lab)
    candidates = list_candidate_tools_for_capability(
        capability,
        action_type=action_type,
        task_family=task_family,
        requested_profiles=context.get('profiles') or None,
        allow_lab=allow_lab,
        preferred_tool=preferred_tool,
        tool_candidates=explicit_candidates,
    )
    allowed = set(get_planner_visible_tools(context.get('profiles') or None))
    selected_tool = ''
    source = 'unresolved'
    if explicit_tool and explicit_tool in allowed:
        selected_tool = explicit_tool
        source = 'explicit_tool'
    elif preferred_tool and preferred_tool in candidates:
        selected_tool = preferred_tool
        source = 'preferred_tool'
    elif candidates:
        selected_tool = candidates[0]
        source = 'capability_recipe'
    return {
        'capability': capability,
        'task_family': task_family,
        'profiles': list(context.get('profiles') or []),
        'base_profiles': list(context.get('base_profiles') or []),
        'coverage_complete': bool(context.get('coverage_complete', True)),
        'coverage_gaps': list(context.get('coverage_gaps') or []),
        'candidate_tools': candidates,
        'selected_tool': selected_tool,
        'resolution_source': source,
    }


def can_resolve_tool_from_capability(
    capability: str,
    *,
    action_type: str = '',
    task_family: str = '',
    requested_profiles: Iterable[str] | str | None = None,
    allow_lab: bool | None = None,
    preferred_tool: str = '',
    tool_candidates: Iterable[Any] | None = None,
) -> bool:
    return bool(
        list_candidate_tools_for_capability(
            capability,
            action_type=action_type,
            task_family=task_family,
            requested_profiles=requested_profiles,
            allow_lab=allow_lab,
            preferred_tool=preferred_tool,
            tool_candidates=tool_candidates,
        )
    )
