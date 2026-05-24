from __future__ import annotations

import copy
from typing import Any, Dict, Iterable, List, Tuple

from govengine_security_helpers import (  # type: ignore
    ACTION_TYPES,
    ACTION_TYPE_TO_CAPABILITY,
    DEFAULT_ACTION_TYPE,
    can_resolve_tool_from_capability,
    get_capability_catalog,
    get_planner_visible_tools,
    get_runtime_brain_allowed_tools,
    normalize_tool,
    validate_action_contract_v2,
    validate_probe_recipe,
)

ALLOWED_BRAIN_ALIGNMENT = {'aligned', 'override', 'unknown', 'partial'}
ALLOWED_REDUNDANCY_RISK = {'low', 'medium', 'high', 'unknown', ''}
CAPABILITIES = set(get_capability_catalog())

ALLOWED_AUDITOR_DECISIONS = {'approve', 'reject', 'owner_approval_required', 'deny', 'blocked'}
ALLOWED_AUDITOR_REASON_CODES = {
    'approve_in_scope',
    'reject_invalid_contract',
    'reject_policy_gate',
    'reject_out_of_scope',
    'owner_approval_required_risk',
    'owner_approval_required_auth',
    'owner_approval_required_uncertain',
    'owner_approval_required_policy',
    'auditor_timeout',
    'invalid_auditor_contract',
    'owner_override',
    'auditor_approve',
    'auditor_reject',
    'auditor_deny',
    'auditor_blocked',
    'auditor_owner_approval_required',
    'auditor_unknown',
    'policy_gate_block',
}
ALLOWED_RISK_BANDS = {'low', 'medium', 'high'}
SHELL_OPERATOR_TOKENS = ('&&', '||', '|', ';', '`', '$(', '>', '<')
BASIC_AUTH_ARG_FLAGS = {'-u', '--user'}
BASIC_AUTH_PAIR_FLAGS = {'--auth'}
CREDENTIALED_ENUMERATION_TOOLS = {'katana', 'feroxbuster', 'gobuster', 'ffuf'}
CREDENTIALED_ENUMERATION_TASK_FAMILIES = {'content_discovery'}
CREDENTIALED_ENUMERATION_ACTION_TYPES = {'enumeration_probe'}
CREDENTIALED_ENUMERATION_AGGRESSION_CAP = 3


def _first_shell_operator_fragment(value: str) -> tuple[int, str] | None:
    raw = str(value or '')
    found: tuple[int, str] | None = None
    for token in SHELL_OPERATOR_TOKENS:
        idx = raw.find(token)
        if idx == -1:
            continue
        if found is None or idx < found[0] or (idx == found[0] and len(token) > len(found[1])):
            found = (idx, token)
    return found


def _sanitize_args(args: Any, *, prefix: str = '') -> tuple[Any, List[Dict[str, Any]]]:
    if not isinstance(args, list):
        return args, []
    sanitized: List[str] = []
    notes: List[Dict[str, Any]] = []
    for idx, arg in enumerate(args):
        s = str(arg)
        found = _first_shell_operator_fragment(s)
        if not found:
            sanitized.append(s)
            continue
        pos, token = found
        trimmed = s[:pos].rstrip()
        note = {
            'path': f'{prefix}args[{idx}]' if prefix else f'args[{idx}]',
            'token': token,
            'dropped_fragment': s[pos:pos + 40],
        }
        if trimmed:
            sanitized.append(trimmed)
            note['action'] = 'trimmed_arg'
            note['kept'] = trimmed[:120]
        else:
            note['action'] = 'dropped_arg'
        notes.append(note)
    return sanitized, notes


