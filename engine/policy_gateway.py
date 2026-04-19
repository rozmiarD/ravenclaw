from __future__ import annotations

from typing import Any, Dict, List

from campaign_utils import extract_host_from_url, host_in_scope, load_scope_domains  # type: ignore
from policy_core import get_runtime_allowed_tools, contains_banned_patterns, normalize_tool, check_credentials_policy  # type: ignore
from action_compiler import compile_action_spec  # type: ignore
from action_validators import validate_probe_recipe, validate_action_contract_v2  # type: ignore
from action_schema import DEFAULT_ACTION_TYPE  # type: ignore


def _chain_steps(brain: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = brain.get('tool_chain', []) if isinstance(brain.get('tool_chain'), list) else []
    return [step for step in steps if isinstance(step, dict)]


def _compiled_chain_steps(compiled: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = compiled.get('execution_plan', []) if isinstance(compiled.get('execution_plan'), list) else []
    return [step for step in steps if isinstance(step, dict)]


def evaluate_action_spec(brain: Dict[str, Any], target: str, owner_approved_auth: bool, creds: Dict[str, Any] | None = None) -> Dict[str, Any]:
    action_type = str(brain.get('action_type') or DEFAULT_ACTION_TYPE).strip().lower()
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
        creds_ok, creds_reason = check_credentials_policy(step_args, creds, owner_approved_auth, step_tool)
        if not creds_ok:
            return {'pass': False, 'reason': f'tool_chain_{idx}:{creds_reason}'}

    return {'pass': True, 'reason': 'ok'}
