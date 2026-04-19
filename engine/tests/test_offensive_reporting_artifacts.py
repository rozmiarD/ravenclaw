from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import offensive_reporting_artifacts as ora  # type: ignore


def _strong_vector() -> dict:
    return {
        'index': 1,
        'objective': 'Confirm cross-account order leak',
        'target': 'https://api.example.com/v1/orders/42',
        'promising': True,
        'signal_contract': {
            'workflow_promotion': {'status': 'confirmable'},
            'finding_signal': {'status': 'strong'},
            'success_outcome': {'status': 'partial'},
            'adaptation_feedback': {'status': 'positive'},
        },
        'engine_compiler': {'semantic_loss_policy': {'loss_class': 'bounded_lowering'}},
        'execution_gate': {'status': 'passed'},
        'brain_reasoning_summary': {
            'action_type': 'state_transition_probe',
            'capability': 'state_transition',
            'sibling_hypotheses': [
                {'hypothesis': 'actor asymmetry variant'},
                {'hypothesis': 'header context variant'},
            ],
        },
        'analysis_contract': {
            'primary_hypothesis': 'cross-account order leak via state transition replay',
            'open_questions': ['does actor B observe the same state?', 'is replay stable?'],
            'actor_or_session_prerequisites': ['two user sessions', 'stable object id'],
        },
        'semantic_lineage_summary': {'lineage_sha256': 'lineage-strong-001'},
        'runtime_task': {
            'acceptance_checks': ['stable reproduction', 'cross-actor differential'],
            'semantic_lineage': {
                'planner_contract': {
                    'task_family': 'authz',
                    'planning_ladder': {
                        'current_stage': 'state_transition_confirmation',
                        'next_stage': 'bounded_exploit_proof',
                    },
                    'target_surface_rationale': ['actor_asymmetry'],
                }
            },
        },
        'success_semantics': {'typed_family_eval': 'authz_boundary'},
    }


def _weak_vector() -> dict:
    return {
        'index': 2,
        'objective': 'Generic probe',
        'target': 'https://api.example.com/health',
        'promising': False,
        'signal_contract': {
            'workflow_promotion': {'status': 'none'},
            'finding_signal': {'status': 'weak'},
            'success_outcome': {'status': 'none'},
            'adaptation_feedback': {'status': 'none'},
        },
        'execution_gate': {'status': 'passed'},
        'brain_reasoning_summary': {'action_type': 'single_probe', 'capability': 'http_probe'},
        'analysis_contract': {},
        'semantic_lineage_summary': {'lineage_sha256': 'lineage-weak-001'},
        'runtime_task': {
            'semantic_lineage': {
                'planner_contract': {
                    'task_family': 'recon',
                    'planning_ladder': {'current_stage': 'recon', 'next_stage': 'enumeration'},
                }
            }
        },
    }


def test_build_proof_bundles_keeps_structured_pending_direction() -> None:
    branch_campaignlets = ora.build_branch_campaignlets([_strong_vector(), _weak_vector()])
    proof_bundles = ora.build_proof_bundles([_strong_vector(), _weak_vector()], branch_campaignlets)

    assert branch_campaignlets['count'] == 1
    assert proof_bundles['schema_version'] == 'proof-bundles-v1'
    assert proof_bundles['count'] == 1

    bundle = proof_bundles['items'][0]
    assert bundle['task_family'] == 'authz'
    assert bundle['current_stage'] == 'state_transition_confirmation'
    assert bundle['next_stage'] == 'bounded_exploit_proof'
    assert bundle['pending_proof_direction'] == 'bounded_exploit_proof'
    assert bundle['signal_status']['workflow'] == 'confirmable'
    assert bundle['signal_status']['finding'] == 'strong'
    assert bundle['actor_or_session_prerequisites'] == ['two user sessions', 'stable object id']
    assert bundle['acceptance_checks'] == ['stable reproduction', 'cross-actor differential']
    assert bundle['persistence_score'] >= 0.7


def test_persist_runtime_state_artifacts_writes_canonical_and_local_state(tmp_path: Path, monkeypatch) -> None:
    reports_dir = tmp_path / 'reports'
    canonical_state_dir = tmp_path / 'canonical-state'
    monkeypatch.setattr(ora, 'rsp', lambda *parts: canonical_state_dir.joinpath(*parts))

    payload = {'schema_version': 'proof-bundles-v1', 'count': 1, 'items': [{'lineage_sha256': 'abc123'}]}
    ora.persist_runtime_state_artifacts(
        reports_dir=reports_dir,
        artifacts={'proof-bundles.json': payload},
    )

    canonical = canonical_state_dir / 'proof-bundles.json'
    local_state = tmp_path / 'state' / 'proof-bundles.json'
    assert canonical.exists()
    assert local_state.exists()
    assert json.loads(canonical.read_text(encoding='utf-8')) == payload
    assert json.loads(local_state.read_text(encoding='utf-8')) == payload
