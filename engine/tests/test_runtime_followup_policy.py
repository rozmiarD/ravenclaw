from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_followup_policy as rfp  # type: ignore


def test_policy_next_followup_family_keeps_progressive_mapping_without_result() -> None:
    assert rfp.next_followup_family('recon', host_from_target_fn=lambda target: target) == 'historical_url_mining'
    assert rfp.next_followup_family('historical_url_mining', host_from_target_fn=lambda target: target) == 'content_discovery'
    assert rfp.next_followup_family('auth_flow', host_from_target_fn=lambda target: target) == 'authz'



def test_policy_next_followup_family_uses_injected_host_resolver_and_progression_hint() -> None:
    captured = {}

    def fake_host_from_target(target: str) -> str:
        captured['target'] = target
        return 'portal.example.com'

    def fake_top_progression_hints(**kwargs):  # type: ignore[no-untyped-def]
        captured['progression_kwargs'] = dict(kwargs)
        return [{'next_family': 'authz'}]

    out = rfp.next_followup_family(
        'recon',
        {
            'target': 'https://portal.example.com/',
            'planning_ladder': {'next_stage': 'control_boundary_confirmation'},
            'planner_rationale': {'target_profile_summary': {'target_type': 'web'}},
        },
        host_from_target_fn=fake_host_from_target,
        top_progression_hints_fn=fake_top_progression_hints,
    )

    assert out == 'authz'
    assert captured['target'] == 'https://portal.example.com/'
    assert captured['progression_kwargs']['family'] == 'recon'
    assert captured['progression_kwargs']['target_type'] == 'web'
    assert captured['progression_kwargs']['next_stage'] == 'control_boundary_confirmation'



def test_attach_adaptive_followup_explainability_is_noop_for_non_dict_result() -> None:
    rfp.attach_adaptive_followup_explainability(
        result=None,
        inferred={'primary_archetype': 'auth_heavy', 'archetypes': ['auth_heavy'], 'confidence': 1.2, 'flags': {'auth_heavy': True}},
        planner_feedback={'dead_end_pressure_recent': 0.8},
        selected_family='authz',
        current_family='recon',
        next_stage='bounded_exploit_proof',
        target_type='api',
        target_surface_rationale=['authenticated_or_boundary_mapping'],
    )
