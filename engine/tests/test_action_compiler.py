from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from action_compiler import compile_action_spec  # type: ignore


def test_compile_action_spec_preserves_differential_probe_semantics() -> None:
    compiled = compile_action_spec({
        'action_type': 'differential_probe',
        'target': 'https://api.example.com/',
        'tool': 'curl',
        'args': ['-I', 'https://api.example.com/'],
        'probe_recipe': {'comparison_mode': 'header_status', 'variant_count': 2},
    })
    assert compiled['action_type'] == 'differential_probe'
    assert compiled['compiler_strategy'] == 'differential_lowering'
    assert compiled['compiler_variant_count'] == 2


def test_compile_action_spec_allows_variant_and_state_transition_types() -> None:
    variant = compile_action_spec({'action_type': 'variant_probe', 'tool': 'curl', 'tool_preferences': {'prefer_tool': 'curl'}, 'probe_recipe': {'variant_count': 3}})
    state = compile_action_spec({'action_type': 'state_transition_probe', 'tool': 'curl', 'probe_recipe': {'sequence_steps': ['a', 'b']}})
    assert variant['compiler_strategy'] == 'variant_lowering'
    assert state['compiler_strategy'] == 'state_transition_lowering'


def test_compile_action_spec_resolves_tool_from_preference_without_explicit_tool() -> None:
    compiled = compile_action_spec({
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'task_family': 'recon',
        'tool_preferences': {'prefer_tool': 'curl'},
        'args': ['https://example.com/'],
    })
    assert compiled['compiler_tool_choice'] == 'curl'
    assert compiled['tool'] == 'curl'


def test_compile_action_spec_builds_named_recipe_execution_plan() -> None:
    compiled = compile_action_spec({
        'action_type': 'enumeration_probe',
        'capability': 'historical_url_collection',
        'task_family': 'historical_url_mining',
        'target': 'https://example.com',
        'probe_recipe': {'recipe_name': 'historical_then_validate', 'variant_count': 2},
    })
    assert compiled['recipe_name'] == 'historical_then_validate'
    assert len(compiled['execution_plan']) == 2
    assert compiled['execution_plan'][0]['tool'] == 'gau'
    assert compiled['execution_plan'][1]['args'][-1] == '{prev_stdout_path}'
    assert compiled['semantic_loss_policy']['loss_class'] == 'bounded_lowering'
    assert compiled['semantic_loss_policy']['policy_response'] == 'proceed_mark_degraded'


def test_compile_action_spec_marks_fingerprint_lowering_for_auditor_rereview() -> None:
    compiled = compile_action_spec({
        'action_type': 'fingerprint_probe',
        'capability': 'http_probe',
        'task_family': 'recon',
        'tool': 'curl',
        'args': ['-I', 'https://example.com'],
    })
    assert compiled['semantic_loss_detected'] is True
    assert compiled['semantic_loss_policy']['loss_class'] == 'degraded_semantics'
    assert compiled['semantic_loss_policy']['policy_response'] == 'auditor_rereview'
    assert compiled['experiment_shape'] == 'fingerprint'


def test_compile_action_spec_marks_unknown_action_as_required_replan() -> None:
    compiled = compile_action_spec({
        'action_type': 'mystery_probe',
        'capability': 'http_probe',
        'task_family': 'authz',
        'tool': 'curl',
        'args': ['-I', 'https://example.com'],
    })
    assert compiled['semantic_loss_detected'] is True
    assert compiled['semantic_loss_policy']['loss_class'] == 'unacceptable_flattening'
    assert compiled['semantic_loss_policy']['policy_response'] == 'required_replan'
