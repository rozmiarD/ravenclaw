from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import policy_gateway as pg  # type: ignore


def test_normalize_policy_decision_v0_preserves_legacy_compatibility() -> None:
    out = pg.normalize_policy_decision_v0(
        {'pass': True, 'reason': 'ok'},
        target='https://example.com/',
        target_host='example.com',
        target_in_scope=True,
        resolved_tool='curl',
        action_type='single_probe',
        constraints={'aggression': 3},
    )
    assert out['schema_version'] == '2026-04-27.policy-decision.v0.1'
    assert out['decision'] == 'allow_prepare'
    assert out['reason_code'] == 'ok'
    assert out['compatibility'] == {'pass': True, 'reason': 'ok'}
    assert out['scope_facts']['target_host'] == 'example.com'
    assert out['tool_facts']['resolved_tool'] == 'curl'
    assert out['constraints']['aggression'] == 3
    assert out['redaction_required'] is True


def test_normalize_policy_decision_v0_marks_owner_gate() -> None:
    out = pg.normalize_policy_decision_v0(
        {'pass': False, 'reason': 'action_type_requires_owner_gate:state_transition_probe'},
        action_type='state_transition_probe',
    )
    assert out['decision'] == 'owner_approval_required'
    assert out['approval_required'] is True
    assert out['compatibility']['pass'] is False


def test_policy_gateway_blocks_state_transition_without_owner_gate(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec({'action_type': 'state_transition_probe', 'tool': 'curl', 'args': ['https://api.example.com/'], 'probe_recipe': {'sequence_steps': ['a', 'b']}}, 'https://api.example.com/', False, creds={})
    assert out['pass'] is False
    assert out['reason'].startswith('action_type_requires_owner_gate')


def test_policy_gateway_allows_enumeration_probe_when_valid(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec({'action_type': 'enumeration_probe', 'tool': 'katana', 'args': ['-u', 'https://api.example.com/'], 'probe_recipe': {}}, 'https://api.example.com/', False, creds={})
    assert out['pass'] is True


def test_policy_gateway_rejects_restricted_tool_patterns(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'enumeration_probe', 'tool': 'curl', 'args': ['--output', 'body.txt', 'https://api.example.com/'], 'probe_recipe': {}},
        'https://api.example.com/',
        False,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'tool_restricted_pattern:curl:--output'


def test_policy_gateway_rejects_katana_proxy_pattern(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'enumeration_probe', 'tool': 'katana', 'args': ['-u', 'https://api.example.com/', '-proxy', 'http://127.0.0.1:8080'], 'probe_recipe': {}},
        'https://api.example.com/',
        False,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'tool_restricted_pattern:katana:-proxy'


def test_policy_gateway_rejects_subfinder_config_pattern(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'enumeration_probe', 'tool': 'subfinder', 'args': ['-config', '/tmp/subfinder.yaml', '-d', 'example.com'], 'probe_recipe': {}},
        'https://example.com/',
        False,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'tool_restricted_pattern:subfinder:-config'


def test_policy_gateway_rejects_gau_url_target_kind(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'enumeration_probe', 'tool': 'gau', 'args': ['https://example.com'], 'probe_recipe': {}},
        'https://example.com/',
        False,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'invalid_target_kind:gau:url'


def test_policy_gateway_rejects_katana_missing_url_target_kind(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'enumeration_probe', 'tool': 'katana', 'args': ['example.com'], 'probe_recipe': {}},
        'https://example.com/',
        False,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'missing_target_kind:katana:url'


def test_policy_gateway_rejects_tool_chain_target_kind_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {
            'action_type': 'state_transition_probe',
            'tool': 'curl',
            'args': ['https://example.com/login'],
            'tool_chain': [
                {'tool': 'curl', 'role': 'probe', 'args': ['https://example.com/login']},
                {'tool': 'gau', 'role': 'validate', 'args': ['https://example.com/account']},
            ],
            'probe_recipe': {'sequence_steps': ['login', 'validate']},
        },
        'https://example.com/',
        True,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'tool_chain_1:invalid_target_kind:gau:url'


def test_policy_gateway_allows_hakrawler_stdin_url_target(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'enumeration_probe', 'tool': 'hakrawler', 'args': ['-d', '2', '-u'], 'stdin': 'https://example.com/app\n', 'probe_recipe': {}},
        'https://example.com/',
        False,
        creds={},
    )
    assert out['pass'] is True


def test_policy_gateway_rejects_hakrawler_missing_stdin_url_target(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: True)
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'enumeration_probe', 'tool': 'hakrawler', 'args': ['-d', '2', '-u'], 'probe_recipe': {}},
        'https://example.com/',
        False,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'missing_target_kind:hakrawler:url'


def test_policy_gateway_rejects_out_of_scope_host_hidden_in_header_value(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: host == 'example.com')
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'single_probe', 'tool': 'curl', 'args': ['-H', 'Host: evil.com', 'https://example.com/'], 'probe_recipe': {}},
        'https://example.com/',
        False,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'out_of_scope_target:evil.com'


def test_policy_gateway_rejects_out_of_scope_stdin_target_for_tool_chain_step(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: host == 'example.com')
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {
            'action_type': 'state_transition_probe',
            'tool': 'curl',
            'args': ['https://example.com/login'],
            'tool_chain': [
                {'tool': 'curl', 'role': 'probe', 'args': ['https://example.com/login']},
                {'tool': 'hakrawler', 'role': 'validate', 'args': ['-d', '2', '-u'], 'stdin': 'https://evil.com/app\n'},
            ],
            'probe_recipe': {'sequence_steps': ['login', 'crawl']},
        },
        'https://example.com/',
        True,
        creds={},
    )
    assert out['pass'] is False
    assert out['reason'] == 'tool_chain_1:out_of_scope_target:evil.com'


def test_policy_gateway_ignores_file_uri_when_checking_scope_tokens(monkeypatch) -> None:
    monkeypatch.setattr(pg, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(pg, 'host_in_scope', lambda host, scope_domains: host == 'example.com')
    monkeypatch.setattr(pg, 'check_credentials_policy', lambda args, creds, owner_approved_auth, tool: (True, 'ok'))
    out = pg.evaluate_action_spec(
        {'action_type': 'single_probe', 'tool': 'curl', 'args': ['file:///tmp/first.txt'], 'probe_recipe': {}},
        'https://example.com/',
        False,
        creds={},
    )
    assert out['pass'] is True
