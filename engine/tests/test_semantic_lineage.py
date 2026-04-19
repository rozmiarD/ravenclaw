from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from semantic_lineage import build_semantic_lineage, summarize_semantic_lineage  # type: ignore


def test_build_semantic_lineage_emits_hashes_and_preserves_stage() -> None:
    lineage = build_semantic_lineage(
        task={
            'target': 'https://api.example.com/',
            'objective': 'Probe authz boundary',
            'task_family': 'authz',
            'planner_input_source': 'experiment_intent_canonical',
            'planner_field_ownership': {'runtime_task_contract': True},
            'planner_rationale': {
                'experiment_intent_id': 'intent-authz-1',
                'target_profile_summary': {'target_type': 'api'},
                'target_surface_rationale': ['authenticated_or_boundary_mapping'],
                'recommended_progression': ['authenticated_or_boundary_mapping', 'control_boundary_confirmation', 'bounded_exploit_proof'],
            },
            'planning_ladder': {'current_stage': 'control_boundary_confirmation', 'next_stage': 'bounded_exploit_proof'},
        },
        runtime_task={
            'experiment_intent_id': 'intent-authz-1',
            'action_type': 'differential_probe',
            'capability': 'http_probe',
            'experiment_shape': 'differential',
            'evidence_goal': 'controlled_comparison',
            'exploit_ladder': {'stage': 'control_boundary_confirmation'},
            'promotion_policy': {'confirm_preferred': True},
        },
        source='test',
    )
    assert lineage['planner_contract']['planning_ladder']['current_stage'] == 'control_boundary_confirmation'
    assert lineage['runtime_contract']['action_type'] == 'differential_probe'
    assert lineage['artifact_boundaries']['planner_contract_sha256']
    assert lineage['artifact_boundaries']['runtime_contract_sha256']
    assert lineage['artifact_boundaries']['lineage_sha256']
    summary = summarize_semantic_lineage(lineage)
    assert summary['current_stage'] == 'control_boundary_confirmation'
    assert summary['lineage_sha256'] == lineage['artifact_boundaries']['lineage_sha256']
