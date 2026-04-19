from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from action_schema import ACTION_TYPE_TO_CAPABILITY, ACTION_TYPE_TO_EXPERIMENT_SHAPE, ALLOWED_EXPERIMENT_SHAPES  # type: ignore
from capability_recipes import (  # type: ignore
    can_resolve_tool_from_capability,
    get_preferred_tools_for_task_family as recipe_preferred_tools,
    list_candidate_tools_for_capability,
)
from campaign_utils import extract_host_from_url  # type: ignore
from policy_core import get_runtime_allowed_tools, get_runtime_brain_allowed_tools  # type: ignore
from tool_registry import get_capability_catalog  # type: ignore



def _ordered_intent_capabilities(capability_candidates: List[str] | None = None, recommended_action_types: List[str] | None = None) -> List[str]:
    ordered: List[str] = []

    def _add(cap: Any) -> None:
        name = str(cap or '').strip().lower()
        if name and name not in ordered:
            ordered.append(name)

    for item in (capability_candidates or []):
        _add(item)
    for action_type in (recommended_action_types or []):
        _add(ACTION_TYPE_TO_CAPABILITY.get(str(action_type or '').strip().lower(), ''))
    return ordered


def fallback_brain_action(
    objective: str,
    target: str,
    aggression: int,
    *,
    task_family: str = '',
    recent_context: List[Dict[str, Any]] | None = None,
    intent_context: Dict[str, Any] | None = None,
    contextual_brain_tooling_fn: Callable[..., dict],
) -> Dict[str, Any]:
    obj = str(objective or '').lower()
    fam = str(task_family or '').lower()
    t = str(target or '').strip()
    recent = (recent_context or [])[-5:]
    recent_blob = json.dumps(recent, ensure_ascii=False).lower()
    host = extract_host_from_url(t) or t
    intent_ctx = intent_context if isinstance(intent_context, dict) else {}
    intent_capabilities = [str(x).strip().lower() for x in (intent_ctx.get('capability_candidates') or []) if str(x).strip()]
    intent_action_types = [str(x).strip().lower() for x in (intent_ctx.get('recommended_action_types') or []) if str(x).strip()]
    effective_intent_capabilities = _ordered_intent_capabilities(intent_capabilities, intent_action_types)
    live_brain_tools = set(contextual_brain_tooling_fn(task_family).get('tools') or [])

    def _mk(tool: str, args: List[str], intent: str, aggr_cap: int = 3, action_type: str = 'single_probe', probe_recipe: Dict[str, Any] | None = None, capability: str = '') -> Dict[str, Any]:
        chosen_action = str(action_type or (intent_action_types[0] if intent_action_types else 'single_probe')).strip().lower() or 'single_probe'
        chosen_capability = str(capability or (effective_intent_capabilities[0] if effective_intent_capabilities else '')).strip().lower()
        return {
            'intent': intent,
            'target': t,
            'tool': tool,
            'args': args,
            'action_type': chosen_action,
            'capability': chosen_capability,
            'probe_recipe': probe_recipe or {},
            'constraints': {'aggression': max(1, min(aggression, aggr_cap))},
            'planner_alignment': 'aligned',
        }

    def _capability_first_fallback() -> Dict[str, Any] | None:
        action_type = intent_action_types[0] if intent_action_types else 'single_probe'
        for cap in effective_intent_capabilities:
            candidates = [
                tool for tool in list_candidate_tools_for_capability(cap, action_type=action_type, task_family=task_family)
                if tool in live_brain_tools
            ]
            if not candidates:
                continue
            tool = candidates[0]
            if cap == 'tls_posture_check':
                if tool == 'httpx-pd':
                    return _mk(tool, ['-silent', '-tls-probe', '-status-code', '-title', '-u', t], 'capability_tls_posture_fallback', aggr_cap=2, action_type='fingerprint_probe', capability=cap)
                if tool == 'testssl.sh':
                    return _mk(tool, ['--warnings', 'off', '--openssl', 'openssl', host], 'capability_tls_posture_fallback', aggr_cap=2, action_type='fingerprint_probe', capability=cap)
                return _mk('curl', ['-sS', '-I', '-k', '--max-time', '15', t], 'capability_tls_posture_fallback', aggr_cap=2, action_type='fingerprint_probe', capability=cap)
            if cap == 'content_discovery':
                if tool == 'katana':
                    return _mk(tool, ['-u', t, '-jc', '-kf', '-silent'], 'capability_content_discovery_fallback', aggr_cap=2, action_type='enumeration_probe', capability=cap)
                if tool == 'ffuf':
                    return _mk(tool, ['-u', f"{t.rstrip('/')}/FUZZ", '-mc', 'all'], 'capability_content_discovery_fallback', aggr_cap=2, action_type='enumeration_probe', capability=cap)
                if tool in {'feroxbuster', 'gobuster', 'dirsearch'}:
                    return _mk(tool, ['-u', t], 'capability_content_discovery_fallback', aggr_cap=2, action_type='enumeration_probe', capability=cap)
            if cap == 'http_probe':
                if tool == 'httpx':
                    return _mk(tool, ['-silent', '-title', '-tech-detect', '-status-code', '-follow-redirects', '-u', t], 'capability_http_probe_fallback', aggr_cap=2, action_type=action_type, capability=cap)
                return _mk(tool, ['-s', '-X', 'GET', t], 'capability_http_probe_fallback', aggr_cap=2, action_type=action_type, capability=cap)
            return _mk(tool, [t], 'capability_first_fallback', aggr_cap=2, action_type=action_type, capability=cap)
        return None

    capability_first = _capability_first_fallback()
    if capability_first is not None:
        return capability_first

    if any(k in fam for k in ['subdomain_expansion', 'dns']) or any(k in obj for k in ['dns', 'subdomain', 'domain', 'mx', 'txt']):
        if any(k in recent_blob for k in ['subdomain', 'subs', 'enumeration']) and 'assetfinder' in live_brain_tools:
            return _mk('assetfinder', ['--subs-only', host], 'assetfinder_dns_fallback', aggr_cap=2)
        if 'subfinder' in live_brain_tools and any(k in recent_blob for k in ['passive', 'enumeration', 'asset']):
            return _mk('subfinder', ['-silent', '-d', host], 'subfinder_dns_fallback', aggr_cap=2, action_type='enumeration_probe')
        return _mk('dig' if 'dig' in live_brain_tools else 'nslookup', ['+short', host], 'dns_fallback', action_type='enumeration_probe')

    if any(k in fam for k in ['tls_assessment']) or any(k in obj for k in ['tls', 'ssl', 'cipher', 'certificate', 'hsts']):
        if 'httpx-pd' in live_brain_tools:
            return _mk('httpx-pd', ['-silent', '-tls-probe', '-status-code', '-title', '-u', t], 'tls_httpxpd_fallback', aggr_cap=2, action_type='fingerprint_probe')
        if 'testssl.sh' in live_brain_tools:
            return _mk('testssl.sh', ['--warnings', 'off', '--openssl', 'openssl', host], 'tls_fallback', aggr_cap=2, action_type='fingerprint_probe')
        return _mk('curl', ['-sS', '-I', '-k', '--max-time', '15', t], 'tls_header_fallback', aggr_cap=2, action_type='fingerprint_probe')

    if any(k in fam for k in ['historical_url_mining']):
        if 'gau' in live_brain_tools:
            return _mk('gau', ['--subs', host], 'historical_url_fallback', aggr_cap=2, action_type='enumeration_probe')
        return _mk('katana', ['-u', t, '-known-files', 'all', '-silent'], 'historical_katana_fallback', aggr_cap=2, action_type='enumeration_probe')

    if any(k in fam for k in ['content_discovery']):
        if 'katana' in live_brain_tools:
            return _mk('katana', ['-u', t, '-jc', '-kf', '-silent'], 'content_discovery_katana_fallback', aggr_cap=2, action_type='enumeration_probe')
        if 'gau' in live_brain_tools:
            return _mk('gau', ['--subs', host], 'content_discovery_gau_fallback', aggr_cap=2)
        if 'ffuf' in live_brain_tools:
            return _mk('ffuf', ['-u', f"{t.rstrip('/')}/FUZZ", '-mc', 'all'], 'ffuf_content_fallback', aggr_cap=2, action_type='enumeration_probe')
        if 'feroxbuster' in live_brain_tools:
            return _mk('feroxbuster', ['-u', t, '-k', '-q', '-d', '1'], 'content_discovery_fallback', aggr_cap=2)

    if any(k in fam for k in ['secret_hunt']):
        if 'katana' in live_brain_tools:
            return _mk('katana', ['-u', t, '-jc', '-kf', '-silent'], 'secret_hunt_katana_fallback', aggr_cap=2)
        return _mk('gau', ['--subs', host], 'secret_hunt_historical_fallback', aggr_cap=2)

    if any(k in fam for k in ['recon']) or any(k in obj for k in ['recon', 'discovery', 'endpoint']):
        if any(k in recent_blob for k in ['directory', 'path brute', 'content discovery', 'wordlist']) and 'feroxbuster' in live_brain_tools:
            return _mk('feroxbuster', ['-u', t, '-k', '-q', '-d', '1'], 'feroxbuster_recon_fallback', aggr_cap=2)
        if any(k in recent_blob for k in ['javascript', 'script', 'route', 'bundle']) and 'katana' in live_brain_tools:
            return _mk('katana', ['-u', t, '-jc', '-kf', '-silent'], 'katana_recon_fallback')
        if any(k in recent_blob for k in ['crawl', 'crawl-depth', 'spider']) and 'hakrawler' in live_brain_tools:
            return _mk('hakrawler', ['-url', t, '-depth', '2', '-plain'], 'hakrawler_recon_fallback', aggr_cap=2)
        if any(k in recent_blob for k in ['wayback', 'archive', 'historical', 'legacy']) and 'gau' in live_brain_tools:
            return _mk('gau', ['--subs', host], 'historical_url_fallback')
        if any(k in recent_blob for k in ['robots.txt', 'sitemap.xml', 'security.txt']) and 'httpx' in live_brain_tools:
            return _mk('httpx', ['-silent', '-title', '-tech-detect', '-status-code', '-follow-redirects', '-u', t], 'fingerprint_fallback')
        return _mk('curl', ['-s', '-X', 'GET', f"{t.rstrip('/')}/robots.txt", f"{t.rstrip('/')}/.well-known/security.txt", f"{t.rstrip('/')}/sitemap.xml"], 'safe_recon_fallback')

    if any(k in fam for k in ['auth', 'authz', 'logic']) or any(k in obj for k in ['auth', 'authz', 'token', 'csrf', 'input', 'redirect']):
        if any(k in recent_blob for k in ['parameter', 'query', 'input', 'missing param']) and 'arjun' in live_brain_tools:
            return _mk('arjun', ['-u', t, '-m', 'GET', '--stable'], 'parameter_mining_fallback', aggr_cap=2)
        path = '/api/v1/user/profile'
        if any(k in recent_blob for k in ['403', '401', 'unauthorized', 'forbidden']):
            path = '/account' if '/account' not in t else '/profile'
        return _mk('curl', ['-s', '-X', 'GET', f"{t.rstrip('/')}{path}"], 'boundary_probe_fallback')

    if any(k in fam for k in ['client_input', 'input_tamper', 'redirect_trust']):
        if 'arjun' in live_brain_tools and any(k in recent_blob for k in ['form', 'input', 'parameter', 'query']):
            return _mk('arjun', ['-u', t, '-m', 'GET', '--stable'], 'input_param_fallback', aggr_cap=2)
        return _mk('curl', ['-s', '-X', 'GET', f"{t.rstrip('/')}?next=%2Fdashboard&probe=rc_canary"], 'input_probe_fallback')

    if any(k in recent_blob for k in ['directory', 'path brute', 'content discovery']) and 'feroxbuster' in live_brain_tools:
        return _mk('feroxbuster', ['-u', t, '-k', '-q', '-d', '1'], 'generic_ferox_fallback', aggr_cap=2)
    if any(k in recent_blob for k in ['javascript', 'route', 'endpoint']) and 'katana' in live_brain_tools:
        return _mk('katana', ['-u', t, '-jc', '-silent'], 'generic_katana_fallback')
    if any(k in recent_blob for k in ['crawl', 'spider']) and 'hakrawler' in live_brain_tools:
        return _mk('hakrawler', ['-url', t, '-depth', '2', '-plain'], 'generic_hakrawler_fallback', aggr_cap=2)
    if any(k in recent_blob for k in ['historical', 'archive', 'legacy']) and 'gau' in live_brain_tools:
        return _mk('gau', ['--subs', host], 'generic_historical_fallback')
    return _mk('curl', ['-s', '-X', 'GET', t], 'safe_probe_fallback')



