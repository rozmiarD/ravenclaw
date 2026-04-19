from __future__ import annotations

from pathlib import Path
import sys

from flask import Flask

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_planner import register_planner_api  # type: ignore
from api_supplemental import register_supplemental_api  # type: ignore
from services import build_campaign_info_payload, build_runtime_health_payload, build_selected_campaign_projection, projection_source_label, selected_runtime_snapshot_view  # type: ignore


def _build_control_client(tmp_path: Path, *, runtime: dict | None = None, alive_sequence: list[tuple[bool, int | None]] | None = None) -> Flask:
    app = Flask(__name__)
    reports = tmp_path / 'reports'
    reports.mkdir(parents=True, exist_ok=True)
    state = {
        'selected_campaign_key': 'camp-alpha',
        'selected_campaign_name': 'Camp Alpha',
        'state': 'idle',
        'owner_override': False,
        'planner_scope_targets': 2,
        'prepared_attacks': 3,
        'runtime_plan_ok': True,
        'runtime_plan_error_preview': '-',
        'pid': '-',
    }
    runtime_payload = runtime if isinstance(runtime, dict) else {
        'runtime_plan': {'campaign_key': 'camp-alpha', 'generated': 3, 'target_count': 2},
        'snapshot': {},
        'auto_campaign': {},
    }
    seq = list(alive_sequence or [(False, None)])
    calls: dict[str, object] = {'writes': [], 'spawned': [], 'terminated': [], 'activated': []}

    def runtime_alive_pid() -> tuple[bool, int | None]:
        if len(seq) > 1:
            return seq.pop(0)
        return seq[0]

    register_supplemental_api(
        app,
        {
            'STATE': state,
            'STATUS_CLASSES': {},
            'fetch_logs': lambda page=1, per_page=500: ([], 0),
            'get_conn': lambda: None,
            'refresh_runtime_state': lambda: None,
            'load_runtime_state': lambda: runtime_payload,
            'load_queue_state': lambda: {'followup_queue': [], 'precision_queue': [], 'source': 'normalized_queue_state'},
            'load_campaign_settings': lambda: {'global': {}, 'by_campaign': {}},
            'save_campaign_settings': lambda data: data,
            'load_pipeline_config': lambda: {},
            'save_pipeline_config': lambda data: data,
            'pipeline_config_meta': lambda: {},
            'load_latest_blueprint': lambda *args, **kwargs: None,
            'selected_campaign_key': lambda: state['selected_campaign_key'],
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
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else state['selected_campaign_key'])),
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
            'write_runtime_state_file': lambda current_state, paused=None: calls['writes'].append({'state': dict(current_state), 'paused': paused}),
            'runtime_alive_pid': runtime_alive_pid,
            'spawn_runtime_process': lambda campaign_key: calls['spawned'].append(str(campaign_key)) or 4242,
            'terminate_runtime_process': lambda pid: calls['terminated'].append(int(pid)) or True,
        },
    )

    register_planner_api(
        app,
        {
            'STATE': state,
            'selected_campaign_key': lambda: state['selected_campaign_key'],
            'load_campaign_blueprint_for_key': lambda key: (None, None, None),
            'runtime_plan_entries_from_blueprint': lambda bp: [],
            'write_runtime_plan': lambda entries, key, reason='manual_or_ui': {'ok': True, 'target_count': len(entries)},
            'load_runtime_plan_meta': lambda: {'campaign_key': state['selected_campaign_key']},
            'load_runtime_state': lambda: runtime_payload,
            'load_runtime_snapshot': lambda: runtime_payload.get('snapshot', {}),
            'selected_runtime_snapshot_view': lambda runtime=None, selected_key=None: selected_runtime_snapshot_view(runtime, str(selected_key if selected_key is not None else state['selected_campaign_key'])),
            'build_selected_campaign_projection': build_selected_campaign_projection,
            'projection_source_label': projection_source_label,
            'load_planner_ui_state': lambda: {'selected_campaign_key': state['selected_campaign_key']},
            'load_latest_blueprint': lambda: None,
            '_list_campaign_registry_items': lambda: [],
            'save_planner_ui_state': lambda data: None,
            'activate_campaign_key': lambda key: calls['activated'].append(str(key)) or {'ok': True},
            'RUNTIME_PLAN_PATH': reports / 'state' / 'public_targets_plan.json',
            'ENGINE_DIR': tmp_path / 'engine',
            'WORKSPACE_DIR': tmp_path,
            'SCOPE_DIR': tmp_path / 'scope',
            'BUDGETS_PATH': tmp_path / 'budgets.yaml',
            'PLAN_CAMPAIGN_SCRIPT': tmp_path / 'engine' / 'plan_campaign.py',
            'PLANNER_REGISTRY_ROOT': tmp_path / 'planner-registry',
        },
    )

    app.testing = True
    client = app.test_client()
    client._control_state = state  # type: ignore[attr-defined]
    client._control_calls = calls  # type: ignore[attr-defined]
    return client


