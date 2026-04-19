from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import run_pipeline as rp  # type: ignore
from runtime_agent_io import truncate_prompt_for_budget  # type: ignore


def _args() -> argparse.Namespace:
    return argparse.Namespace(
        objective='Confirm whether unauthenticated state transitions leak cross-account order or profile data using minimal bounded probes',
        target='https://www.tradepmr.com/',
        aggression=4,
        task_success_criteria='confirmed differential tied to actor/session boundary',
        campaign_success_criteria='reportable authz or workflow issue',
        task_family='authz',
        acceptance_checks='cross-actor differential, stable reproduction, non-destructive',
        evidence_required='response diff, state transition evidence, bounded proof',
    )


def test_build_brain_base_prompt_preserves_critical_markers_under_budget() -> None:
    prompt = rp.build_brain_base_prompt(
        args=_args(),
        task_family='authz',
        contextual_profiles=['core', 'extended'],
        allowed_tools_sorted=['curl', 'httpx', 'ffuf', 'nuclei', 'katana', 'whatweb', 'dnsx', 'dig'],
        preferred_tools=['curl', 'httpx', 'ffuf'],
        planner_hints={
            'preferred_vectors_for_target': ['authz', 'workflow', 'logic'],
            'ambiguities': ['unknown auth state', 'possible multi-actor boundary'],
            'interpretation_conflicts': ['redirect may hide state transition'],
            'target_profile': {'task_family_seeds': ['authz', 'logic'], 'notes': ['stateful flow likely']},
            'task_family_context': {'authz': ['boundary differential', 'cross-account access']},
        },
        intent_runtime_context={
            'experiment_intent_id': 'intent-123',
            'capability_candidates': ['http_probe', 'differential_http', 'state_transition'],
            'recommended_action_types': ['differential_probe', 'state_transition_probe'],
            'hypothesis_candidates': ['cross-account order leak', 'profile boundary leak'],
            'open_questions': ['does state transition require auth?', 'is actor asymmetry observable?'],
            'planner_constraints': {'max_variants': 2},
            'planner_preferences': {'prefer_tool': 'curl'},
            'planning_ladder': {'current_stage': 'state_transition_confirmation', 'next_stage': 'bounded_exploit_proof'},
            'target_surface_rationale': ['actor_asymmetry', 'authenticated_or_boundary_mapping'],
        },
        experimental_mode=True,
    )
    truncated = truncate_prompt_for_budget(prompt, 900)
    for marker in ['EXPERIMENTAL MODE ON', 'TaskTruth:', 'ExperimentIntentContext:', 'PlannerHints:', 'VectorFamilyMotifs:', 'ExploitMotifs:', 'ToolingSummary:', 'forbidden: exec/execute/shell/command/cmd/echo/cat/ls/bash/python3']:
        assert marker in truncated
    assert 'sibling_hypotheses' in rp.build_brain_contract_hint()


def test_compaction_helpers_reduce_prompt_bloat() -> None:
    planner_hints = {
        'preferred_vectors_for_target': ['a', 'b', 'c', 'd', 'e'],
        'deprioritized_task_families': ['x', 'y', 'z'],
        'ambiguities': ['a1', 'a2', 'a3'],
        'interpretation_conflicts': ['c1', 'c2', 'c3'],
        'task_family_context': {'authz': ['one', 'two', 'three', 'four', 'five']},
        'target_profile': {'task_family_seeds': ['authz', 'logic', 'workflow', 'recon', 'content_discovery'], 'preferred_vectors_for_target': ['v1', 'v2', 'v3', 'v4'], 'notes': ['n1', 'n2', 'n3']},
    }
    compact_hints = rp.compact_planner_hints_for_brain(planner_hints)
    assert len(compact_hints['preferred_vectors_for_target']) == 3
    assert len(compact_hints['deprioritized_task_families']) == 2
    assert len(compact_hints['ambiguities']) == 2

    intent = {
        'experiment_intent_id': 'intent-123',
        'capability_candidates': ['a', 'b', 'c', 'd', 'e'],
        'recommended_action_types': ['x', 'y', 'z', 'w', 'q'],
        'hypothesis_candidates': ['h1', 'h2', 'h3', 'h4'],
        'open_questions': ['q1', 'q2', 'q3', 'q4'],
        'planner_constraints': {'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5', 'f': '6'},
        'planner_preferences': {'prefer_tool': 'curl', 'another': 'httpx'},
        'planning_ladder': {'current_stage': 'state_transition_confirmation', 'next_stage': 'bounded_exploit_proof'},
        'target_surface_rationale': ['r1', 'r2', 'r3', 'r4', 'r5'],
    }
    compact_intent = rp.compact_intent_runtime_context_for_brain(intent)
    assert len(compact_intent['capability_candidates']) == 4
    assert len(compact_intent['recommended_action_types']) == 4
    assert len(compact_intent['hypothesis_candidates']) == 3
    assert len(compact_intent['open_questions']) == 3


def test_brain_contract_hint_is_compact_and_not_tool_enum_heavy() -> None:
    contract_hint = rp.build_brain_contract_hint()
    assert 'optional_planner_allowed_tool' in contract_hint
    assert 'sibling_hypotheses' in contract_hint
    assert 'curl|httpx|ffuf' not in contract_hint
    assert len(contract_hint) < 1600
