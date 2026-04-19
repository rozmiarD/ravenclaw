from __future__ import annotations

from pathlib import Path
import sys

from flask import Flask

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_supplemental import register_supplemental_api  # type: ignore
from services import build_campaign_info_payload, build_runtime_health_payload, build_selected_campaign_projection, projection_source_label, selected_runtime_snapshot_view  # type: ignore


def _build_app(tmp_path: Path, runtime: dict, host_state: dict | None = None) -> Flask:
    app = Flask(__name__)
    reports = tmp_path / 'reports'
    reports.mkdir(exist_ok=True)
    stdout_path = reports / 'runtime.stdout.log'
    stderr_path = reports / 'runtime.stderr.log'
    stdout_path.write_text('', encoding='utf-8')
    stderr_path.write_text('', encoding='utf-8')
    host_state_path = reports / 'host-state.json'
    host_state_path.write_text('{}', encoding='utf-8')

    register_supplemental_api(
        app,
        {
            'STATE': {'selected_campaign_name': 'Alpha', 'state': 'idle'},
            'STATUS_CLASSES': {},
            'fetch_logs': lambda page=1, per_page=500: ([], 0),
            'get_conn': lambda: None,
            'refresh_runtime_state': lambda: None,
            'load_runtime_state': lambda: runtime,
            'load_queue_state': lambda: {'followup_queue': [], 'precision_queue': [], 'source': 'runtime_snapshot'},
            'load_campaign_settings': lambda: {'global': {}, 'by_campaign': {}},
            'save_campaign_settings': lambda data: data,
            'load_pipeline_config': lambda: {},
            'save_pipeline_config': lambda data: data,
            'pipeline_config_meta': lambda: {},
            'load_latest_blueprint': lambda *args, **kwargs: None,
            'selected_campaign_key': lambda: 'alpha',
            '_list_campaign_registry_items': lambda *args, **kwargs: [],
            'load_host_state': lambda: (host_state or {'hosts': {'legacy.example.com': {'state': 'active'}}}),
            'read_tail': lambda *args, **kwargs: '',
            'RUNTIME_STDOUT_PATH': stdout_path,
            'RUNTIME_STDERR_PATH': stderr_path,
            '_load_owner_approval_actions': lambda: {'approved_ids': [], 'deleted_ids': []},
            '_save_owner_approval_actions': lambda data: None,
            '_owner_approval_row_ids': lambda: [],
            'fetch_filtered_logs': lambda *args, **kwargs: {'page': 1, 'per_page': 50, 'total': 0, 'total_pages': 1, 'items': []},
            'save_planner_ui_state': lambda data: None,
            'load_planner_ui_state': lambda: {},
            'HOST_STATE_PATH': host_state_path,
            'save_orchestrator_state': lambda data: None,
            'RUNTIME_PLAN_META_PATH': reports / '.runtime_plan.meta.json',
            'RUNTIME_PLAN_DELETE_PATHS': [],
            'PLANNER_REGISTRY_ROOT': tmp_path / 'planner-registry',
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else 'alpha')),
            'build_campaign_info_payload': build_campaign_info_payload,
            'build_runtime_health_payload': build_runtime_health_payload,
            'build_selected_campaign_projection': build_selected_campaign_projection,
            'projection_source_label': projection_source_label,
            'RUNTIME_SNAPSHOT_PATH': reports / '.runtime_snapshot.json',
            'RUNTIME_STATE_PATH': reports / '.runtime_state.json',
            'RUNTIME_PID_PATH': reports / '.runtime.pid',
            'ENGINE_DIR': tmp_path / 'engine',
            'WORKSPACE_DIR': tmp_path,
            'PYTHON_BIN': sys.executable,
            'write_runtime_state_file': lambda state, paused=None: None,
        },
    )
    return app


def test_runtime_state_clears_campaign_scoped_snapshot_sections_for_mismatch(tmp_path: Path) -> None:
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
    client = _build_app(tmp_path, runtime).test_client()

    payload = client.get('/api/runtime-state').get_json()

    assert payload['snapshot']['campaign'] == {}
    assert payload['snapshot']['plan'] == {}
    assert payload['snapshot']['latest_run'] == {}
    assert payload['snapshot']['queues'] == {}
    assert payload['snapshot']['telemetry'] == {}
    assert payload['snapshot']['hosts'] == {}
    assert payload['snapshot']['economics'] == {}


def test_runtime_health_and_host_state_ignore_mismatched_snapshot(tmp_path: Path) -> None:
    runtime = {
        'snapshot': {
            'campaign': {'campaign_key': 'beta', 'updated_at': 'snap-ts'},
            'plan': {'plan_revision': 'r2', 'plan_hash': 'feedfacecafebeef'},
            'queues': {'followup_count': 3, 'precision_count': 1},
            'telemetry': {'execution_gate_skip_total': 5},
            'latest_run': {'target': 'https://beta.example.com/'},
            'hosts': {'items': [{'host': 'beta.example.com'}], 'by_host': {'beta.example.com': {'state': 'cooled'}}},
            'economics': {'family_efficiency': [{'key': 'xss', 'runs': 4}]},
        },
        'runtime_plan': {'plan_revision': 'r1', 'plan_hash': 'abc123'},
        'auto_campaign': {'updated_at': 'auto-ts'},
    }
    host_state = {'hosts': {'legacy.example.com': {'state': 'active'}}}
    client = _build_app(tmp_path, runtime, host_state=host_state).test_client()

    health = client.get('/api/runtime-health').get_json()
    campaign_info = client.get('/api/campaign-info').get_json()
    metrics = client.get('/api/metrics').get_json()
    quality = client.get('/api/finding-quality').get_json()
    host_payload = client.get('/api/host-state').get_json()
    host_yield = client.get('/api/host-yield').get_json()
    family_yield = client.get('/api/family-yield').get_json()

    assert health['runtime_snapshot_source'] == 'legacy'
    assert health['queue_followups'] == 0
    assert health['execution_gate_skip_total'] == 0
    assert health['runtime_plan_revision'] == 'r1'
    assert campaign_info['runtime_snapshot_source'] == 'legacy'
    assert metrics['runtime_snapshot_source'] == 'legacy'
    assert quality['runtime_snapshot_source'] == 'legacy'
    assert host_payload['source'] == 'normalized_host_state_file'
    assert host_payload['items'][0]['host'] == 'legacy.example.com'
    assert host_yield['source'] == 'legacy_runtime_vectors'
    assert family_yield['source'] == 'legacy_runtime_vectors'