def _strip_disallowed_basic_auth_args(args: Any, *, prefix: str = '') -> tuple[Any, List[Dict[str, Any]]]:
    if not isinstance(args, list):
        return args, []
    sanitized: List[str] = []
    notes: List[Dict[str, Any]] = []
    values = [str(arg) for arg in args]
    i = 0
    while i < len(values):
        token = values[i]
        path = f'{prefix}args[{i}]' if prefix else f'args[{i}]'
        if token in BASIC_AUTH_ARG_FLAGS:
            note: Dict[str, Any] = {
                'path': path,
                'action': 'dropped_basic_auth_flag',
                'token': token,
            }
            if i + 1 < len(values):
                note['dropped_value'] = '<redacted>'
                i += 2
            else:
                note['orphaned_flag'] = True
                i += 1
            notes.append(note)
            continue
        if token in BASIC_AUTH_PAIR_FLAGS:
            note = {
                'path': path,
                'action': 'dropped_basic_auth_flag',
                'token': token,
            }
            dropped_count = 1
            if i + 1 < len(values):
                dropped_count += 1
            if i + 2 < len(values):
                dropped_count += 1
            note['dropped_parts'] = dropped_count
            i += dropped_count
            notes.append(note)
            continue
        sanitized.append(token)
        i += 1
    return sanitized, notes


def sanitize_action_spec(spec: Dict[str, Any]) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not isinstance(spec, dict):
        return spec, []
    clone: Dict[str, Any] = copy.deepcopy(spec)
    notes: List[Dict[str, Any]] = []
    args, arg_notes = _sanitize_args(clone.get('args', []))
    if arg_notes:
        clone['args'] = args
        notes.extend(arg_notes)
    tool_chain = clone.get('tool_chain')
    if isinstance(tool_chain, list):
        for idx, step in enumerate(tool_chain):
            if not isinstance(step, dict) or 'args' not in step:
                continue
            args, step_notes = _sanitize_args(step.get('args', []), prefix=f'tool_chain[{idx}].')
            if step_notes:
                step['args'] = args
                notes.extend(step_notes)
    return clone, notes


def sanitize_action_spec_auth_modes(spec: Dict[str, Any], creds_policy: Dict[str, Any] | None = None) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not isinstance(spec, dict):
        return spec, []
    policy = creds_policy if isinstance(creds_policy, dict) else {}
    if bool(policy.get('allow_basic_auth', False)):
        return copy.deepcopy(spec), []

    clone: Dict[str, Any] = copy.deepcopy(spec)
    notes: List[Dict[str, Any]] = []
    args, arg_notes = _strip_disallowed_basic_auth_args(clone.get('args', []))
    if arg_notes:
        clone['args'] = args
        notes.extend(arg_notes)
    tool_chain = clone.get('tool_chain')
    if isinstance(tool_chain, list):
        for idx, step in enumerate(tool_chain):
            if not isinstance(step, dict) or 'args' not in step:
                continue
            args, step_notes = _strip_disallowed_basic_auth_args(step.get('args', []), prefix=f'tool_chain[{idx}].')
            if step_notes:
                step['args'] = args
                notes.extend(step_notes)
    return clone, notes


def _has_request_decoration(creds_policy: Dict[str, Any]) -> bool:
    policy = creds_policy if isinstance(creds_policy, dict) else {}
    request_decoration = policy.get('request_decoration') if isinstance(policy.get('request_decoration'), dict) else {}
    headers = request_decoration.get('headers') if isinstance(request_decoration.get('headers'), list) else []
    cookies = request_decoration.get('cookies') if isinstance(request_decoration.get('cookies'), list) else []
    basic_auth = request_decoration.get('basic_auth') if isinstance(request_decoration.get('basic_auth'), dict) else {}
    mode = str(request_decoration.get('mode') or '').strip().lower()
    return bool(
        mode in {'campaign_required', 'operator_supplied', 'mixed'}
        or headers
        or cookies
        or bool(basic_auth.get('enabled', False))
    )


def _is_credentialed_enumeration_shape(spec: Dict[str, Any]) -> bool:
    if not isinstance(spec, dict):
        return False
    tool = normalize_tool(spec.get('tool'))
    action_type = str(spec.get('action_type') or '').strip().lower()
    task_family = str(spec.get('task_family') or '').strip().lower()
    if tool in CREDENTIALED_ENUMERATION_TOOLS and (
        action_type in CREDENTIALED_ENUMERATION_ACTION_TYPES or task_family in CREDENTIALED_ENUMERATION_TASK_FAMILIES
    ):
        return True
    tool_chain = spec.get('tool_chain') if isinstance(spec.get('tool_chain'), list) else []
    for step in tool_chain:
        if not isinstance(step, dict):
            continue
        step_tool = normalize_tool(step.get('tool'))
        if step_tool in CREDENTIALED_ENUMERATION_TOOLS and (
            action_type in CREDENTIALED_ENUMERATION_ACTION_TYPES or task_family in CREDENTIALED_ENUMERATION_TASK_FAMILIES
        ):
            return True
    return False


