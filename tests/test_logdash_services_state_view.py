from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import selected_runtime_snapshot_view  # type: ignore


def test_selected_runtime_snapshot_view_keeps_matching_snapshot_sections() -> None:
    runtime = {
        'snapshot': {
            'campaign': {'campaign_key': 'alpha', 'executed': 3},
            'plan': {'generated': 9},
            'latest_run': {'target': 'https://alpha.example.com/'},
            'queues': {'followup_count': 2},
            'telemetry': {'execution_gate_skip_total': 4},
            'hosts': {'items': [{'host': 'alpha.example.com'}]},
            'economics': {'confirm_conversion_rate': 0.5},
        }
    }
    view = selected_runtime_snapshot_view(runtime, 'alpha')
    assert view['snapshot_matches_selected'] is True
    assert view['snap_campaign']['campaign_key'] == 'alpha'
    assert view['snap_plan']['generated'] == 9
    assert view['snap_latest']['target'] == 'https://alpha.example.com/'
    assert view['snap_hosts']['items'][0]['host'] == 'alpha.example.com'
    assert view['snap_economics']['confirm_conversion_rate'] == 0.5
    assert view['filtered_snapshot']['queues']['followup_count'] == 2
    assert view['filtered_snapshot']['telemetry']['execution_gate_skip_total'] == 4
    assert view['filtered_snapshot']['hosts']['items'][0]['host'] == 'alpha.example.com'
    assert view['filtered_snapshot']['economics']['confirm_conversion_rate'] == 0.5


def test_selected_runtime_snapshot_view_clears_mismatched_snapshot_sections() -> None:
    runtime = {
        'snapshot': {
            'campaign': {'campaign_key': 'beta', 'executed': 7},
            'plan': {'generated': 12},
            'latest_run': {'target': 'https://beta.example.com/'},
            'queues': {'followup_count': 5},
            'telemetry': {'execution_gate_skip_total': 8},
            'hosts': {'items': [{'host': 'beta.example.com'}]},
            'economics': {'confirm_conversion_rate': 0.9},
        }
    }
    view = selected_runtime_snapshot_view(runtime, 'alpha')
    assert view['snapshot_matches_selected'] is False
    assert view['snap_campaign'] == {}
    assert view['snap_plan'] == {}
    assert view['snap_latest'] == {}
    assert view['snap_hosts'] == {}
    assert view['snap_economics'] == {}
    assert view['filtered_snapshot']['campaign'] == {}
    assert view['filtered_snapshot']['plan'] == {}
    assert view['filtered_snapshot']['latest_run'] == {}
    assert view['filtered_snapshot']['queues'] == {}
    assert view['filtered_snapshot']['telemetry'] == {}
    assert view['filtered_snapshot']['hosts'] == {}
    assert view['filtered_snapshot']['economics'] == {}
