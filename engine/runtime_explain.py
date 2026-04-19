from __future__ import annotations

from typing import Any, Dict


def build_compact_explain(
    *,
    why: list[str],
    blockers: list[str],
    inputs: Dict[str, Any],
    scores: Dict[str, Any],
    flags: Dict[str, bool],
) -> Dict[str, Any]:
    return {
        'decision': dict(flags),
        'why': list(why or []),
        'blockers': list(blockers or []),
        'inputs': dict(inputs or {}),
        'scores': dict(scores or {}),
        'summary': _summary(flags, why, blockers),
    }


def _summary(flags: Dict[str, bool], why: list[str], blockers: list[str]) -> str:
    active = [k for k, v in (flags or {}).items() if v]
    if active:
        lead = 'selected=' + ','.join(active)
    else:
        lead = 'selected=none'
    why_part = (';why=' + ','.join((why or [])[:3])) if why else ''
    block_part = (';blockers=' + ','.join((blockers or [])[:3])) if blockers else ''
    return lead + why_part + block_part
