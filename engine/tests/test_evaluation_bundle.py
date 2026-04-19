from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from evaluation_bundle import (  # type: ignore
    REPLAY_BUNDLE_SCHEMA_VERSION,
    build_replay_bundle,
    build_replay_dataset_from_summary,
    normalize_variant_ref,
    validate_replay_bundle,
)


def _run() -> dict:
    return {
        'index': 3,
        'objective': 'Confirm bounded exploit proof',
        'target': 'https://api.example.com/v1/users/123',
        'task_family': 'authz',
        'plan_name': 'AUTHZ-EXPLOIT',
        'mode': 'fast',
        'aggression': 4,
        'auditor_decision': 'approve',
        'engine_status': 'ok',
        'signal_contract': {
            'workflow_promotion': {'status': 'confirmable', 'verdict': 'confirmed'},
            'finding_signal': {'status': 'strong'},
            'success_outcome': {'status': 'partial'},
            'adaptation_feedback': {'status': 'positive'},
        },
        'decision_intent_flags': {'confirm': True},
        'decision_flags': {'confirm': True},
        'decision_effective_status': 'applied',
        'decision_selected_action': 'confirm',
        'decision_effective_action': 'confirm',
        'decision_economics': {'priority_score': 0.8},
        'runtime_task': {
            'action_type': 'differential_probe',
            'capability': 'http_probe',
            'session_requirements': {'requires_auth': True},
            'promotion_policy': {'confirm_preferred': True},
        },
        'planner_rationale': {
            'experiment_intent_id': 'intent-123',
            'target_surface_rationale': ['actor_asymmetry'],
        },
        'planning_ladder': {'current_stage': 'bounded_exploit_proof', 'next_stage': 'report_artifact_capture'},
        'analysis_contract': {'semantic_loss_class': 'none'},
        'engine_compiler': {'tool_chain': ['curl', 'jq']},
    }


def test_build_replay_bundle_sets_bundle_identity_and_variant() -> None:
    bundle = build_replay_bundle(_run(), run_id='run-1', campaign_key='camp-1', variant={'variant_id': 'baseline'})
    assert bundle['schema_version'] == REPLAY_BUNDLE_SCHEMA_VERSION
    assert bundle['bundle_id']
    assert bundle['run_identity']['run_id'] == 'run-1'
    assert bundle['run_identity']['campaign_key'] == 'camp-1'
    assert bundle['variant']['variant_id'] == 'baseline'
    assert bundle['governance']['request_count_estimate'] == 2
    validated = validate_replay_bundle(bundle)
    assert validated['runtime_decision']['requested_action'] == 'confirm'


def test_build_replay_dataset_from_summary_builds_stable_dataset() -> None:
    summary = {
        'run_id': 'run-1',
        'campaign_validation': {'campaign_key': 'camp-1'},
        'vectors': [_run()],
    }
    dataset = build_replay_dataset_from_summary(summary)
    assert dataset['schema_version'] == 'phase5-replay-dataset-v1'
    assert dataset['dataset_id']
    assert dataset['bundle_count'] == 1
    assert dataset['bundles'][0]['run_identity']['task_family'] == 'authz'


def test_normalize_variant_ref_applies_defaults() -> None:
    variant = normalize_variant_ref({'id': 'NEW-QUEUE'})
    assert variant['variant_id'] == 'new-queue'
    assert variant['metric_version'] == 'phase5-metrics-v1'
    assert variant['replay_version'] == 'phase5-replay-v1'
