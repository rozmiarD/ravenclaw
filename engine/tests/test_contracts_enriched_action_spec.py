from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from contracts import validate_action_spec  # type: ignore


def test_validate_action_spec_accepts_enriched_brain_fields() -> None:
    ok, errors = validate_action_spec({
        'action_type': 'confirmatory_probe',
        'tool': 'curl',
        'args': ['-I', 'https://api.example.com/'],
        'probe_recipe': {'evidence_goal': 'Confirm authz response delta.', 'variant_count': 2},
        'constraints': {'aggression': 3},
        'hypothesis': 'Header variance may expose auth boundary asymmetry.',
        'why_now': 'Recent partial signal suggests a low-noise confirmation probe.',
        'planner_alignment': 'aligned',
        'planner_override_reason': '',
        'expected_signal': 'Differential status/header behavior.',
        'evidence_goal': 'Confirm authz response delta.',
        'next_if_positive': 'Pivot to controlled authz variant.',
        'next_if_negative': 'Return to recon or logic family.',
        'redundancy_risk': 'low',
    })
    assert ok is True
    assert errors == []


def test_validate_action_spec_rejects_invalid_alignment_and_redundancy() -> None:
    ok, errors = validate_action_spec({
        'action_type': 'variant_probe',
        'tool': 'curl',
        'args': ['https://api.example.com/'],
        'probe_recipe': {'variant_count': 9},
        'planner_alignment': 'random',
        'redundancy_risk': 'very_high',
    })
    assert ok is False
    assert 'invalid_planner_alignment:random' in errors
    assert 'invalid_redundancy_risk:very_high' in errors
    assert any(e.startswith('variant_count_out_of_range') for e in errors)


def test_validate_action_spec_accepts_capability_first_resolution_when_tool_is_omitted() -> None:
    ok, errors = validate_action_spec({
        'action_type': 'state_transition_probe',
        'capability': 'http_probe',
        'task_family': 'authz',
        'args': ['https://api.example.com/login'],
        'probe_recipe': {'sequence_steps': ['login', 'account'], 'evidence_goal': 'state transition'},
    })
    assert ok is True
    assert errors == []
