from __future__ import annotations

import sys
import time
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_health_policy import apply_transport_cooldowns  # type: ignore


def test_apply_transport_cooldowns_uses_configured_403_threshold_and_cooldown() -> None:
    host_cooldown_until = {}
    host_code000_streak = {}
    host_code000_total = {}
    host_403_streak = {'api.example.com': 1}

    apply_transport_cooldowns(
        summary_text='HTTP 403 observed on control path',
        host='api.example.com',
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        code000_streak_threshold=3,
        code000_session_cap=5,
        code000_cooldown_sec=3600,
        transport_observation_cooldown_sec=120,
        http_403_streak_threshold=2,
        http_403_cooldown_sec=900,
    )
    assert host_403_streak['api.example.com'] == 2
    assert 850 <= (host_cooldown_until['api.example.com'] - time.time()) <= 900.5


def test_apply_transport_cooldowns_uses_configured_code000_session_cooldown() -> None:
    host_cooldown_until = {}
    host_code000_streak = {'api.example.com': 1}
    host_code000_total = {'api.example.com': 4}
    host_403_streak = {}

    apply_transport_cooldowns(
        summary_text='__RC_METRICS__ code=000 transport failure',
        host='api.example.com',
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        code000_streak_threshold=3,
        code000_session_cap=5,
        code000_cooldown_sec=3600,
        code000_session_cooldown_sec=43200,
    )
    assert host_code000_streak['api.example.com'] == 2
    assert host_code000_total['api.example.com'] == 5
    assert 43150 <= (host_cooldown_until['api.example.com'] - time.time()) <= 43200.5
