#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
ENGINE_DIR = WORKSPACE / 'engine'
LOGDASH_DIR = WORKSPACE / 'logdash'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(LOGDASH_DIR) not in sys.path:
    sys.path.insert(0, str(LOGDASH_DIR))

from runtime_state_schemas import normalize_campaign_settings  # type: ignore
from state import build_initial_state  # type: ignore

SYSTEM_SETTINGS = LOGDASH_DIR / 'templates' / 'system_settings.html'
CAMPAIGN_SETUP = LOGDASH_DIR / 'templates' / 'campaign_setup.html'

REQUIRED_IDS = {
    'requestDecorationMode',
    'requestDecorationHeaders',
    'requestDecorationCookies',
    'requestDecorationBasicUser',
    'requestDecorationBasicPass',
    'requestDecorationNotes',
}


def main() -> int:
    normalized = normalize_campaign_settings({'global': {}, 'by_campaign': {}})
    rd = normalized.get('global', {}).get('request_decoration', {})
    expected_keys = {'mode', 'headers', 'cookies', 'basic_auth', 'provenance_notes'}
    missing_schema = sorted(expected_keys - set(rd.keys()))
    default_state = build_initial_state()
    default_rd = default_state.get('request_decoration', {}) if isinstance(default_state, dict) else {}
    missing_state = sorted(expected_keys - set(default_rd.keys()))

    system_html = SYSTEM_SETTINGS.read_text(encoding='utf-8', errors='ignore') if SYSTEM_SETTINGS.exists() else ''
    campaign_html = CAMPAIGN_SETUP.read_text(encoding='utf-8', errors='ignore') if CAMPAIGN_SETUP.exists() else ''
    missing_system = sorted(x for x in REQUIRED_IDS if x not in system_html)
    missing_campaign = sorted(x for x in REQUIRED_IDS if x not in campaign_html)

    print(
        ' '.join([
            f'schema_missing={len(missing_schema)}',
            f'state_missing={len(missing_state)}',
            f'system_ui_missing={len(missing_system)}',
            f'campaign_ui_missing={len(missing_campaign)}',
        ])
    )
    if missing_schema:
        print('SCHEMA_MISSING:', ', '.join(missing_schema))
        return 2
    if missing_state:
        print('STATE_MISSING:', ', '.join(missing_state))
        return 3
    if missing_system:
        print('SYSTEM_UI_MISSING:', ', '.join(missing_system))
        return 4
    if missing_campaign:
        print('CAMPAIGN_UI_MISSING:', ', '.join(missing_campaign))
        return 5
    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
