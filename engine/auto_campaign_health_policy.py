from __future__ import annotations

from datetime import datetime, timezone


def apply_transport_cooldowns(
    *,
    summary_text: str,
    host: str,
    host_cooldown_until: dict[str, float],
    host_code000_streak: dict[str, int],
    host_code000_total: dict[str, int],
    host_403_streak: dict[str, int],
    code000_streak_threshold: int,
    code000_session_cap: int,
    code000_cooldown_sec: int,
    transport_observation_cooldown_sec: int = 600,
    http_403_streak_threshold: int = 4,
    http_403_cooldown_sec: int = 1800,
    code000_session_cooldown_sec: int = 86400,
) -> None:
    sh = host
    if not sh:
        return
    low = (summary_text or '').lower()
    now = datetime.now(timezone.utc).timestamp()
    transport_observation_cooldown_sec = max(60, int(transport_observation_cooldown_sec or 600))
    http_403_streak_threshold = max(1, int(http_403_streak_threshold or 4))
    http_403_cooldown_sec = max(60, int(http_403_cooldown_sec or 1800))
    code000_session_cooldown_sec = max(300, int(code000_session_cooldown_sec or 86400))

    if 'http 403' in low or '__rc_metrics__ code=403' in low or '__rc_metrics__ code=000' in low:
        host_cooldown_until[sh] = now + transport_observation_cooldown_sec

    if '__rc_metrics__ code=000' in low or 'code=000' in low:
        host_code000_streak[sh] = host_code000_streak.get(sh, 0) + 1
        host_code000_total[sh] = host_code000_total.get(sh, 0) + 1
        if host_code000_streak[sh] >= code000_streak_threshold:
            host_cooldown_until[sh] = now + code000_cooldown_sec
        if host_code000_total[sh] >= code000_session_cap:
            host_cooldown_until[sh] = now + code000_session_cooldown_sec
    else:
        host_code000_streak[sh] = 0

    if '__rc_metrics__ code=403' in low or 'http 403' in low:
        host_403_streak[sh] = host_403_streak.get(sh, 0) + 1
        if host_403_streak[sh] >= http_403_streak_threshold:
            host_cooldown_until[sh] = now + http_403_cooldown_sec
    else:
        host_403_streak[sh] = 0
