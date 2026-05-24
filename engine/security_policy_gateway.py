from __future__ import annotations

"""Ravenclaw-owned security policy gateway over local security helpers.

Scope loading and the allow/deny decision belong to the security runtime. The
action/tool helper functions are kept behind the same compatibility import seam
for callers, but their active implementation is Ravenclaw-owned.
"""

import re
from typing import Any, Dict, List

from campaign_utils import host_in_scope, load_scope_domains  # type: ignore
from govengine.scope_ports import extract_host_from_url


HOST_TOKEN_RE = re.compile(r"(https?://[^\s\"'<>]+)|\b((?:[a-z0-9-]+\.)+[a-z]{2,})\b", re.IGNORECASE)


def _compat_helper(name: str) -> Any:
    import govengine_security_helpers as helpers  # type: ignore

    return getattr(helpers, name)


def validate_probe_recipe(value: Dict[str, Any]) -> List[str]:
    return _compat_helper('validate_probe_recipe')(value)


def validate_action_contract_v2(value: Dict[str, Any]) -> List[str]:
    return _compat_helper('validate_action_contract_v2')(value)


def compile_action_spec(value: Dict[str, Any]) -> Dict[str, Any]:
    return _compat_helper('compile_action_spec')(value)


def get_runtime_allowed_tools() -> set[str]:
    return _compat_helper('get_runtime_allowed_tools')()


def get_tool_catalog() -> Dict[str, Dict[str, Any]]:
    return _compat_helper('get_tool_catalog')()


def normalize_tool(value: Any) -> str:
    return _compat_helper('normalize_tool')(value)


def contains_banned_patterns(args: List[Any]) -> tuple[bool, str]:
    return _compat_helper('contains_banned_patterns')(args)


def contains_tool_restricted_patterns(tool: Any, args: List[Any]) -> tuple[bool, str]:
    return _compat_helper('contains_tool_restricted_patterns')(tool, args)


def check_credentials_policy(args: List[Any], creds: Dict[str, Any], owner_approved_auth: bool, tool: str) -> tuple[bool, str]:
    return _compat_helper('check_credentials_policy')(args, creds, owner_approved_auth, tool)


