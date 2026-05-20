from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.runtime_shell import validate_control_action, validate_queue_snapshot, validate_runtime_snapshot  # type: ignore
from govengine_state_control_projection import (  # type: ignore
    build_control_decision_projection,
    build_gov_queue_snapshot_projection,
    build_gov_run_state_projection,
    build_gov_runtime_snapshot_projection,
)


def test_run_state_projection_uses_govengine_0_3_runtime_states() -> None:
    projection = build_gov_run_state_projection(
        runtime_campaign_state={'state': 'running', 'owner_override': True, 'updated_at': '2026-05-20T10:00:00+00:00'},
        selected_campaign_key='camp-alpha',
        runtime_snapshot={'campaign': {'campaign_key': 'camp-alpha', 'run_id': 'run-alpha'}},
        process_alive=True,
    )

    assert projection['run_id'] == 'run-alpha'
    assert projection['state'] == 'running'
    assert projection['profile'] == 'ravenclaw-security'
    assert projection['metadata']['ravenclaw_runtime_state'] == 'running'
    assert projection['metadata']['selected_campaign_key'] == 'camp-alpha'
    assert projection['projection_gaps'] == []


def test_stopped_runtime_is_projected_without_govengine_0_2_gap() -> None:
    projection = build_gov_run_state_projection(
        runtime_campaign_state={'state': 'stopped'},
        selected_campaign_key='camp-alpha',
    )

    assert projection['state'] == 'stopped'
    assert projection['projection_gaps'] == []


def test_queue_snapshot_projection_redacts_targets_and_commands() -> None:
    projection = build_gov_queue_snapshot_projection(
        queue_state={
            'source': 'runtime_snapshot',
            'followup_queue': [
                {
                    'target': 'https://sensitive.example/',
                    'task_family': 'recon',
                    'priority_score': 7,
                    'runtime_task': {'capability_lane': 'http'},
                }
            ],
            'precision_queue': [],
            'execution_gate_skip_count': {'warmup_gate_skip': 2},
        }
    )

    lanes = {lane['name']: lane for lane in projection['lanes']}
    preview = lanes['followup']['preview'][0]

    validate_queue_snapshot(projection)
    assert lanes['followup']['count'] == 1
    assert preview['has_target'] is True
    assert preview['target_redacted'] is True
    assert 'https://sensitive.example/' not in str(projection)
    assert projection['metadata']['command_values_in_preview'] is False


def test_runtime_snapshot_projection_combines_state_plan_queue_and_sources() -> None:
    projection = build_gov_runtime_snapshot_projection(
        selected_campaign_key='camp-alpha',
        runtime_state={
            'auto_campaign': {'state': 'running', 'updated_at': 'auto-ts'},
            'runtime_plan': {'plan_revision': 4, 'plan_hash': 'abc123', 'generated': 8, 'target_count': 2},
            'snapshot': {
                'campaign': {'campaign_key': 'camp-alpha', 'executed': 3, 'max_runs': 10, 'updated_at': 'snap-ts'},
                'latest_run': {'target': 'https://example.com/', 'decision_effective_status': 'blocked'},
            },
            'sources': {'snapshot': 'normalized_snapshot_file'},
        },
        queue_state={'followup_queue': [], 'precision_queue': []},
    )

    validate_runtime_snapshot(projection)
    assert projection['plan_summary']['generated'] == 8
    assert projection['run_summary']['executed'] == 3
    assert projection['queue_summary']['run_id'] == projection['run_id']
    assert projection['latest_transition']['target_present'] is True
    assert 'does_not_claim_govengine_scheduler_ownership' in projection['non_claims']


def test_pause_control_projection_is_a_valid_govengine_control_decision() -> None:
    state = build_gov_run_state_projection(runtime_campaign_state={'state': 'running'}, selected_campaign_key='camp-alpha')

    projection = build_control_decision_projection(action='pause', run_state_projection=state)
    action = validate_control_action(projection['control_action'])

    assert projection['projection_gaps'] == []
    assert action.action == 'pause'
    assert action.requested_state == 'paused'


def test_start_and_stop_control_actions_are_first_class_govengine_0_3_actions() -> None:
    state = build_gov_run_state_projection(runtime_campaign_state={'state': 'idle'}, selected_campaign_key='camp-alpha')

    start = build_control_decision_projection(action='start', run_state_projection=state)
    stop = build_control_decision_projection(action='stop', run_state_projection=state)

    assert validate_control_action(start['control_action']).action == 'start'
    assert validate_control_action(start['control_action']).requested_state == 'running'
    assert validate_control_action(stop['control_action']).action == 'stop'
    assert validate_control_action(stop['control_action']).requested_state == 'stopped'
    assert start['projection_gaps'] == []
    assert stop['projection_gaps'] == []
