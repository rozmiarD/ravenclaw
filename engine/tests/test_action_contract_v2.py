from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import security_policy_gateway as pg
from security_action_compiler import compile_action_spec
from contracts import validate_action_spec  # type: ignore
from security_policy_gateway import evaluate_action_spec


def test_validate_action_spec_accepts_v2_fields_and_infers_capability_when_missing() -> None:
    ok, errors = validate_action_spec({
        'action_type': 'state_transition_probe',
        'tool': 'curl',
        'tool_candidates': ['curl', 'httpx'],
        'tool_chain': [
            {'tool': 'curl', 'role': 'probe', 'args': ['https://example.com/login']},
            {'tool': 'curl', 'role': 'validate', 'args': ['https://example.com/account']},
        ],
        'experiment_shape': 'bounded_chain',
        'target_cardinality': 'single',
        'probe_recipe': {'sequence_steps': ['login', 'account'], 'evidence_goal': 'state transition'},
        'args': ['https://example.com/login'],
    })
    assert ok is True, errors


def test_compile_action_spec_preserves_execution_plan_and_candidates() -> None:
    compiled = compile_action_spec({
        'action_type': 'differential_probe',
        'capability': 'http_probe',
        'tool': 'curl',
        'tool_candidates': ['curl', 'httpx'],
        'tool_chain': [
            {'tool': 'curl', 'role': 'probe', 'args': ['https://example.com/a']},
            {'tool': 'curl', 'role': 'validate', 'args': ['https://example.com/b']},
        ],
        'probe_recipe': {'comparison_mode': 'header_status', 'variant_count': 2, 'evidence_goal': 'compare'},
        'args': ['https://example.com/a'],
    })
    assert compiled['capability'] == 'http_probe'
    assert compiled['tool_candidates'] == ['curl', 'httpx']
    assert len(compiled['execution_plan']) == 2
    assert compiled['execution_plan'][1]['role'] == 'validate'


def test_policy_gateway_validates_tool_chain_steps(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []})
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    res = evaluate_action_spec(
        {
            'action_type': 'single_probe',
            'capability': 'http_probe',
            'tool': 'curl',
            'args': ['https://example.com/'],
            'tool_chain': [
                {'tool': 'curl', 'role': 'probe', 'args': ['https://example.com/']},
                {'tool': 'curl', 'role': 'validate', 'args': ['https://example.com/ok && whoami']},
            ],
        },
        'https://example.com/',
        False,
        {},
    )
    assert res['pass'] is False
    assert 'tool_chain_disallowed_pattern' in res['reason']


def test_policy_gateway_accepts_capability_first_when_compiler_can_resolve_tool(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []})
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    res = evaluate_action_spec(
        {
            'action_type': 'differential_probe',
            'capability': 'http_probe',
            'task_family': 'authz',
            'args': ['https://example.com/account'],
            'probe_recipe': {'comparison_mode': 'header_status', 'variant_count': 2, 'evidence_goal': 'compare'},
        },
        'https://example.com/account',
        False,
        {},
    )
    assert res['pass'] is True
    assert res['reason'] == 'ok'


def test_validate_action_spec_accepts_bounded_stdin_target_shape() -> None:
    ok, errors = validate_action_spec({
        'action_type': 'enumeration_probe',
        'capability': 'crawler_route_discovery',
        'tool': 'hakrawler',
        'args': ['-d', '2', '-u'],
        'stdin': 'https://example.com/app\n',
    })
    assert ok is True, errors


def test_validate_action_spec_rejects_non_string_or_oversized_stdin() -> None:
    ok1, errors1 = validate_action_spec({
        'action_type': 'enumeration_probe',
        'capability': 'crawler_route_discovery',
        'tool': 'hakrawler',
        'args': ['-d', '2', '-u'],
        'stdin': ['https://example.com/app'],
    })
    assert ok1 is False
    assert 'stdin_must_be_string' in errors1

    ok2, errors2 = validate_action_spec({
        'action_type': 'enumeration_probe',
        'capability': 'crawler_route_discovery',
        'tool': 'hakrawler',
        'args': ['-d', '2', '-u'],
        'tool_chain': [{'tool': 'hakrawler', 'role': 'probe', 'args': ['-d', '2', '-u'], 'stdin': ('https://example.com/app\n' * 40)}],
    })
    assert ok2 is False
    assert 'tool_chain_0_stdin_too_many_lines' in errors2