def remap_aggression_for_policy(spec: Dict[str, Any], creds_policy: Dict[str, Any] | None, aggression: int | str | None) -> tuple[int, Dict[str, Any] | None]:
    try:
        requested = int(aggression or 0)
    except Exception:
        requested = 0
    if requested <= 0:
        return requested, None
    if not _has_request_decoration(creds_policy if isinstance(creds_policy, dict) else {}):
        return requested, None
    if not _is_credentialed_enumeration_shape(spec):
        return requested, None
    if requested <= CREDENTIALED_ENUMERATION_AGGRESSION_CAP:
        return requested, None
    remapped = CREDENTIALED_ENUMERATION_AGGRESSION_CAP
    return remapped, {
        'reason': 'credentialed_crawler_policy_cap',
        'requested_aggression': requested,
        'effective_aggression': remapped,
        'cap': CREDENTIALED_ENUMERATION_AGGRESSION_CAP,
        'task_family': str(spec.get('task_family') or '').strip().lower(),
        'action_type': str(spec.get('action_type') or '').strip().lower(),
        'tool': normalize_tool(spec.get('tool')),
    }


def _validate_args(args: Any, prefix: str = '') -> List[str]:
    errors: List[str] = []
    label = prefix or ''
    if not isinstance(args, list):
        return [f'{label}args_must_be_array']
    if len(args) > 32:
        errors.append(f'{label}args_too_long')
    for idx, arg in enumerate(args):
        s = str(arg)
        if _first_shell_operator_fragment(s):
            errors.append(f'{label}arg_contains_shell_operator:{idx}')
            break
        if '<' in s and '>' in s:
            errors.append(f'{label}arg_contains_placeholder:{idx}')
            break
    return errors


def _validate_stdin(value: Any, prefix: str = '') -> List[str]:
    errors: List[str] = []
    label = prefix or ''
    if value is None:
        return errors
    if not isinstance(value, str):
        return [f'{label}stdin_must_be_string']
    if '\x00' in value:
        errors.append(f'{label}stdin_contains_nul')
    if len(value) > 4096:
        errors.append(f'{label}stdin_too_long')
    if len(value.splitlines()) > 32:
        errors.append(f'{label}stdin_too_many_lines')
    return errors


def get_contract_allowed_tools(requested_profiles: Iterable[str] | str | None = None) -> set[str]:
    return {str(x).strip().lower() for x in get_runtime_brain_allowed_tools(requested_profiles) if str(x).strip()}


def _allowed_tools_set(allowed_tools: Iterable[str] | None = None, requested_profiles: Iterable[str] | str | None = None) -> set[str]:
    if allowed_tools is None:
        return get_contract_allowed_tools(requested_profiles)
    return {str(x).strip().lower() for x in allowed_tools if str(x).strip()}


