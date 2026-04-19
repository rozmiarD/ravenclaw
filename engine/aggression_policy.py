from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import re

from paths import WORKSPACE

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

POLICY_PATH = WORKSPACE / 'policy.yaml'


def _safe_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except Exception:
        return fallback


def _load_with_regex_fallback(text: str) -> Dict[str, int]:
    default = {'min_level': 1, 'max_level': 10, 'default_level': 6}
    # very small fallback parser for policy.yaml aggression section
    block = re.search(r"(?ms)^aggression:\s*(.*?)^(?:\S|\Z)", text + "\nX")
    section = block.group(1) if block else text
    mn = _safe_int(re.search(r"min_level:\s*(\d+)", section).group(1), default['min_level']) if re.search(r"min_level:\s*(\d+)", section) else default['min_level']
    mx = _safe_int(re.search(r"max_level:\s*(\d+)", section).group(1), default['max_level']) if re.search(r"max_level:\s*(\d+)", section) else default['max_level']
    df = _safe_int(re.search(r"default_level:\s*(\d+)", section).group(1), default['default_level']) if re.search(r"default_level:\s*(\d+)", section) else default['default_level']
    if mn > mx:
        mn, mx = mx, mn
    if df < mn:
        df = mn
    if df > mx:
        df = mx
    return {'min_level': mn, 'max_level': mx, 'default_level': df}


def load_aggression_policy() -> Dict[str, int]:
    default = {'min_level': 1, 'max_level': 10, 'default_level': 6}
    try:
        if not POLICY_PATH.exists():
            return default
        text = POLICY_PATH.read_text(encoding='utf-8')
        if yaml is not None:
            data = yaml.safe_load(text) or {}
            aggr = data.get('aggression', {}) if isinstance(data, dict) else {}
            mn = _safe_int(aggr.get('min_level'), default['min_level'])
            mx = _safe_int(aggr.get('max_level'), default['max_level'])
            df = _safe_int(aggr.get('default_level'), default['default_level'])
            if mn > mx:
                mn, mx = mx, mn
            if df < mn:
                df = mn
            if df > mx:
                df = mx
            return {'min_level': mn, 'max_level': mx, 'default_level': df}
        return _load_with_regex_fallback(text)
    except Exception:
        return default


def clamp_aggression(level: int | None) -> int:
    p = load_aggression_policy()
    if level is None:
        return p['default_level']
    try:
        value = int(level)
    except Exception:
        value = p['default_level']
    if value < p['min_level']:
        return p['min_level']
    if value > p['max_level']:
        return p['max_level']
    return value


def derive_profile_from_scope(parsed: Dict[str, Any], base_default: int | None = None) -> Dict[str, Any]:
    p = load_aggression_policy()
    mn, mx = p['min_level'], p['max_level']
    default = clamp_aggression(base_default if base_default is not None else p['default_level'])

    allow = set((parsed or {}).get('allow_keywords') or [])
    deny = set((parsed or {}).get('deny_keywords') or [])
    domain_count = len((parsed or {}).get('domains') or [])

    # deterministic heuristics
    if deny:
        default = max(mn, default - 1)
    if {'xss', 'idor', 'csrf', 'open redirect'} & allow:
        default = min(mx, default + 1)
    if domain_count > 40:
        default = max(mn, default - 1)

    rec_min = max(mn, default - 1)
    rec_max = min(mx, default + 2)
    if rec_min > rec_max:
        rec_min = rec_max

    rationale = []
    if deny:
        rationale.append('deny_keywords_present')
    if {'xss', 'idor', 'csrf', 'open redirect'} & allow:
        rationale.append('safe_web_vectors_allowed')
    if domain_count > 40:
        rationale.append('large_scope_reduce_default')
    if not rationale:
        rationale.append('policy_default')

    return {
        'policy_min': mn,
        'policy_max': mx,
        'recommended_min': rec_min,
        'recommended_default': default,
        'recommended_max': rec_max,
        'confidence': 0.72,
        'rationale': rationale,
    }
