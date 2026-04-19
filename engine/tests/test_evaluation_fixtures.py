from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from evaluation_bundle import build_replay_bundle  # type: ignore
from evaluation_fixtures import evaluate_fixture_corpus, validate_replay_fixture  # type: ignore


def _run() -> dict:
    return {
        'index': 1,
        'objective': 'Map stateful auth flow',
        'target': 'https://app.example.com/checkout',
        'task_family': 'workflow',
        'auditor_decision': 'approve',
        'engine_status': 'ok',
        'signal_contract': {
            'execution_anomaly': {'status': 'none'},
            'workflow_promotion': {'status': 'candidate', 'verdict': 'weak_signal'},
            'finding_signal': {'status': 'weak'},
            'success_outcome': {'status': 'partial'},
            'adaptation_feedback': {'status': 'positive'},
        },
        'decision_selected_action': 'followup',
        'decision_effective_action': 'followup',
        'decision_effective_status': 'applied',
        'decision_intent_flags': {'followup': True},
        'decision_flags': {'followup': True},
        'runtime_task': {
            'session_requirements': {'requires_state': True},
        },
        'planning_ladder': {'current_stage': 'state_transition_confirmation', 'next_stage': 'bounded_exploit_proof'},
    }


def test_validate_replay_fixture_passes_for_matching_expectations() -> None:
    fixture = {
        'schema_version': 'phase5-replay-fixture-v1',
        'fixture_id': 'workflow-followup',
        'bundle': build_replay_bundle(_run()),
        'expected': {
            'status': 'ok',
            'requested_action': 'followup',
            'effective_action': 'followup',
            'candidate': True,
            'evidence_class': 'evidence_bearing',
            'semantic_outcome_class': 'weak_evidence',
            'state_prereq_missing': True,
        },
    }
    result = validate_replay_fixture(fixture)
    assert result['passed'] is True


def test_evaluate_fixture_corpus_reports_failures() -> None:
    good = {
        'schema_version': 'phase5-replay-fixture-v1',
        'fixture_id': 'good',
        'bundle': build_replay_bundle(_run()),
        'expected': {'requested_action': 'followup'},
    }
    bad = {
        'schema_version': 'phase5-replay-fixture-v1',
        'fixture_id': 'bad',
        'bundle': build_replay_bundle(_run()),
        'expected': {'requested_action': 'confirm'},
    }
    corpus = evaluate_fixture_corpus([good, bad])
    assert corpus['total'] == 2
    assert corpus['passed'] == 1
    assert corpus['failed'] == 1
