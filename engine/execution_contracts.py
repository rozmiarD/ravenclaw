from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List
from urllib.parse import urlparse

from campaign_utils import extract_host_from_url  # type: ignore


_DECORATION_HEADER_FLAGS = {'-H', '--header', '--headers'}
_DECORATION_COOKIE_FLAGS = {'-b', '--cookie'}
_DECORATION_BASIC_AUTH_FLAGS = {'-u', '--user'}
_SUPPORTED_DECORATION_TOOLS = {'curl', 'ffuf', 'httpx', 'httpx-pd', 'katana', 'feroxbuster', 'gobuster'}
_HEADER_RAW_TOOLS = {'curl', 'ffuf', 'httpx-pd', 'katana', 'feroxbuster', 'gobuster'}
_HEADER_PAIR_TOOLS = {'httpx'}
_COOKIE_RAW_TOOLS = {'curl', 'ffuf', 'feroxbuster'}
_COOKIE_GOBUSTER_TOOLS = {'gobuster'}
_COOKIE_PAIR_TOOLS = {'httpx'}
_BASIC_AUTH_RAW_TOOLS = {'curl'}
_BASIC_AUTH_PAIR_TOOLS = {'httpx'}


def _safe_str(value: Any) -> str:
    return str(value or '')


def _deepcopy_jsonish(value: Any) -> Any:
    try:
        return deepcopy(value)
    except Exception:
        return value


def _candidate_host_from_scalar(value: Any) -> str:
    text = _safe_str(value).strip()
    if not text:
        return ''
    lowered = text.lower()
    for prefix in ('host:', 'origin:', 'referer:', 'authority:'):
        if lowered.startswith(prefix):
            text = text[len(prefix):].strip()
            lowered = text.lower()
            break
    host = _safe_str(extract_host_from_url(text)).strip().lower()
    if host:
        return host
    token = text.strip("\"'`()[]{}<>,;")
    if not token or token.startswith('-'):
        return ''
    if '@' in token and '://' not in token:
        return ''
    parsed = urlparse('//' + token)
    host = _safe_str(parsed.hostname).strip().lower()
    if host.startswith('*.'):
        host = host[2:]
    if not host or '.' not in host:
        return ''
    if any(ch.isspace() for ch in host):
        return ''
    allowed = set('abcdefghijklmnopqrstuvwxyz0123456789.-')
    if any(ch not in allowed for ch in host):
        return ''
    return host


def _collect_hosts_from_args(args: List[Any]) -> List[str]:
    hosts: List[str] = []
    seen: set[str] = set()
    for raw in list(args or []):
        host = _candidate_host_from_scalar(raw)
        if host and host not in seen:
            seen.add(host)
            hosts.append(host)
    return hosts


