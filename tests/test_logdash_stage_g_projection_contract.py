from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import build_selected_campaign_projection, projection_source_label  # type: ignore


def test_build_selected_campaign_projection_prefers_snapshot_plan_counts() -> None:
    payload = build_selected_campaign_projection(
        {'runtime_plan': {'generated': 2, 'target_count': 1}},
        {
            'selected_campaign_key': 'alpha',
            'filtered_snapshot': {'campaign': {'campaign_key': 'alpha'}},
            'snapshot_matches_selected': True,
            'snap_campaign': {'executed': 3},
            'snap_plan': {'generated': 7, 'target_count': 5},
            'snap_latest': {'target': 'https://alpha.example.com/'},
            'snap_queues': {'followup_count': 2},
            'snap_telemetry': {'execution_gate_skip_total': 1},
            'snap_hosts': {'items': []},
            'snap_economics': {'family_efficiency': []},
        },
        {'prepared_attacks': 9, 'planner_scope_targets': 8},
    )
    assert payload['selected_campaign_key'] == 'alpha'
    assert payload['snapshot_matches_selected'] is True
    assert payload['generated'] == 7
    assert payload['target_count'] == 5
    assert payload['snapshot']['campaign']['campaign_key'] == 'alpha'
    assert payload['snap_queues']['followup_count'] == 2


def test_build_selected_campaign_projection_zeroes_counts_without_selected_campaign() -> None:
    payload = build_selected_campaign_projection(
        {'runtime_plan': {'generated': 4, 'target_count': 6}},
        {'selected_campaign_key': '', 'filtered_snapshot': {}, 'snapshot_matches_selected': False},
        {'prepared_attacks': 9, 'planner_scope_targets': 8},
    )
    assert payload['selected_campaign_key'] == ''
    assert payload['generated'] == 0
    assert payload['target_count'] == 0
    assert payload['snapshot'] == {}


def test_projection_source_label_tracks_snapshot_presence() -> None:
    assert projection_source_label(snapshot={'updated_at': 'ts'}, fallback='legacy') == 'snapshot'
    assert projection_source_label(snapshot={}, fallback='legacy_runtime_vectors') == 'legacy_runtime_vectors'
