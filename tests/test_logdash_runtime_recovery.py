from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1] / 'logdash'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import services  # type: ignore


class _Conn:
    def close(self) -> None:
        return None


def test_refresh_runtime_state_clears_stale_pid_file_and_returns_idle(tmp_path: Path, monkeypatch) -> None:
    reports = tmp_path / 'reports'
    reports.mkdir()
    runtime_state_path = reports / '.auto_campaign.state.json'
    runtime_pid_path = reports / '.auto_campaign.pid'
    runtime_state_path.write_text(json.dumps({'paused': False, 'stopped': False, 'owner_override': True}), encoding='utf-8')
    runtime_pid_path.write_text('999999', encoding='utf-8')

    monkeypatch.setattr(services, 'runtime_process_alive', lambda path: (False, '-'))
    monkeypatch.setattr(services, 'latest_log_for', lambda conn, tor: None)

    state = {'state': 'running', 'owner_override': False, 'pid': '999999'}
    services.refresh_runtime_state(
        state,
        get_conn=lambda: _Conn(),
        runtime_state_path=runtime_state_path,
        runtime_pid_path=runtime_pid_path,
        reports_dir=reports,
    )

    persisted = json.loads(runtime_state_path.read_text(encoding='utf-8'))
    assert state['state'] == 'idle'
    assert state['pid'] == '-'
    assert state['owner_override'] is True
    assert not runtime_pid_path.exists()
    assert persisted['stopped'] is False
    assert persisted['paused'] is False
    assert persisted['owner_override'] is True



def test_refresh_runtime_state_preserves_paused_when_runtime_alive(tmp_path: Path, monkeypatch) -> None:
    reports = tmp_path / 'reports'
    reports.mkdir()
    runtime_state_path = reports / '.auto_campaign.state.json'
    runtime_pid_path = reports / '.auto_campaign.pid'
    runtime_state_path.write_text(json.dumps({'paused': True, 'stopped': False, 'owner_override': False}), encoding='utf-8')

    monkeypatch.setattr(services, 'runtime_process_alive', lambda path: (True, '4242'))
    monkeypatch.setattr(services, 'latest_log_for', lambda conn, tor: None)

    state = {'state': 'idle', 'owner_override': False, 'pid': '-'}
    services.refresh_runtime_state(
        state,
        get_conn=lambda: _Conn(),
        runtime_state_path=runtime_state_path,
        runtime_pid_path=runtime_pid_path,
        reports_dir=reports,
    )

    persisted = json.loads(runtime_state_path.read_text(encoding='utf-8'))
    assert state['state'] == 'paused'
    assert state['pid'] == '4242'
    assert runtime_pid_path.read_text(encoding='utf-8') == '4242'
    assert persisted['paused'] is True
    assert persisted['stopped'] is False



def test_refresh_runtime_state_keeps_stopped_over_recent_activity(tmp_path: Path, monkeypatch) -> None:
    reports = tmp_path / 'reports'
    reports.mkdir()
    runtime_state_path = reports / '.auto_campaign.state.json'
    runtime_pid_path = reports / '.auto_campaign.pid'
    runtime_state_path.write_text(json.dumps({'paused': False, 'stopped': True, 'owner_override': False}), encoding='utf-8')

    monkeypatch.setattr(services, 'runtime_process_alive', lambda path: (False, '-'))
    monkeypatch.setattr(
        services,
        'latest_log_for',
        lambda conn, tor: {'status': 'running', 'timestamp': '2099-01-01T00:00:00+00:00'} if tor == 'AUTO_CAMPAIGN' else None,
    )

    state = {'state': 'running', 'owner_override': False, 'pid': '777'}
    services.refresh_runtime_state(
        state,
        get_conn=lambda: _Conn(),
        runtime_state_path=runtime_state_path,
        runtime_pid_path=runtime_pid_path,
        reports_dir=reports,
    )

    persisted = json.loads(runtime_state_path.read_text(encoding='utf-8'))
    assert state['state'] == 'stopped'
    assert state['pid'] == '-'
    assert persisted['stopped'] is True
    assert persisted['paused'] is False