def summarize_request_shape_hygiene(*, target: str, normalized_args: List[Any], execution_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
    target_host = _safe_str(extract_host_from_url(target)).strip().lower()
    arg_hosts = _collect_hosts_from_args(normalized_args)
    plan_hosts: List[str] = []
    seen_plan: set[str] = set()
    for step in list(execution_plan or []):
        if not isinstance(step, dict):
            continue
        for host in _collect_hosts_from_args(list(step.get('args') or [])):
            if host not in seen_plan:
                seen_plan.add(host)
                plan_hosts.append(host)
    detected_hosts: List[str] = []
    seen_all: set[str] = set()
    for host in [*arg_hosts, *plan_hosts]:
        if host not in seen_all:
            seen_all.add(host)
            detected_hosts.append(host)
    detected_sources: List[str] = []
    if arg_hosts:
        detected_sources.append('normalized_args')
    if plan_hosts:
        detected_sources.append('execution_plan')
    mismatched_hosts = [host for host in detected_hosts if host != target_host] if target_host else list(detected_hosts)
    mismatch_sources: List[str] = []
    if any(host != target_host for host in arg_hosts if target_host):
        mismatch_sources.append('normalized_args')
    elif arg_hosts and not target_host:
        mismatch_sources.append('normalized_args')
    if any(host != target_host for host in plan_hosts if target_host):
        mismatch_sources.append('execution_plan')
    elif plan_hosts and not target_host:
        mismatch_sources.append('execution_plan')
    if mismatched_hosts:
        reason = f"mismatched_hosts_detected:{','.join(mismatched_hosts)}"
        status = 'cross_host_mismatch'
        match_status = 'mixed'
    elif detected_hosts:
        reason = 'all_detected_hosts_match_target'
        status = 'clean'
        match_status = 'exact'
    else:
        reason = 'no_hosts_detected_in_prepared_shape'
        status = 'ambiguous'
        match_status = 'none_detected'
    return {
        'target_host': target_host,
        'arg_hosts_detected': arg_hosts,
        'execution_plan_hosts_detected': plan_hosts,
        'all_hosts_detected': detected_hosts,
        'mismatched_hosts_detected': mismatched_hosts,
        'target_host_match_status': match_status,
        'request_shape_hygiene_status': status,
        'request_shape_hygiene_reason': reason,
        'request_shape_hygiene_source': '+'.join(mismatch_sources) if mismatch_sources else ('+'.join(detected_sources) if detected_sources else 'none'),
    }


def _header_entry(raw: str, *, creds: Dict[str, Any]) -> Dict[str, Any]:
    text = _safe_str(raw).strip()
    if ':' in text:
        name, value = text.split(':', 1)
        name = name.strip()
        value = value.strip()
    else:
        name, value = text, ''
    source = 'operator_supplied'
    user = _safe_str(creds.get('bug_bounty_username')).strip()
    mail = _safe_str(creds.get('test_account_email')).strip()
    if name.lower() == 'x-bug-bounty' and user and value == user:
        source = 'campaign_required'
    elif name.lower() == 'x-test-account-email' and mail and value == mail:
        source = 'campaign_required'
    return {
        'name': name,
        'value': value,
        'raw': text,
        'source': source,
    }


def _cookie_entries(raw: str, *, redacted: bool = True) -> List[Dict[str, Any]]:
    text = _safe_str(raw).strip()
    if not text:
        return []
    out: List[Dict[str, Any]] = []
    for part in text.split(';'):
        token = str(part).strip()
        if not token:
            continue
        if '=' in token:
            name, value = token.split('=', 1)
            out.append({'name': name.strip(), 'value': '<redacted>' if redacted else value.strip(), 'source': 'operator_supplied'})
        else:
            out.append({'name': token, 'value': '<redacted>' if redacted else '', 'source': 'operator_supplied'})
    return out


def _request_decoration_from_creds(creds: Dict[str, Any]) -> Dict[str, Any]:
    rd = dict(creds.get('request_decoration') or {}) if isinstance(creds.get('request_decoration'), dict) else {}
    headers: List[Dict[str, Any]] = []
    user = _safe_str(creds.get('bug_bounty_username')).strip()
    mail = _safe_str(creds.get('test_account_email')).strip()
    if user:
        headers.append({'name': 'X-Bug-Bounty', 'value': user, 'source': 'campaign_required'})
    if mail:
        headers.append({'name': 'X-Test-Account-Email', 'value': mail, 'source': 'campaign_required'})

    for item in list(rd.get('headers') or []):
        if not isinstance(item, dict):
            continue
        name = _safe_str(item.get('name')).strip()
        if not name:
            continue
        headers.append({
            'name': name,
            'value': _safe_str(item.get('value')),
            'source': _safe_str(item.get('source') or 'operator_supplied').strip() or 'operator_supplied',
        })

    cookies: List[Dict[str, Any]] = []
    for item in list(rd.get('cookies') or []):
        if not isinstance(item, dict):
            continue
        name = _safe_str(item.get('name')).strip()
        if not name:
            continue
        cookies.append({
            'name': name,
            'value': _safe_str(item.get('value')),
            'source': _safe_str(item.get('source') or 'operator_supplied').strip() or 'operator_supplied',
        })

    basic_in = rd.get('basic_auth') if isinstance(rd.get('basic_auth'), dict) else {}
    basic_auth = {
        'enabled': bool(basic_in.get('enabled', False)),
        'username': _safe_str(basic_in.get('username')),
        'password': _safe_str(basic_in.get('password')),
        'password_ref': _safe_str(basic_in.get('password_ref')),
    }

    has_campaign = any(h.get('source') == 'campaign_required' for h in headers)
    has_operator = any(h.get('source') != 'campaign_required' for h in headers) or bool(cookies) or bool(basic_auth.get('enabled'))
    mode = _safe_str(rd.get('mode')).strip().lower()
    if mode not in {'none', 'campaign_required', 'operator_supplied', 'mixed'}:
        if has_campaign and has_operator:
            mode = 'mixed'
        elif has_campaign:
            mode = 'campaign_required'
        elif has_operator:
            mode = 'operator_supplied'
        else:
            mode = 'none'

    return {
        'mode': mode,
        'headers': headers,
        'cookies': cookies,
        'basic_auth': basic_auth,
        'uses_auth_header': bool(creds.get('allow_auth_header', False)),
        'uses_cookie_header': bool(creds.get('allow_cookie_header', False)),
        'owner_approval_required': bool(creds.get('credentials_required', False) and not creds.get('credentials_owner_approved', False)),
        'provenance_notes': [str(x) for x in (rd.get('provenance_notes') or []) if str(x).strip()],
    }


def _args_have_header(args: List[str], name: str, *, tool: str = '') -> bool:
    target = name.strip().lower()
    norm_tool = _safe_str(tool).strip().lower()
    i = 0
    while i < len(args):
        tok = _safe_str(args[i]).strip()
        nxt = _safe_str(args[i + 1]).strip() if i + 1 < len(args) else ''
        nxt2 = _safe_str(args[i + 2]).strip() if i + 2 < len(args) else ''
        if norm_tool in _HEADER_PAIR_TOOLS and tok in {'--headers', '-h'} and nxt and nxt2:
            if nxt.strip().lower() == target:
                return True
            i += 3
            continue
        if tok in _DECORATION_HEADER_FLAGS and nxt:
            hdr = _header_entry(nxt, creds={})
            if _safe_str(hdr.get('name')).strip().lower() == target:
                return True
            i += 2
            continue
        i += 1
    return False


def _args_have_cookie(args: List[str], name: str, *, tool: str = '') -> bool:
    target = name.strip().lower()
    norm_tool = _safe_str(tool).strip().lower()
    i = 0
    while i < len(args):
        tok = _safe_str(args[i]).strip()
        nxt = _safe_str(args[i + 1]).strip() if i + 1 < len(args) else ''
        nxt2 = _safe_str(args[i + 2]).strip() if i + 2 < len(args) else ''
        if norm_tool in _COOKIE_PAIR_TOOLS and tok == '--cookies' and nxt and nxt2:
            if nxt.strip().lower() == target:
                return True
            i += 3
            continue
        if norm_tool in _COOKIE_GOBUSTER_TOOLS and tok in {'-c', '--cookies'} and nxt:
            for item in _cookie_entries(nxt, redacted=False):
                if _safe_str(item.get('name')).strip().lower() == target:
                    return True
            i += 2
            continue
        if tok in _DECORATION_COOKIE_FLAGS and nxt:
            for item in _cookie_entries(nxt, redacted=False):
                if _safe_str(item.get('name')).strip().lower() == target:
                    return True
            i += 2
            continue
        i += 1
    return False


def _args_have_basic_auth(args: List[str], *, tool: str = '') -> bool:
    norm_tool = _safe_str(tool).strip().lower()
    i = 0
    while i < len(args):
        tok = _safe_str(args[i]).strip()
        nxt = _safe_str(args[i + 1]).strip() if i + 1 < len(args) else ''
        nxt2 = _safe_str(args[i + 2]).strip() if i + 2 < len(args) else ''
        if norm_tool in _BASIC_AUTH_PAIR_TOOLS and tok == '--auth' and nxt and nxt2:
            return True
        if tok in _DECORATION_BASIC_AUTH_FLAGS and nxt:
            return True
        i += 1
    return False


def apply_request_decoration_to_args(tool: str, args: List[Any], creds: Dict[str, Any]) -> List[str]:
    norm_tool = _safe_str(tool).strip().lower()
    out = [_safe_str(a) for a in (args or [])]
    if norm_tool not in _SUPPORTED_DECORATION_TOOLS:
        return out

    decoration = _request_decoration_from_creds(creds)
    for header in decoration.get('headers', []):
        if not isinstance(header, dict):
            continue
        name = _safe_str(header.get('name')).strip()
        if not name or _args_have_header(out, name, tool=norm_tool):
            continue
        value = _safe_str(header.get('value'))
        if norm_tool in _HEADER_PAIR_TOOLS:
            out.extend(['--headers', name, value])
        else:
            out.extend(['-H', f"{name}: {value}"])

    for cookie in decoration.get('cookies', []):
        if not isinstance(cookie, dict):
            continue
        name = _safe_str(cookie.get('name')).strip()
        if not name or _args_have_cookie(out, name, tool=norm_tool):
            continue
        value = _safe_str(cookie.get('value'))
        if norm_tool in _COOKIE_PAIR_TOOLS:
            out.extend(['--cookies', name, value])
        elif norm_tool in _COOKIE_GOBUSTER_TOOLS:
            out.extend(['-c', f'{name}={value}' if value else name])
        elif norm_tool in _COOKIE_RAW_TOOLS:
            out.extend(['-b', f'{name}={value}' if value else name])

    basic_auth = decoration.get('basic_auth') if isinstance(decoration.get('basic_auth'), dict) else {}
    if bool(basic_auth.get('enabled')) and not _args_have_basic_auth(out, tool=norm_tool):
        username = _safe_str(basic_auth.get('username')).strip()
        password = _safe_str(basic_auth.get('password'))
        if username:
            if norm_tool in _BASIC_AUTH_PAIR_TOOLS:
                out.extend(['--auth', username, password])
            elif norm_tool in _BASIC_AUTH_RAW_TOOLS:
                out.extend(['-u', f'{username}:{password}'])

    return out


def summarize_request_decoration(action_spec: Dict[str, Any], creds: Dict[str, Any]) -> Dict[str, Any]:
    headers: List[Dict[str, Any]] = []
    cookies: List[Dict[str, Any]] = []
    basic_auth = {'enabled': False, 'username': '', 'password_ref': ''}
    execution_plan = action_spec.get('tool_chain') if isinstance(action_spec.get('tool_chain'), list) else []
    if not execution_plan:
        execution_plan = [{'tool': action_spec.get('tool'), 'args': action_spec.get('args', [])}]

    for step in execution_plan:
        if not isinstance(step, dict):
            continue
        args = list(step.get('args') or [])
        i = 0
        while i < len(args):
            tok = _safe_str(args[i]).strip()
            nxt = _safe_str(args[i + 1]).strip() if i + 1 < len(args) else ''
            if tok in _DECORATION_HEADER_FLAGS and nxt:
                headers.append(_header_entry(nxt, creds=creds))
                i += 2
                continue
            if tok in _DECORATION_COOKIE_FLAGS and nxt:
                cookies.extend(_cookie_entries(nxt))
                i += 2
                continue
            if tok in _DECORATION_BASIC_AUTH_FLAGS and nxt:
                basic_auth['enabled'] = True
                basic_auth['username'] = nxt.split(':', 1)[0].strip() if ':' in nxt else nxt
                basic_auth['password_ref'] = 'inline_redacted'
                i += 2
                continue
            i += 1

    config_decoration = _request_decoration_from_creds(creds)
    has_campaign = any(h.get('source') == 'campaign_required' for h in headers)
    has_operator = any(h.get('source') != 'campaign_required' for h in headers) or bool(cookies) or bool(basic_auth['enabled'])
    if has_campaign and has_operator:
        mode = 'mixed'
    elif has_campaign:
        mode = 'campaign_required'
    elif has_operator:
        mode = 'operator_supplied'
    else:
        mode = 'none'

    return {
        'mode': mode,
        'headers': headers,
        'cookies': cookies,
        'basic_auth': basic_auth,
        'uses_auth_header': bool(creds.get('allow_auth_header', False)),
        'uses_cookie_header': bool(creds.get('allow_cookie_header', False)),
        'owner_approval_required': bool(creds.get('credentials_required', False) and not creds.get('credentials_owner_approved', False)),
        'provenance_notes': list(config_decoration.get('provenance_notes') or []),
        'policy_snapshot': {
            'mode': _safe_str(config_decoration.get('mode') or ''),
            'header_count': len(list(config_decoration.get('headers') or [])),
            'cookie_count': len(list(config_decoration.get('cookies') or [])),
            'basic_auth_enabled': bool((config_decoration.get('basic_auth') or {}).get('enabled', False)) if isinstance(config_decoration.get('basic_auth'), dict) else False,
        },
    }


def redact_prepared_execution_spec_for_auditor(spec: Dict[str, Any]) -> Dict[str, Any]:
    redacted = _deepcopy_jsonish(spec)
    if not isinstance(redacted, dict):
        return {'error': 'invalid_prepared_execution_spec'}

    def _truncate_arg(value: Any) -> str:
        s = _safe_str(value)
        return s if len(s) <= 240 else (s[:240] + '...<truncated>')

    if isinstance(redacted.get('normalized_args'), list):
        norm_args = []
        args = list(redacted.get('normalized_args') or [])
        i = 0
        while i < len(args):
            tok = _safe_str(args[i]).strip()
            nxt = _safe_str(args[i + 1]).strip() if i + 1 < len(args) else ''
            if tok in _DECORATION_COOKIE_FLAGS and nxt:
                norm_args.extend([tok, '<cookie_redacted>'])
                i += 2
                continue
            if tok in _DECORATION_BASIC_AUTH_FLAGS and nxt:
                user = nxt.split(':', 1)[0].strip() if ':' in nxt else nxt
                norm_args.extend([tok, f'{user}:<redacted>'])
                i += 2
                continue
            norm_args.append(_truncate_arg(tok))
            i += 1
        redacted['normalized_args'] = norm_args

    plan = redacted.get('execution_plan') if isinstance(redacted.get('execution_plan'), list) else []
    safe_plan = []
    for step in plan:
        if not isinstance(step, dict):
            continue
        step_out = dict(step)
        step_args = []
        raw_args = list(step.get('args') or [])
        i = 0
        while i < len(raw_args):
            tok = _safe_str(raw_args[i]).strip()
            nxt = _safe_str(raw_args[i + 1]).strip() if i + 1 < len(raw_args) else ''
            if tok in _DECORATION_COOKIE_FLAGS and nxt:
                step_args.extend([tok, '<cookie_redacted>'])
                i += 2
                continue
            if tok in _DECORATION_BASIC_AUTH_FLAGS and nxt:
                user = nxt.split(':', 1)[0].strip() if ':' in nxt else nxt
                step_args.extend([tok, f'{user}:<redacted>'])
                i += 2
                continue
            step_args.append(_truncate_arg(tok))
            i += 1
        step_out['args'] = step_args
        safe_plan.append(step_out)
    redacted['execution_plan'] = safe_plan

    request_decoration = redacted.get('request_decoration') if isinstance(redacted.get('request_decoration'), dict) else {}
    if request_decoration:
        cookies = []
        for item in list(request_decoration.get('cookies') or []):
            if not isinstance(item, dict):
                continue
            cookies.append({**item, 'value': '<redacted>'})
        basic = dict(request_decoration.get('basic_auth') or {}) if isinstance(request_decoration.get('basic_auth'), dict) else {}
        if basic:
            basic['password_ref'] = basic.get('password_ref') or '<redacted>'
        request_decoration['cookies'] = cookies
        request_decoration['basic_auth'] = basic
        redacted['request_decoration'] = request_decoration

    return redacted


def build_prepared_execution_spec(
    *,
    raw_action_spec: Dict[str, Any],
    prepared_action_spec: Dict[str, Any],
    compiled_action: Dict[str, Any],
    creds_policy: Dict[str, Any],
    target: str,
    target_in_scope: bool,
) -> Dict[str, Any]:
    execution_plan = prepared_action_spec.get('tool_chain') if isinstance(prepared_action_spec.get('tool_chain'), list) else []
    normalized_args = list(prepared_action_spec.get('args') or [])
    target_host = extract_host_from_url(target)
    request_shape_hygiene = summarize_request_shape_hygiene(
        target=target,
        normalized_args=normalized_args,
        execution_plan=execution_plan,
    )
    return {
        'spec_version': '2026-03-18.prepared.v1',
        'target': _safe_str(target),
        'target_host': _safe_str(target_host),
        'target_in_scope': bool(target_in_scope),
        'action_type': _safe_str(compiled_action.get('action_type') or prepared_action_spec.get('action_type') or raw_action_spec.get('action_type') or 'single_probe'),
        'capability': _safe_str(compiled_action.get('capability') or prepared_action_spec.get('capability') or raw_action_spec.get('capability') or ''),
        'task_family': _safe_str(prepared_action_spec.get('task_family') or raw_action_spec.get('task_family') or ''),
        'execution_mode': _safe_str(compiled_action.get('execution_mode') or prepared_action_spec.get('execution_mode') or 'normalized'),
        'resolved_planner_profiles': list(prepared_action_spec.get('resolved_planner_profiles') or compiled_action.get('resolved_planner_profiles') or []),
        'resolved_tool': _safe_str(compiled_action.get('compiler_tool_choice') or compiled_action.get('tool') or prepared_action_spec.get('tool') or ''),
        'tool_candidates': list(prepared_action_spec.get('tool_candidates') or compiled_action.get('tool_candidates') or []),
        'normalized_args': normalized_args,
        'execution_plan': _deepcopy_jsonish(execution_plan),
        'request_decoration': summarize_request_decoration(prepared_action_spec, creds_policy),
        'arg_hosts_detected': list(request_shape_hygiene.get('arg_hosts_detected') or []),
        'execution_plan_hosts_detected': list(request_shape_hygiene.get('execution_plan_hosts_detected') or []),
        'all_hosts_detected': list(request_shape_hygiene.get('all_hosts_detected') or []),
        'mismatched_hosts_detected': list(request_shape_hygiene.get('mismatched_hosts_detected') or []),
        'target_host_match_status': _safe_str(request_shape_hygiene.get('target_host_match_status') or ''),
        'request_shape_hygiene_status': _safe_str(request_shape_hygiene.get('request_shape_hygiene_status') or ''),
        'request_shape_hygiene_reason': _safe_str(request_shape_hygiene.get('request_shape_hygiene_reason') or ''),
        'request_shape_hygiene_source': _safe_str(request_shape_hygiene.get('request_shape_hygiene_source') or ''),
        'scope_facts': {
            'target': _safe_str(target),
            'target_host': _safe_str(target_host),
            'target_in_scope': bool(target_in_scope),
        },
        'credentials_policy_snapshot': {
            'credentials_required': bool(creds_policy.get('credentials_required', False)),
            'allow_auth_header': bool(creds_policy.get('allow_auth_header', False)),
            'allow_cookie_header': bool(creds_policy.get('allow_cookie_header', False)),
            'allow_basic_auth': bool(creds_policy.get('allow_basic_auth', False)),
            'credentials_owner_approved': bool(creds_policy.get('credentials_owner_approved', False)),
            'resolved_campaign_key': _safe_str(creds_policy.get('resolved_campaign_key') or ''),
        },
        'compiler': {
            'compiler_strategy': _safe_str(compiled_action.get('compiler_strategy') or ''),
            'compiler_tool_choice': _safe_str(compiled_action.get('compiler_tool_choice') or compiled_action.get('tool') or ''),
            'compiler_tool_choice_source': _safe_str(compiled_action.get('compiler_tool_choice_source') or ''),
            'compiler_variant_count': int(compiled_action.get('compiler_variant_count', 1) or 1),
            'recipe_name': _safe_str(compiled_action.get('recipe_name') or ''),
            'semantic_loss_detected': bool(compiled_action.get('semantic_loss_detected', False)),
            'normalization_reason': _safe_str(compiled_action.get('normalization_reason') or ''),
            'semantic_loss_policy': _deepcopy_jsonish(compiled_action.get('semantic_loss_policy') or {}),
        },
    }


def build_command_preview_from_execution_spec(spec: Dict[str, Any]) -> List[str]:
    if not isinstance(spec, dict):
        return []
    execution_plan = spec.get('execution_plan') if isinstance(spec.get('execution_plan'), list) else []
    if execution_plan:
        first = execution_plan[0] if isinstance(execution_plan[0], dict) else {}
        tool = _safe_str(first.get('tool') or spec.get('resolved_tool') or '')
        args = list(first.get('args') or []) if isinstance(first, dict) else []
        return [tool, *[_safe_str(a) for a in args]] if tool else [_safe_str(a) for a in args]
    tool = _safe_str(spec.get('resolved_tool') or '')
    args = list(spec.get('normalized_args') or [])
    return [tool, *[_safe_str(a) for a in args]] if tool else [_safe_str(a) for a in args]



def build_approved_execution_spec(
    prepared_execution_spec: Dict[str, Any],
    *,
    auditor: Dict[str, Any],
    approval_source: str,
    approval_transform_chain: List[Dict[str, Any]],
    owner_override_applied: bool,
) -> Dict[str, Any]:
    approved = _deepcopy_jsonish(prepared_execution_spec)
    compiler = approved.get('compiler') if isinstance(approved.get('compiler'), dict) else {}
    semantic_policy = compiler.get('semantic_loss_policy') if isinstance(compiler.get('semantic_loss_policy'), dict) else {}
    semantic_rereview_required = _safe_str(semantic_policy.get('policy_response') or '') == 'auditor_rereview'
    approved['approval'] = {
        'decision': _safe_str((auditor or {}).get('decision') or ''),
        'reason': _safe_str((auditor or {}).get('reason') or ''),
        'reason_code': _safe_str((auditor or {}).get('reason_code') or ''),
        'constraints': _deepcopy_jsonish((auditor or {}).get('constraints') or {}),
        'approval_source': _safe_str(approval_source),
        'owner_override_applied': bool(owner_override_applied),
        'approval_transform_chain': _deepcopy_jsonish(approval_transform_chain),
        'approved_under_degradation': bool(semantic_policy.get('approved_under_degradation', False)),
        'semantic_loss_rereview_required': semantic_rereview_required,
        'semantic_loss_rereview_completed': semantic_rereview_required and _safe_str((auditor or {}).get('decision') or '') == 'approve',
        'semantic_loss_rereview_decision': _safe_str((auditor or {}).get('decision') or '') if semantic_rereview_required else '',
    }
    approved['execution_truth'] = {
        'artifact_type': 'approved_execution_spec',
        'resolved_tool': _safe_str(approved.get('resolved_tool') or ''),
        'normalized_args': _deepcopy_jsonish(approved.get('normalized_args') or []),
        'execution_plan': _deepcopy_jsonish(approved.get('execution_plan') or []),
        'command_preview': build_command_preview_from_execution_spec(approved),
        'arg_hosts_detected': _deepcopy_jsonish(approved.get('arg_hosts_detected') or []),
        'execution_plan_hosts_detected': _deepcopy_jsonish(approved.get('execution_plan_hosts_detected') or []),
        'all_hosts_detected': _deepcopy_jsonish(approved.get('all_hosts_detected') or []),
        'mismatched_hosts_detected': _deepcopy_jsonish(approved.get('mismatched_hosts_detected') or []),
        'target_host_match_status': _safe_str(approved.get('target_host_match_status') or ''),
        'request_shape_hygiene_status': _safe_str(approved.get('request_shape_hygiene_status') or ''),
        'request_shape_hygiene_reason': _safe_str(approved.get('request_shape_hygiene_reason') or ''),
        'request_shape_hygiene_source': _safe_str(approved.get('request_shape_hygiene_source') or ''),
    }
    approved['spec_version'] = '2026-03-18.approved.v1'
    return approved
