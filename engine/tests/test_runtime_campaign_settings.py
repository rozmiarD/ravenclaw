from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_state_schemas import normalize_campaign_settings  # type: ignore


def test_normalize_campaign_settings_request_decoration_shape() -> None:
    out = normalize_campaign_settings({
        'global': {
            'request_decoration': {
                'headers': ['X-Canary: rc'],
                'cookies': ['session=abc'],
                'basic_auth': {'enabled': True, 'username': 'user', 'password': 'secret'},
                'provenance_notes': ['operator'],
            }
        },
        'by_campaign': {},
    })
    rd = out['global']['request_decoration']
    assert rd['headers'][0]['name'] == 'X-Canary'
    assert rd['headers'][0]['value'] == 'rc'
    assert rd['cookies'][0]['name'] == 'session'
    assert rd['cookies'][0]['value'] == 'abc'
    assert rd['basic_auth']['enabled'] is True
    assert rd['basic_auth']['username'] == 'user'
    assert rd['mode'] == 'operator_supplied'


def test_normalize_campaign_settings_budgets_and_retry_policy() -> None:
    out = normalize_campaign_settings({
        'global': {
            'max_runs': '20',
            'target_load_limit': '77',
            'time_budget_min': '15',
            'retry_policy': 'AGGRESSIVE',
            'aggression_override': '11',
            'aggression_effective': '0',
        },
        'by_campaign': {},
    })
    cfg = out['global']
    assert cfg['max_runs'] == 20
    assert cfg['target_load_limit'] == 77
    assert cfg['time_budget_min'] == 15
    assert cfg['retry_policy'] == 'aggressive'
    assert cfg['aggression_override'] == 10
    assert cfg['aggression_effective'] == 1
