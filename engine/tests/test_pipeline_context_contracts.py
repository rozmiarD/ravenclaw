from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from pipeline_context import _merge_intent_runtime_context  # type: ignore



def test_merge_intent_runtime_context_preserves_expanded_planner_runtime_fields() -> None:
    args = argparse.Namespace(
        experiment_intent_id='intent-authz-1',
        capability_candidates_json='["http_probe"]',
        recommended_action_types_json='["differential_probe"]',
        hypothesis_candidates_json='["idor on https://api.example.com/"]',
        open_questions_json='["tenant edge on https://api.example.com/"]',
        planner_constraints_json='{"campaign_bound_context": true}',
        planner_preferences_json='{"preferred_vector_families": ["authz"]}',
        planner_rationale_json='{"target_surface_rationale": ["authenticated_or_boundary_mapping"], "recommended_progression": ["control_boundary_confirmation"], "target_profile_summary": {"target_type": "api"}}',
        planning_ladder_json='{"current_stage": "control_boundary_confirmation", "next_stage": "bounded_exploit_proof"}',
        target_surface_rationale_json='["authenticated_or_boundary_mapping"]',
        recommended_progression_json='["control_boundary_confirmation"]',
        semantic_lineage_json='{"lineage_sha256": "abc", "stage": "control_boundary_confirmation"}',
        semantic_lineage_summary_json='{"summary": "boundary confirmation lineage"}',
    )

    merged = _merge_intent_runtime_context(args, {'target_profile': {'host': 'api.example.com'}}, target='https://api.example.com/')

    assert merged['experiment_intent_id'] == 'intent-authz-1'
    assert merged['capability_candidates'] == ['http_probe']
    assert merged['recommended_action_types'] == ['differential_probe']
    assert merged['planner_constraints']['campaign_bound_context'] is True
    assert merged['planner_constraints']['target_host_binding'] == 'api.example.com'
    assert merged['planner_preferences'] == {'preferred_vector_families': ['authz']}
    assert merged['planner_rationale']['target_surface_rationale'] == ['authenticated_or_boundary_mapping']
    assert merged['planner_rationale']['recommended_progression'] == ['control_boundary_confirmation']
    assert merged['planning_ladder']['next_stage'] == 'bounded_exploit_proof'
    assert merged['target_surface_rationale'] == ['authenticated_or_boundary_mapping']
    assert merged['recommended_progression'] == ['control_boundary_confirmation']
    assert merged['semantic_lineage']['lineage_sha256'] == 'abc'
    assert merged['semantic_lineage_summary']['summary'] == 'boundary confirmation lineage'