def _compiled_chain_steps(compiled: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = compiled.get('execution_plan', []) if isinstance(compiled.get('execution_plan'), list) else []
    return [step for step in steps if isinstance(step, dict)]


def _arg_target_observations(args: List[Any], stdin_text: Any = '') -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {'urls': [], 'hosts': [], 'files': []}
    seen: Dict[str, set[str]] = {'urls': set(), 'hosts': set(), 'files': set()}

    def _observe(raw_value: Any) -> None:
        raw = str(raw_value or '').strip()
        if not raw or raw.startswith('-'):
            return
        lowered = raw.lower()
        if lowered.startswith(('http://', 'https://')):
            if lowered not in seen['urls']:
                seen['urls'].add(lowered)
                out['urls'].append(raw)
            return
        if lowered.startswith('file://'):
            if lowered not in seen['files']:
                seen['files'].add(lowered)
                out['files'].append(raw)
            return
        if any(ch.isspace() for ch in raw) or '/' in raw or '\\' in raw:
            return
        host = str(extract_host_from_url(raw) or raw).strip().lower()
        if not host or '.' not in host:
            return
        if host not in seen['hosts']:
            seen['hosts'].add(host)
            out['hosts'].append(host)

    for token in list(args or []):
        _observe(token)
    for line in str(stdin_text or '').splitlines():
        _observe(line)
    return out


def _extract_hosts_from_text(text: Any) -> List[str]:
    raw = str(text or '').strip()
    if not raw:
        return []
    raw_lower = raw.lower()
    if raw_lower.startswith('file://'):
        return []
    hosts: List[str] = []
    seen: set[str] = set()
    direct = str(extract_host_from_url(raw) or '').strip().lower()
    if direct:
        seen.add(direct)
        hosts.append(direct)
    allow_bare_domain_match = ('/' not in raw and '\\' not in raw) or 'host:' in raw_lower
    for match in HOST_TOKEN_RE.finditer(raw):
        if match.group(1):
            token = str(match.group(1) or '').strip().lower()
        else:
            if not allow_bare_domain_match:
                continue
            token = str(match.group(2) or '').strip().lower()
        host = str(extract_host_from_url(token) or token).strip().lower()
        if host and host not in seen:
            seen.add(host)
            hosts.append(host)
    return hosts


def _check_target_semantics(tool: str, args: List[Any], catalog: Dict[str, Dict[str, Any]], stdin_text: Any = '') -> str:
    tool_norm = normalize_tool(tool)
    info = catalog.get(tool_norm) or {}
    target_validation_mode = str(info.get('target_validation_mode') or 'none').strip().lower() or 'none'
    observed = _arg_target_observations(args, stdin_text=stdin_text)

    if target_validation_mode == 'strict_url':
        if observed['files'] and not observed['urls']:
            return ''
        if not observed['urls']:
            return f'missing_target_kind:{tool_norm}:url'
        return ''

    if target_validation_mode == 'strict_host_domain':
        if observed['urls']:
            return f'invalid_target_kind:{tool_norm}:url'
        if not observed['hosts']:
            return f'missing_target_kind:{tool_norm}:host_or_domain'

    return ''


def _check_scope_semantics(args: List[Any], scope_domains: Any, stdin_text: Any = '') -> str:
    for token in [*(args or []), *str(stdin_text or '').splitlines()]:
        for host in _extract_hosts_from_text(token):
            if not host_in_scope(host, scope_domains):
                return f'out_of_scope_target:{host}'
    return ''


def normalize_policy_decision_v0(
    legacy_decision: Dict[str, Any] | None,
    *,
    target: str = '',
    target_host: str = '',
    target_in_scope: bool | None = None,
    resolved_tool: str = '',
    action_type: str = '',
    approval_required: bool = False,
    constraints: Dict[str, Any] | None = None,
    redaction_required: bool = True,
) -> Dict[str, Any]:
    """Return the current host policy-decision shape for legacy callers."""

    legacy = legacy_decision or {}
    legacy_pass = bool(legacy.get('pass', False))
    reason = str(legacy.get('reason') or '').strip() or ('ok' if legacy_pass else 'unspecified')
    owner_gate = approval_required or reason.startswith('action_type_requires_owner_gate')
    if legacy_pass:
        decision = 'allow_prepare'
    elif owner_gate:
        decision = 'owner_approval_required'
    else:
        decision = 'deny'
    return {
        'schema_version': '2026-04-27.policy-decision.v0.1',
        'decision': decision,
        'reason_code': reason,
        'reasons': [reason] if reason else [],
        'scope_facts': {
            'target': str(target or ''),
            'target_host': str(target_host or ''),
            'target_in_scope': bool(target_in_scope) if target_in_scope is not None else legacy_pass,
        },
        'tool_facts': {
            'resolved_tool': str(resolved_tool or ''),
            'action_type': str(action_type or ''),
        },
        'approval_required': bool(owner_gate),
        'constraints': dict(constraints or {}),
        'redaction_required': bool(redaction_required),
        'compatibility': {
            'pass': legacy_pass,
            'reason': reason,
        },
    }


def evaluate_action_spec(brain: Dict[str, Any], target: str, owner_approved_auth: bool, creds: Dict[str, Any] | None = None) -> Dict[str, Any]:
    action_type = str(brain.get('action_type') or _compat_helper('DEFAULT_ACTION_TYPE')).strip().lower()
    recipe_errors = validate_probe_recipe(brain)
    if recipe_errors:
        return {'pass': False, 'reason': 'invalid_probe_recipe:' + ','.join(recipe_errors)}

    contract_v2_errors = validate_action_contract_v2(brain)
    if contract_v2_errors:
        return {'pass': False, 'reason': 'invalid_action_contract_v2:' + ','.join(contract_v2_errors)}

    if action_type in {'variant_probe', 'state_transition_probe'} and not owner_approved_auth:
        return {'pass': False, 'reason': f'action_type_requires_owner_gate:{action_type}'}

    try:
        compiled = compile_action_spec(brain)
    except Exception as exc:
        reason = str(exc or 'compile_failed').strip() or 'compile_failed'
        return {'pass': False, 'reason': reason}

    allowed_tools = get_runtime_allowed_tools()
    tool_catalog = get_tool_catalog()
    tool = normalize_tool(compiled.get('tool'))
    args = compiled.get('args', []) or []
    if not tool:
        return {'pass': False, 'reason': 'missing_tool'}
    if tool not in allowed_tools:
        return {'pass': False, 'reason': f'tool_not_allowed:{tool}'}

    host = extract_host_from_url(target)
    scope_domains = load_scope_domains()
    if not host or not host_in_scope(host, scope_domains):
        return {'pass': False, 'reason': f'out_of_scope_target:{host or target}'}

    banned, pattern = contains_banned_patterns(args)
    if banned:
        return {'pass': False, 'reason': f'disallowed_pattern:{pattern}'}
    restricted, restricted_pattern = contains_tool_restricted_patterns(tool, args)
    if restricted:
        return {'pass': False, 'reason': f'tool_restricted_pattern:{tool}:{restricted_pattern}'}
    target_reason = _check_target_semantics(tool, args, tool_catalog, stdin_text=compiled.get('stdin') or '')
    if target_reason:
        return {'pass': False, 'reason': target_reason}
    scope_reason = _check_scope_semantics(args, scope_domains, stdin_text=compiled.get('stdin') or '')
    if scope_reason:
        return {'pass': False, 'reason': scope_reason}

    creds = creds or {}
    creds_ok, creds_reason = check_credentials_policy(args, creds, owner_approved_auth, tool)
    if not creds_ok:
        return {'pass': False, 'reason': creds_reason}

    for idx, step in enumerate(_compiled_chain_steps(compiled)):
        step_tool = normalize_tool(step.get('tool'))
        step_args = step.get('args', []) or []
        if not step_tool:
            return {'pass': False, 'reason': f'missing_tool_chain_tool:{idx}'}
        if step_tool not in allowed_tools:
            return {'pass': False, 'reason': f'tool_chain_not_allowed:{idx}:{step_tool}'}
        banned, pattern = contains_banned_patterns(step_args)
        if banned:
            return {'pass': False, 'reason': f'tool_chain_disallowed_pattern:{idx}:{pattern}'}
        restricted, restricted_pattern = contains_tool_restricted_patterns(step_tool, step_args)
        if restricted:
            return {'pass': False, 'reason': f'tool_chain_restricted_pattern:{idx}:{step_tool}:{restricted_pattern}'}
        target_reason = _check_target_semantics(step_tool, step_args, tool_catalog, stdin_text=step.get('stdin') or '')
        if target_reason:
            return {'pass': False, 'reason': f'tool_chain_{idx}:{target_reason}'}
        scope_reason = _check_scope_semantics(step_args, scope_domains, stdin_text=step.get('stdin') or '')
        if scope_reason:
            return {'pass': False, 'reason': f'tool_chain_{idx}:{scope_reason}'}
        creds_ok, creds_reason = check_credentials_policy(step_args, creds, owner_approved_auth, step_tool)
        if not creds_ok:
            return {'pass': False, 'reason': f'tool_chain_{idx}:{creds_reason}'}

    return {'pass': True, 'reason': 'ok'}