def test_campaign_control_start_spawns_runtime_and_persists_running_state(tmp_path: Path) -> None:
    client = _build_control_client(tmp_path, alive_sequence=[(False, None)])

    resp = client.post('/api/campaign/control', json={'action': 'start', 'owner_override': True})
    payload = resp.get_json()

    assert resp.status_code == 200
    assert payload['ok'] is True
    assert payload['started'] is True
    assert payload['resumed'] is False
    assert payload['pid'] == 4242
    assert client._control_state['state'] == 'running'  # type: ignore[attr-defined]
    assert client._control_state['owner_override'] is True  # type: ignore[attr-defined]
    assert client._control_calls['spawned'] == ['camp-alpha']  # type: ignore[attr-defined]
    assert client._control_calls['writes'][0]['paused'] is False  # type: ignore[attr-defined]


def test_campaign_control_resume_when_runtime_alive_reports_resumed_without_spawn(tmp_path: Path) -> None:
    client = _build_control_client(tmp_path, alive_sequence=[(True, 5150)])

    resp = client.post('/api/campaign/control', json={'action': 'resume'})
    payload = resp.get_json()

    assert resp.status_code == 200
    assert payload['ok'] is True
    assert payload['started'] is False
    assert payload['resumed'] is True
    assert payload['pid'] == 5150
    assert client._control_calls['spawned'] == []  # type: ignore[attr-defined]
    assert client._control_state['state'] == 'running'  # type: ignore[attr-defined]


def test_campaign_control_pause_requires_running_runtime(tmp_path: Path) -> None:
    client = _build_control_client(tmp_path, alive_sequence=[(False, None)])

    resp = client.post('/api/campaign/control', json={'action': 'pause'})
    payload = resp.get_json()

    assert resp.status_code == 400
    assert payload['ok'] is False
    assert payload['error'] == 'runtime_not_running'


def test_campaign_control_stop_without_live_runtime_is_still_clean_stop(tmp_path: Path) -> None:
    client = _build_control_client(tmp_path, alive_sequence=[(False, None)])

    resp = client.post('/api/campaign/control', json={'action': 'stop'})
    payload = resp.get_json()

    assert resp.status_code == 200
    assert payload['ok'] is True
    assert payload['stopped'] is True
    assert payload['terminated'] is False
    assert client._control_state['state'] == 'stopped'  # type: ignore[attr-defined]
    assert client._control_calls['terminated'] == []  # type: ignore[attr-defined]


def test_campaign_control_start_rejects_mismatched_runtime_plan(tmp_path: Path) -> None:
    runtime = {
        'runtime_plan': {'campaign_key': 'other-campaign', 'generated': 3, 'target_count': 2},
        'snapshot': {},
        'auto_campaign': {},
    }
    client = _build_control_client(tmp_path, runtime=runtime, alive_sequence=[(False, None)])

    resp = client.post('/api/campaign/control', json={'action': 'start'})
    payload = resp.get_json()

    assert resp.status_code == 400
    assert payload['ok'] is False
    assert payload['error'] == 'runtime_plan_missing_for_selected_campaign'


def test_activate_from_blueprint_resets_selected_campaign_to_idle_before_activation(tmp_path: Path) -> None:
    client = _build_control_client(tmp_path)
    client._control_state['state'] = 'running'  # type: ignore[attr-defined]

    resp = client.post('/api/campaign/activate-from-blueprint', json={'campaign_key': 'camp-beta'})
    payload = resp.get_json()

    assert resp.status_code == 200
    assert payload['ok'] is True
    assert payload['selected_campaign_key'] == 'camp-beta'
    assert client._control_state['selected_campaign_key'] == 'camp-beta'  # type: ignore[attr-defined]
    assert client._control_state['state'] == 'idle'  # type: ignore[attr-defined]
    assert client._control_calls['activated'] == ['camp-beta']  # type: ignore[attr-defined]
