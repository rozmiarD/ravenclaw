from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import yaml

import security_tool_registry as tr
from security_policy_core import get_runtime_allowed_tools, get_runtime_brain_allowed_tools  # type: ignore
from security_tool_registry import (
    get_active_planner_profile_state,
    get_execution_allowed_tools,
    get_planner_visible_tools,
    get_tool_catalog,
    resolve_planner_profiles,
    save_tool_registry_state,
)

ROOT = Path(__file__).resolve().parents[2]


def test_tool_registry_matches_whitelist_for_current_default_core_profile() -> None:
    wl = yaml.safe_load((ROOT / 'whitelist.yaml').read_text(encoding='utf-8')) or {}
    allowed = {str(x).strip().lower() for x in (wl.get('allowed_commands') or []) if str(x).strip()}
    brain = {str(x).strip().lower() for x in (wl.get('brain_allowed_commands') or []) if str(x).strip()}
    runtime_allowed = {str(x).strip().lower() for x in get_runtime_allowed_tools()}
    runtime_brain = {str(x).strip().lower() for x in get_runtime_brain_allowed_tools('core')}
    assert get_execution_allowed_tools() == allowed
    assert set(get_planner_visible_tools('core')) == brain
    assert runtime_allowed <= allowed
    assert runtime_brain == brain


def test_extended_and_lab_profiles_expose_future_tools_without_affecting_core() -> None:
    extended = set(get_planner_visible_tools('extended'))
    core = set(get_planner_visible_tools('core'))
    specialized = set(get_planner_visible_tools('specialized'))
    lab = set(get_planner_visible_tools('lab'))
    assert 'gitleaks' in extended
    assert 'trufflehog' in extended
    assert 'masscan' in extended
    assert 'openssl' in extended
    assert 'git' in extended
    assert 'rg' in extended
    assert 'dirsearch' in extended
    assert 'naabu' in extended
    assert 'gitleaks' not in core
    assert 'mitmdump' in specialized
    assert 'smbclient' in specialized
    assert 'rpcclient' in specialized
    assert 'ldapsearch' in specialized
    assert 'snmpwalk' in specialized
    assert 'hydra' in lab
    assert 'aircrack-ng' in lab


def test_resolve_planner_profiles_expands_inheritance() -> None:
    assert resolve_planner_profiles('specialized') == ['core', 'extended', 'specialized']
    assert resolve_planner_profiles('lab') == ['core', 'extended', 'specialized', 'lab']


def test_tool_registry_uses_neutral_govengine_profile_env_name() -> None:
    text = (ROOT / 'engine' / 'tool_registry.yaml').read_text(encoding='utf-8')

    assert 'planner_profiles_env: GOVENGINE_TOOL_PROFILES' in text
    assert 'planner_profiles_env: RAVENCLAW_BRAIN_TOOL_PROFILES' not in text


def test_save_tool_registry_state_persists_selected_profile(tmp_path: Path, monkeypatch) -> None:
    state_path = tmp_path / '.tool_registry.state.json'
    monkeypatch.setattr(tr, 'TOOL_REGISTRY_STATE_PATH', state_path)
    saved = save_tool_registry_state('extended')
    state = get_active_planner_profile_state()
    assert saved['selected_profile'] == 'extended'
    assert state['active_profile'] == 'extended'
    assert state['source'] == 'config'
    assert 'extended' in state['resolved_profiles']


def test_tool_registry_exposes_planner_invocation_mode_for_hakrawler() -> None:
    catalog = get_tool_catalog()
    assert catalog['hakrawler']['planner_invocation_mode'] == 'stdin_target'
    assert catalog['hakrawler']['planner_stdin_args'] == ['-d', '2', '-u']
    assert catalog['curl']['planner_invocation_mode'] == 'direct_args'


def test_tool_registry_exposes_target_validation_mode_for_strict_tools() -> None:
    catalog = get_tool_catalog()
    assert catalog['curl']['target_validation_mode'] == 'strict_url'
    assert catalog['hakrawler']['target_validation_mode'] == 'strict_url'
    assert catalog['gau']['target_validation_mode'] == 'strict_host_domain'
    assert catalog['amass']['target_validation_mode'] == 'strict_host_domain'
    assert catalog['httpx']['target_validation_mode'] == 'none'