def preferred_tools_for_task_family(
    task_family: str,
    objective: str,
    *,
    recent_context: List[Dict[str, Any]] | None = None,
    capability_candidates: List[str] | None = None,
    recommended_action_types: List[str] | None = None,
    contextual_brain_tooling_fn: Callable[..., dict],
) -> List[str]:
    tooling = contextual_brain_tooling_fn(task_family)
    ordered: List[str] = []
    effective_capabilities = _ordered_intent_capabilities(capability_candidates, recommended_action_types)
    preferred_action_type = str((recommended_action_types or [''])[0] or '').strip().lower()
    for cap in effective_capabilities:
        for tool in list_candidate_tools_for_capability(
            cap,
            action_type=preferred_action_type,
            task_family=task_family,
            requested_profiles=tooling.get('profiles') or None,
        ):
            if tool not in ordered:
                ordered.append(tool)
    preferred = recipe_preferred_tools(
        task_family,
        objective=objective,
        recent_context=recent_context,
        requested_profiles=tooling.get('profiles') or None,
        limit=6,
    )
    for tool in preferred:
        if tool not in ordered:
            ordered.append(tool)
    if ordered:
        return ordered[:6]
    return list(tooling.get('tools') or list(get_runtime_brain_allowed_tools(tooling.get('profiles') or None)))[:6]



