from __future__ import annotations

from typing import Any, Dict, List

from security_action_schema import ACTION_TYPE_TO_CAPABILITY, ACTION_TYPE_TO_EXPERIMENT_SHAPE, DEFAULT_ACTION_TYPE, DEFAULT_CAPABILITY  # type: ignore
from security_capability_recipes import build_named_recipe_execution_plan, resolve_action_tooling  # type: ignore
from security_policy_core import normalize_tool  # type: ignore
from security_semantic_loss_policy import classify_semantic_loss  # type: ignore


def _normalize_chain_step(step: Dict[str, Any], fallback_tool: str) -> Dict[str, Any]:
    tool = normalize_tool(step.get('tool')) or fallback_tool
    out = {
        'tool': tool,
        'args': [str(a) for a in (step.get('args', []) or [])],
        'role': str(step.get('role') or 'probe').strip().lower() or 'probe',
    }
    stdin_text = str(step.get('stdin') or '')
    if stdin_text:
        out['stdin'] = stdin_text
    return out


def _finalize_semantic_policy(compiled: Dict[str, Any]) -> Dict[str, Any]:
    compiled['semantic_loss_policy'] = classify_semantic_loss(compiled, task_family=str(compiled.get('task_family') or ''))
    return compiled


def compile_action_spec(action_spec: Dict[str, Any]) -> Dict[str, Any]:
    spec = dict(action_spec or {})
    action_type = str(spec.get('action_type') or DEFAULT_ACTION_TYPE).strip().lower()
    capability = str(spec.get('capability') or ACTION_TYPE_TO_CAPABILITY.get(action_type) or DEFAULT_CAPABILITY).strip().lower()
    recipe = spec.get('probe_recipe', {}) if isinstance(spec.get('probe_recipe'), dict) else {}
    recipe_name = str(spec.get('recipe_name') or recipe.get('recipe_name') or '').strip().lower()
    execution_mode = str(spec.get('execution_mode') or 'normalized').strip().lower() or 'normalized'
    args = [str(a) for a in (spec.get('args', []) or [])]
    stdin_text = str(spec.get('stdin') or '')
    preferred_tool = normalize_tool(((spec.get('tool_preferences') or {}) if isinstance(spec.get('tool_preferences'), dict) else {}).get('prefer_tool'))
    tool_candidates = [normalize_tool(x) for x in (spec.get('tool_candidates', []) or []) if normalize_tool(x)]
    resolution = resolve_action_tooling(spec)
    tool = normalize_tool(spec.get('tool')) or normalize_tool(resolution.get('selected_tool'))
    tool_chain_raw = spec.get('tool_chain', []) if isinstance(spec.get('tool_chain'), list) else []

    execution_plan: List[Dict[str, Any]] = []
    if tool_chain_raw:
        if not tool:
            raise ValueError(f'missing_tool_for_action_type:{action_type}')
        execution_plan = [_normalize_chain_step(step, tool) for step in tool_chain_raw if isinstance(step, dict)]
        if execution_plan and execution_plan[0]['tool'] != tool:
            execution_plan.insert(0, {'tool': tool, 'args': args, 'role': 'probe'})
    elif recipe_name:
        execution_plan = build_named_recipe_execution_plan(spec, recipe_name, requested_profiles=resolution.get('profiles') or None)
        if execution_plan:
            tool = normalize_tool(execution_plan[0].get('tool')) or tool
    else:
        if not tool:
            raise ValueError(f'missing_tool_for_action_type:{action_type}')
        probe_step: Dict[str, Any] = {'tool': tool, 'args': args, 'role': 'probe'}
        if stdin_text:
            probe_step['stdin'] = stdin_text
        execution_plan = [probe_step]

    if not tool:
        raise ValueError(f'missing_tool_for_action_type:{action_type}')

    resolved_candidates = [normalize_tool(x) for x in (resolution.get('candidate_tools') or []) if normalize_tool(x)]
    compiled: Dict[str, Any] = {
        'action_type': action_type,
        'capability': capability,
        'recipe_name': recipe_name,
        'execution_mode': execution_mode,
        'experiment_shape': str(spec.get('experiment_shape') or ACTION_TYPE_TO_EXPERIMENT_SHAPE.get(action_type) or 'single_step').strip().lower() or 'single_step',
        'target_cardinality': str(spec.get('target_cardinality') or 'single').strip().lower() or 'single',
        'compiler_strategy': 'recipe_lowering' if recipe_name else 'passthrough',
        'compiler_tool_choice': tool,
        'compiler_tool_choice_source': str(resolution.get('resolution_source') or ('explicit_tool' if normalize_tool(spec.get('tool')) else 'unknown')),
        'compiler_variant_count': int(recipe.get('variant_count', 1) or 1),
        'semantic_loss_detected': False,
        'normalization_reason': f'recipe:{recipe_name}' if recipe_name else '',
        'tool': tool,
        'preferred_tool': preferred_tool or tool,
        'tool_candidates': tool_candidates or resolved_candidates,
        'resolved_planner_profiles': list(resolution.get('profiles') or []),
        'tool_chain': execution_plan,
        'execution_plan': execution_plan,
        'args': args,
        'stdin': stdin_text,
        'target': str(spec.get('target') or ''),
        'task_family': str(spec.get('task_family') or ''),
    }

    if action_type == 'single_probe':
        return _finalize_semantic_policy(compiled)

    if action_type == 'fingerprint_probe':
        compiled['semantic_loss_detected'] = True
        compiled['normalization_reason'] = 'fingerprint_probe_lowered_to_single_probe'
        return _finalize_semantic_policy(compiled)

    if action_type == 'enumeration_probe':
        compiled['compiler_strategy'] = 'enumeration_lowering'
        return _finalize_semantic_policy(compiled)

    if action_type == 'differential_probe':
        comparison_mode = str(recipe.get('comparison_mode') or 'header_status').strip().lower()
        compiled['compiler_strategy'] = 'differential_lowering'
        compiled['semantic_loss_detected'] = False
        compiled['normalization_reason'] = f'comparison_mode:{comparison_mode}'
        return _finalize_semantic_policy(compiled)

    if action_type == 'confirmatory_probe':
        compiled['compiler_strategy'] = 'confirmatory_lowering'
        return _finalize_semantic_policy(compiled)

    if action_type == 'variant_probe':
        compiled['compiler_strategy'] = 'variant_lowering'
        return _finalize_semantic_policy(compiled)

    if action_type == 'state_transition_probe':
        compiled['compiler_strategy'] = 'state_transition_lowering'
        return _finalize_semantic_policy(compiled)

    compiled['semantic_loss_detected'] = True
    compiled['normalization_reason'] = 'unknown_action_type_lowered_to_passthrough'
    return _finalize_semantic_policy(compiled)
