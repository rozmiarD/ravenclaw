from __future__ import annotations

from typing import Any, Dict


def derive_family_state(*, analysis_contract: dict | None, promising: bool, host_state_band: str = '') -> str:
    ac = analysis_contract if isinstance(analysis_contract, dict) else {}
    if str(host_state_band or '').lower() in {'degraded', 'noisy'}:
        return 'suppressed'
    if str(ac.get('evidence_goal_met') or '') == 'yes':
        return 'confirming'
    if str(ac.get('expected_signal_observed') or '') == 'partial':
        return 'signal_found'
    if str(ac.get('hypothesis_support') or '') == 'weakened':
        return 'dead_end'
    if promising:
        return 'exploring'
    return 'untested'


def derive_host_stage(*, promising: bool, family_state: str, host_state_band: str = '') -> str:
    band = str(host_state_band or '').lower()
    if band in {'degraded', 'noisy'}:
        return 'degraded'
    if band == 'exploitation':
        return 'exploitation'
    if family_state == 'confirming':
        return 'confirmation'
    if family_state == 'signal_found':
        return 'validation'
    if promising:
        return 'promising'
    return 'profiling'


def derive_campaign_stage(*, runs: list[dict]) -> str:
    recent = [r for r in (runs or []) if isinstance(r, dict)]
    if not recent:
        return 'seeded'
    if any(str((r.get('analysis_contract') or {}).get('evidence_goal_met') or '') == 'yes' for r in recent[-8:]):
        return 'confirmation_phase'
    if any(bool(r.get('promising', False)) for r in recent[-8:]):
        return 'signal_validation'
    return 'active_discovery'