def validate_action_spec(spec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(spec, dict):
        return False, ['spec_not_object']

    action_type = str(spec.get('action_type') or DEFAULT_ACTION_TYPE).strip().lower()
    if action_type not in ACTION_TYPES:
        errors.append(f'invalid_action_type:{action_type}')

    capability = str(spec.get('capability') or ACTION_TYPE_TO_CAPABILITY.get(action_type) or '').strip().lower()
    if capability and capability not in CAPABILITIES:
        errors.append(f'invalid_capability:{capability}')

    requested_profiles = spec.get('resolved_planner_profiles')
    allowed_tools = _allowed_tools_set(get_planner_visible_tools(requested_profiles) if requested_profiles else None, requested_profiles=requested_profiles)

    tool = normalize_tool(spec.get('tool'))
    if not tool:
        if can_resolve_tool_from_capability(
            capability,
            action_type=action_type,
            task_family=str(spec.get('task_family') or ''),
            requested_profiles=requested_profiles,
        ):
            pass  # tool can be resolved later, so missing_tool is not an error
        else:
            errors.append('missing_tool')
    elif tool not in allowed_tools:
        errors.append(f'invalid_tool:{tool}')

    errors.extend(_validate_args(spec.get('args', [])))
    errors.extend(_validate_stdin(spec.get('stdin')))

    constraints = spec.get('constraints', {})
    if constraints is not None and not isinstance(constraints, dict):
        errors.append('constraints_must_be_object')

    tool_preferences = spec.get('tool_preferences', {})
    if tool_preferences is not None and not isinstance(tool_preferences, dict):
        errors.append('tool_preferences_must_be_object')
    elif isinstance(tool_preferences, dict):
        preferred_tool = normalize_tool(tool_preferences.get('prefer_tool')) if tool_preferences.get('prefer_tool') else ''
        if preferred_tool and preferred_tool not in allowed_tools:
            errors.append(f'invalid_prefer_tool:{preferred_tool}')

    tool_candidates = spec.get('tool_candidates', [])
    if isinstance(tool_candidates, list):
        for idx, candidate in enumerate(tool_candidates):
            c = normalize_tool(candidate)
            if not c:
                continue
            if c not in allowed_tools:
                errors.append(f'invalid_tool_candidate:{idx}:{c}')
    elif tool_candidates is not None:
        errors.append('tool_candidates_must_be_array')

    tool_chain = spec.get('tool_chain', [])
    if isinstance(tool_chain, list):
        for idx, step in enumerate(tool_chain):
            if not isinstance(step, dict):
                continue
            step_tool = normalize_tool(step.get('tool'))
            if not step_tool:
                errors.append(f'missing_tool_chain_tool:{idx}')
            elif step_tool not in allowed_tools:
                errors.append(f'invalid_tool_chain_tool:{idx}:{step_tool}')
            if 'args' in step:
                errors.extend(_validate_args(step.get('args', []), prefix=f'tool_chain_{idx}_'))
            errors.extend(_validate_stdin(step.get('stdin'), prefix=f'tool_chain_{idx}_'))
    elif tool_chain is not None:
        errors.append('tool_chain_must_be_array')

    errors.extend(validate_probe_recipe(spec))
    errors.extend(validate_action_contract_v2(spec))

    planner_alignment = str(spec.get('planner_alignment') or '').strip().lower()
    if planner_alignment and planner_alignment not in ALLOWED_BRAIN_ALIGNMENT:
        errors.append(f'invalid_planner_alignment:{planner_alignment}')

    redundancy_risk = str(spec.get('redundancy_risk') or '').strip().lower()
    if redundancy_risk not in ALLOWED_REDUNDANCY_RISK:
        errors.append(f'invalid_redundancy_risk:{redundancy_risk}')

    for key in ['hypothesis', 'why_now', 'planner_override_reason', 'expected_signal', 'evidence_goal', 'next_if_positive', 'next_if_negative']:
        value = spec.get(key)
        if value is not None and not isinstance(value, str):
            errors.append(f'{key}_must_be_string')
        elif isinstance(value, str) and len(value) > 500:
            errors.append(f'{key}_too_long')

    return len(errors) == 0, errors


def validate_auditor_payload(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(payload, dict):
        return False, ['auditor_payload_not_object']

    decision = str(payload.get('decision') or '').strip().lower()
    if decision not in ALLOWED_AUDITOR_DECISIONS:
        errors.append(f'invalid_decision:{decision}')

    reason_code = str(payload.get('reason_code') or '').strip().lower()
    if reason_code and reason_code not in ALLOWED_AUDITOR_REASON_CODES:
        errors.append(f'invalid_reason_code:{reason_code}')

    risk_band = str(payload.get('risk_band') or '').strip().lower()
    if risk_band and risk_band not in ALLOWED_RISK_BANDS:
        errors.append(f'invalid_risk_band:{risk_band}')

    owner_gate = payload.get('owner_gate')
    if owner_gate is not None and not isinstance(owner_gate, bool):
        errors.append('owner_gate_must_be_bool')

    constraints = payload.get('constraints', {})
    if constraints is not None and not isinstance(constraints, dict):
        errors.append('constraints_must_be_object')

    reason = payload.get('reason')
    if reason is not None and not isinstance(reason, str):
        errors.append('reason_must_be_string')

    return len(errors) == 0, errors
