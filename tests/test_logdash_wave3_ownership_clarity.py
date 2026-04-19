from pathlib import Path
import sys

from flask import Flask

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_supplemental import register_supplemental_api  # type: ignore
from services import build_campaign_info_payload, build_runtime_health_payload, build_selected_campaign_projection, projection_source_label, selected_runtime_snapshot_view  # type: ignore


def test_queue_state_empty_selected_campaign_uses_explicit_empty_source(tmp_path: Path) -> None:
    app = Flask(__name__)
    reports = tmp_path / 'reports'
    reports.mkdir(parents=True, exist_ok=True)
    runtime = {
        'snapshot': {
            'campaign': {'campaign_key': 'other-campaign'},
            'queues': {'followup_count': 4, 'precision_count': 2},
        },
        'runtime_plan': {'campaign_key': 'alpha'},
    }
    register_supplemental_api(
        app,
        {
            'STATE': {'selected_campaign_name': 'Alpha', 'state': 'idle'},
            'STATUS_CLASSES': {},
            'fetch_logs': lambda page=1, per_page=500: ([], 0),
            'get_conn': lambda: None,
            'refresh_runtime_state': lambda: None,
            'load_runtime_state': lambda: runtime,
            'load_queue_state': lambda: {'followup_queue': [{'target': 'https://wrong.example/'}], 'precision_queue': [], 'source': 'runtime_snapshot'},
            'load_campaign_settings': lambda: {'global': {}, 'by_campaign': {}},
            'save_campaign_settings': lambda data: data,
            'load_pipeline_config': lambda: {},
            'save_pipeline_config': lambda data: data,
            'pipeline_config_meta': lambda: {},
            'load_latest_blueprint': lambda *args, **kwargs: None,
            'selected_campaign_key': lambda: 'alpha',
            '_list_campaign_registry_items': lambda *args, **kwargs: [],
            'load_host_state': lambda: {'hosts': {}},
            'read_tail': lambda *args, **kwargs: '',
            'RUNTIME_STDOUT_PATH': reports / 'runtime.stdout.log',
            'RUNTIME_STDERR_PATH': reports / 'runtime.stderr.log',
            '_load_owner_approval_actions': lambda: {'approved_ids': [], 'deleted_ids': []},
            '_save_owner_approval_actions': lambda data: None,
            '_owner_approval_row_ids': lambda: [],
            'fetch_filtered_logs': lambda *args, **kwargs: {'page': 1, 'per_page': 50, 'total': 0, 'total_pages': 1, 'items': []},
            'save_planner_ui_state': lambda data: None,
            'load_planner_ui_state': lambda: {},
            'HOST_STATE_PATH': reports / 'host-state.json',
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
            'runtime_alive_pid': lambda: (False, None),
            'spawn_runtime_process': lambda campaign_key: 111,
            'terminate_runtime_process': lambda pid: True,
        },
    )
    app.testing = True
    client = app.test_client()

    payload = client.get('/api/queue-state').get_json()

    assert payload['source'] == 'empty_selected_campaign_queue'
    assert payload['followup_count'] == 0
    assert payload['precision_count'] == 0
