from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from contracts import remap_aggression_for_policy, sanitize_action_spec, sanitize_action_spec_auth_modes, validate_action_spec  # type: ignore
from action_compiler import compile_action_spec  # type: ignore


def test_validate_action_spec_allows_capability_resolved_tool_and_rejects_invalid_prefer_tool() -> None:
    ok, errors = validate_action_spec({
        'action_type': 'differential_probe',
        'capability': 'http_probe',
        'task_family': 'authz',
        'tool': '',
        'tool_preferences': {'prefer_tool': 'bash'},
        'args': ['https://api.example.com/'],
        'probe_recipe': {'comparison_mode': 'header_status', 'variant_count': 2, 'evidence_goal': 'compare'},
    })
    assert ok is False
    assert 'missing_tool' not in errors
    assert 'invalid_prefer_tool:bash' in errors


def test_compile_action_spec_resolves_tool_from_capability_recipe() -> None:
    compiled = compile_action_spec({
        'action_type': 'variant_probe',
        'capability': 'http_probe',
        'task_family': 'authz',
        'probe_recipe': {'variant_count': 2},
        'tool_preferences': {'prefer_tool': 'curl'},
    })
    assert compiled['tool'] == 'curl'
    assert compiled['compiler_tool_choice_source'] in {'preferred_tool', 'capability_recipe'}


def test_sanitize_action_spec_trims_shell_like_arg_fragments() -> None:
    sanitized, notes = sanitize_action_spec({
        'action_type': 'enumeration_probe',
        'tool': 'katana',
        'args': ['-u', 'https://www.opposhop.cn/ | grep admin', '-jc'],
    })
    assert sanitized['args'] == ['-u', 'https://www.opposhop.cn/', '-jc']
    assert notes
    assert notes[0]['action'] == 'trimmed_arg'
    assert notes[0]['token'] == '|'


def test_sanitize_action_spec_drops_pure_shell_operator_args() -> None:
    sanitized, notes = sanitize_action_spec({
        'action_type': 'enumeration_probe',
        'tool': 'katana',
        'args': ['-u', '|', 'https://www.opposhop.cn/'],
    })
    assert sanitized['args'] == ['-u', 'https://www.opposhop.cn/']
    assert any(note['action'] == 'dropped_arg' for note in notes)


def test_sanitize_action_spec_trims_shell_like_tool_chain_arg_fragments() -> None:
    sanitized, notes = sanitize_action_spec({
        'action_type': 'confirmatory_probe',
        'tool': 'curl',
        'args': ['https://target.example/'],
        'tool_chain': [
            {'tool': 'curl', 'args': ['-H', 'X-Test: ok', 'https://target.example/']},
            {'tool': 'katana', 'args': ['-u', 'https://target.example/ | grep admin', '-jc']},
        ],
    })
    assert sanitized['tool_chain'][1]['args'] == ['-u', 'https://target.example/', '-jc']
    assert any(note['path'] == 'tool_chain[1].args[1]' for note in notes)


def test_validate_action_spec_still_rejects_remaining_shell_operator_args() -> None:
    ok, errors = validate_action_spec({
        'action_type': 'enumeration_probe',
        'tool': 'katana',
        'args': ['-u', 'https://www.opposhop.cn/ && cat /etc/passwd'],
        'probe_recipe': {'variant_count': 1},
    })
    assert ok is False
    assert any(err.startswith('arg_contains_shell_operator') for err in errors)


def test_sanitize_action_spec_auth_modes_strips_basic_auth_flags_when_policy_forbids_it() -> None:
    sanitized, notes = sanitize_action_spec_auth_modes(
        {
            'action_type': 'enumeration_probe',
            'tool': 'curl',
            'args': ['-u', 'user:pass', '-H', 'X-HackerOne-Research: researcher-example', 'https://target.example/'],
        },
        {'allow_basic_auth': False},
    )
    assert sanitized['args'] == ['-H', 'X-HackerOne-Research: researcher-example', 'https://target.example/']
    assert any(note['action'] == 'dropped_basic_auth_flag' for note in notes)


def test_sanitize_action_spec_auth_modes_strips_basic_auth_from_tool_chain_when_policy_forbids_it() -> None:
    sanitized, notes = sanitize_action_spec_auth_modes(
        {
            'action_type': 'confirmatory_probe',
            'tool': 'curl',
            'args': ['https://target.example/'],
            'tool_chain': [
                {'tool': 'httpx', 'args': ['--auth', 'user', 'pass', '-H', 'X-HackerOne-Research: researcher-example', 'https://target.example/']},
            ],
        },
        {'allow_basic_auth': False},
    )
    assert sanitized['tool_chain'][0]['args'] == ['-H', 'X-HackerOne-Research: researcher-example', 'https://target.example/']
    assert any(note['path'] == 'tool_chain[0].args[0]' for note in notes)


def test_sanitize_action_spec_auth_modes_preserves_basic_auth_when_policy_allows_it() -> None:
    original = {
        'action_type': 'enumeration_probe',
        'tool': 'curl',
        'args': ['-u', 'user:pass', 'https://target.example/'],
    }
    sanitized, notes = sanitize_action_spec_auth_modes(original, {'allow_basic_auth': True})
    assert sanitized == original
    assert notes == []


def test_remap_aggression_for_policy_caps_credentialed_crawler_enumeration() -> None:
    new_aggr, note = remap_aggression_for_policy(
        {
            'tool': 'katana',
            'action_type': 'enumeration_probe',
            'task_family': 'content_discovery',
        },
        {
            'request_decoration': {
                'mode': 'campaign_required',
                'headers': [{'name': 'X-HackerOne-Research', 'value': 'researcher-example'}],
                'cookies': [],
                'basic_auth': {'enabled': False, 'username': '', 'password': ''},
            },
        },
        4,
    )
    assert new_aggr == 3
    assert note
    assert note['reason'] == 'credentialed_crawler_policy_cap'


def test_remap_aggression_for_policy_is_noop_without_credentialed_request_shape() -> None:
    new_aggr, note = remap_aggression_for_policy(
        {
            'tool': 'katana',
            'action_type': 'enumeration_probe',
            'task_family': 'content_discovery',
        },
        {
            'request_decoration': {
                'mode': 'none',
                'headers': [],
                'cookies': [],
                'basic_auth': {'enabled': False, 'username': '', 'password': ''},
            },
        },
        4,
    )
    assert new_aggr == 4
    assert note is None