def apply_intent_guidance_to_brain(
    brain: Dict[str, Any],
    intent_context: Dict[str, Any],
    *,
    objective: str,
    target: str,
    aggression: int,
    task_family: str = '',
    recent_context: List[Dict[str, Any]] | None = None,
    preferred_tools_for_task_family_fn: Callable[..., List[str]],
) -> Dict[str, Any]:
    out = dict(brain or {}) if isinstance(brain, dict) else {}
    if not isinstance(intent_context, dict):
        return out
    capability_candidates = [str(x).strip().lower() for x in (intent_context.get('capability_candidates') or []) if str(x).strip()]
    recommended_action_types = [str(x).strip().lower() for x in (intent_context.get('recommended_action_types') or []) if str(x).strip()]
    hypothesis_candidates = [str(x).strip() for x in (intent_context.get('hypothesis_candidates') or []) if str(x).strip()]
    valid_capabilities = {str(x).strip().lower() for x in get_capability_catalog() if str(x).strip()}
    if not str(out.get('action_type') or '').strip() and recommended_action_types:
        out['action_type'] = recommended_action_types[0]
    current_capability = str(out.get('capability') or '').strip().lower()
    if capability_candidates and (not current_capability or current_capability not in valid_capabilities):
        out['capability'] = capability_candidates[0]
    current_experiment_shape = str(out.get('experiment_shape') or '').strip().lower()
    canonical_experiment_shape = ACTION_TYPE_TO_EXPERIMENT_SHAPE.get(str(out.get('action_type') or '').strip().lower(), 'single_step')
    if not current_experiment_shape or current_experiment_shape not in ALLOWED_EXPERIMENT_SHAPES:
        out['experiment_shape'] = canonical_experiment_shape
    if not str(out.get('hypothesis') or '').strip() and hypothesis_candidates:
        out['hypothesis'] = hypothesis_candidates[0]
    tool_preferences = dict(out.get('tool_preferences') or {}) if isinstance(out.get('tool_preferences'), dict) else {}
    if not tool_preferences.get('prefer_tool'):
        preferred_tools = preferred_tools_for_task_family_fn(
            task_family,
            objective,
            recent_context=recent_context,
            capability_candidates=capability_candidates,
            recommended_action_types=recommended_action_types,
        )
        if preferred_tools:
            tool_preferences['prefer_tool'] = preferred_tools[0]
    if tool_preferences:
        out['tool_preferences'] = tool_preferences
    if not str(out.get('planner_alignment') or '').strip():
        out['planner_alignment'] = 'aligned'
    if intent_context.get('experiment_intent_id') and not out.get('experiment_intent_id'):
        out['experiment_intent_id'] = str(intent_context.get('experiment_intent_id') or '')
    if intent_context.get('planner_constraints') and not out.get('planner_constraints'):
        out['planner_constraints'] = dict(intent_context.get('planner_constraints') or {})
    if intent_context.get('planner_preferences') and not out.get('planner_preferences'):
        out['planner_preferences'] = dict(intent_context.get('planner_preferences') or {})
    if capability_candidates and not out.get('capability_candidates'):
        out['capability_candidates'] = capability_candidates
    if recommended_action_types and not out.get('recommended_action_types'):
        out['recommended_action_types'] = recommended_action_types
    if hypothesis_candidates and not out.get('hypothesis_candidates'):
        out['hypothesis_candidates'] = hypothesis_candidates
    return out



