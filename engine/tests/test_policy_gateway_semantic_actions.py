from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import policy_gateway as pg  # type: ignore


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
