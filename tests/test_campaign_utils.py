from pathlib import Path

from engine import campaign_utils as cu
from engine.campaign_utils import extract_host_from_url, host_in_scope


def test_extract_host_from_url_strips_port_and_lowercases():
    assert extract_host_from_url("https://API.Example.com:8443/path?q=1") == "api.example.com"


def test_host_in_scope_with_wildcard_suffix():
    domains = {"exact": ["api.example.com"], "suffix": ["example.org"]}
    assert host_in_scope("service.example.org", domains) is True
    assert host_in_scope("example.org", domains) is True
    assert host_in_scope("evil-example.org", domains) is False


def test_resolve_scope_text_path_prefers_scope_scope_txt_when_no_ui_selection(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cu, 'WORKSPACE_DIR', tmp_path)
    monkeypatch.setattr(cu, 'SCOPE_DIR', tmp_path / 'scope')
    monkeypatch.setattr(cu, 'DEFAULT_SCOPE_PATH', tmp_path / 'scope' / 'scope.txt')
    monkeypatch.setattr(cu, 'PLANNER_UI_STATE_PATH', tmp_path / 'reports' / '.planner.ui.state.json')
    (tmp_path / 'scope').mkdir(parents=True)
    (tmp_path / 'scope' / 'scope.txt').write_text('IN SCOPE:\nexample.com\n', encoding='utf-8')
    assert cu.resolve_scope_text_path() == (tmp_path / 'scope' / 'scope.txt')