def enforce_brain_tool_whitelist(
    brain: Dict[str, Any],
    objective: str,
    target: str,
    aggression: int,
    *,
    task_family: str = '',
    recent_context: List[Dict[str, Any]] | None = None,
    execution_mode: str = 'normalized',
    contextual_brain_tooling_fn: Callable[..., dict],
    fallback_brain_action_fn: Callable[..., Dict[str, Any]],
) -> tuple[Dict[str, Any], Dict[str, Any] | None]:
    tool = str((brain or {}).get('tool') or '').strip().lower()
    fam = str(task_family or '').strip().lower()
    tooling = contextual_brain_tooling_fn(fam, list((brain or {}).get('resolved_planner_profiles') or []))
    allowed_tools = set(tooling.get('tools') or list(get_runtime_brain_allowed_tools(tooling.get('profiles') or None)))

    if execution_mode != 'faithful' and fam == 'tls_assessment' and tool == 'testssl.sh' and 'httpx-pd' in allowed_tools:
        fb = dict(brain or {})
        fb['tool'] = 'httpx-pd'
        fb['intent'] = str(fb.get('intent') or 'tls_httpxpd_normalized')
        fb['args'] = ['-silent', '-tls-probe', '-status-code', '-title', '-u', target]
        return fb, {'original_tool': tool, 'normalized_tool': 'httpx-pd', 'reason': 'tls_first_pass_httpxpd_enforced', 'confidence': 'high'}
    if execution_mode != 'faithful' and fam == 'content_discovery' and tool == 'feroxbuster' and 'katana' in allowed_tools:
        fb = dict(brain or {})
        fb['tool'] = 'katana'
        fb['intent'] = str(fb.get('intent') or 'content_discovery_katana_normalized')
        fb['args'] = ['-u', target, '-jc', '-kf', '-silent']
        return fb, {'original_tool': tool, 'normalized_tool': 'katana', 'reason': 'content_discovery_first_pass_katana_enforced', 'confidence': 'high'}

    if tool in allowed_tools:
        return brain, None

    capability = str((brain or {}).get('capability') or '').strip().lower()
    if not tool and can_resolve_tool_from_capability(
        capability,
        action_type=str((brain or {}).get('action_type') or '').strip().lower(),
        task_family=fam,
        requested_profiles=list((brain or {}).get('resolved_planner_profiles') or []),
        preferred_tool=str((((brain or {}).get('tool_preferences') or {}) if isinstance((brain or {}).get('tool_preferences'), dict) else {}).get('prefer_tool') or '').strip().lower(),
        tool_candidates=list((brain or {}).get('tool_candidates') or []),
    ):
        return brain, None

    if tool in {'exec', 'execute', 'shell', 'command', 'cmd'}:
        fb = fallback_brain_action_fn(objective, target, aggression, task_family=task_family, recent_context=recent_context)
        fb['intent'] = f'normalized_from_{tool}'
        return fb, {'original_tool': tool, 'normalized_tool': str(fb.get('tool') or ''), 'reason': 'pseudo_tool_alias', 'confidence': 'medium'}

    fb = fallback_brain_action_fn(objective, target, aggression, task_family=task_family, recent_context=recent_context)
    reason = 'tool_not_whitelisted'
    confidence = 'low'
    if tool in get_runtime_allowed_tools():
        reason = 'tool_not_allowed_for_brain'
        confidence = 'high'
    return fb, {'original_tool': tool or 'unknown', 'normalized_tool': str(fb.get('tool') or ''), 'reason': reason, 'confidence': confidence}
