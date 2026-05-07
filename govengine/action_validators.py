from __future__ import annotations

from typing import Any, Dict, List

from govengine.action_schema import (
    ACTION_TYPES,
    ALLOWED_CHAIN_ROLES,
    ALLOWED_EXPERIMENT_SHAPES,
    ALLOWED_TARGET_CARDINALITY,
    CHAIN_MAX_STEPS,
    DIFFERENTIAL_MAX_STEPS,
    ENUMERATION_VARIANT_MAX,
    SEQUENCE_MAX_STEPS,
    VARIANT_MAX_STEPS,
)
from govengine.tool_registry import get_capability_catalog


CAPABILITIES = set(get_capability_catalog())
STDIN_MAX_CHARS = 4096
STDIN_MAX_LINES = 32


def _validate_stdin_value(value: Any, *, prefix: str = '') -> List[str]:
    if value is None:
        return []
    label = prefix or ''
    if not isinstance(value, str):
        return [f'{label}stdin_must_be_string']
    if '\x00' in value:
        return [f'{label}stdin_contains_nul']
    errors: List[str] = []
    if len(value) > STDIN_MAX_CHARS:
        errors.append(f'{label}stdin_too_long')
    if len(value.splitlines()) > STDIN_MAX_LINES:
        errors.append(f'{label}stdin_too_many_lines')
    return errors


def validate_probe_recipe(spec: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    action_type = str(spec.get('action_type') or '').strip().lower()
    recipe = spec.get('probe_recipe', {})
    if recipe is not None and not isinstance(recipe, dict):
        return ['probe_recipe_must_be_object']
    recipe = recipe or {}

    if action_type == 'enumeration_probe':
        variant_count = int(recipe.get('variant_count', 1) or 1)
        if variant_count < 1 or variant_count > ENUMERATION_VARIANT_MAX:
            errors.append(f'enumeration_variant_count_out_of_range:{variant_count}')
    if action_type == 'differential_probe':
        comparison_mode = str(recipe.get('comparison_mode') or '').strip().lower()
        if not comparison_mode:
            errors.append('missing_comparison_mode')
        variant_count = int(recipe.get('variant_count', 1) or 1)
        if variant_count < 2 or variant_count > DIFFERENTIAL_MAX_STEPS:
            errors.append(f'differential_variant_count_out_of_range:{variant_count}')
    if action_type == 'confirmatory_probe':
        variant_count = int(recipe.get('variant_count', 1) or 1)
        if variant_count < 1 or variant_count > 2:
            errors.append(f'confirm_variant_count_out_of_range:{variant_count}')
    if action_type == 'variant_probe':
        variant_count = int(recipe.get('variant_count', 1) or 1)
        if variant_count < 2 or variant_count > VARIANT_MAX_STEPS:
            errors.append(f'variant_count_out_of_range:{variant_count}')
    if action_type == 'state_transition_probe':
        sequence_steps = recipe.get('sequence_steps', [])
        if not isinstance(sequence_steps, list) or len(sequence_steps) < 2:
            errors.append('state_transition_requires_sequence_steps')
        elif len(sequence_steps) > SEQUENCE_MAX_STEPS:
            errors.append(f'state_transition_sequence_too_long:{len(sequence_steps)}')
    if action_type == 'fingerprint_probe':
        variant_count = int(recipe.get('variant_count', 1) or 1)
        if variant_count < 1 or variant_count > 2:
            errors.append(f'fingerprint_variant_count_out_of_range:{variant_count}')

    evidence_goal = str(recipe.get('evidence_goal') or '').strip()
    if len(evidence_goal) > 240:
        errors.append('evidence_goal_too_long')

    return errors


def validate_action_contract_v2(spec: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    capability = str(spec.get('capability') or '').strip().lower()
    if capability and capability not in CAPABILITIES:
        errors.append(f'invalid_capability:{capability}')

    experiment_shape = str(spec.get('experiment_shape') or '').strip().lower()
    if experiment_shape and experiment_shape not in ALLOWED_EXPERIMENT_SHAPES:
        errors.append(f'invalid_experiment_shape:{experiment_shape}')

    target_cardinality = str(spec.get('target_cardinality') or '').strip().lower()
    if target_cardinality and target_cardinality not in ALLOWED_TARGET_CARDINALITY:
        errors.append(f'invalid_target_cardinality:{target_cardinality}')

    tool_candidates = spec.get('tool_candidates', [])
    if tool_candidates is not None and not isinstance(tool_candidates, list):
        errors.append('tool_candidates_must_be_array')
    elif isinstance(tool_candidates, list):
        if len(tool_candidates) > 4:
            errors.append('tool_candidates_too_many')
        for idx, candidate in enumerate(tool_candidates):
            if not isinstance(candidate, str) or not str(candidate).strip():
                errors.append(f'invalid_tool_candidate:{idx}')

    errors.extend(_validate_stdin_value(spec.get('stdin'), prefix=''))

    tool_chain = spec.get('tool_chain', [])
    if tool_chain is not None and not isinstance(tool_chain, list):
        errors.append('tool_chain_must_be_array')
    elif isinstance(tool_chain, list):
        if len(tool_chain) > CHAIN_MAX_STEPS:
            errors.append(f'tool_chain_too_long:{len(tool_chain)}')
        for idx, step in enumerate(tool_chain):
            if not isinstance(step, dict):
                errors.append(f'tool_chain_step_not_object:{idx}')
                continue
            role = str(step.get('role') or '').strip().lower()
            if role and role not in ALLOWED_CHAIN_ROLES:
                errors.append(f'invalid_tool_chain_role:{idx}:{role}')
            args = step.get('args', [])
            if args is not None and not isinstance(args, list):
                errors.append(f'tool_chain_args_must_be_array:{idx}')
            elif isinstance(args, list) and len(args) > 32:
                errors.append(f'tool_chain_args_too_long:{idx}')
            errors.extend(_validate_stdin_value(step.get('stdin'), prefix=f'tool_chain_{idx}_'))

    for key in ['capability', 'experiment_shape', 'rationale', 'expected_artifacts']:
        value = spec.get(key)
        if value is not None and not isinstance(value, str):
            errors.append(f'{key}_must_be_string')
        elif isinstance(value, str) and len(value) > 500:
            errors.append(f'{key}_too_long')

    return errors
