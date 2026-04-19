from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import yaml

import tool_registry as tr  # type: ignore
from policy_core import get_runtime_allowed_tools, get_runtime_brain_allowed_tools  # type: ignore
from tool_registry import (  # type: ignore
    get_active_planner_profile_state,
    get_execution_allowed_tools,
    get_planner_visible_tools,
    resolve_planner_profiles,
    save_tool_registry_state,
)

ROOT = Path(__file__).resolve().parents[2]


def test_tool_registry_matches_whitelist_for_current_default_core_profile() -> None:
    wl = yaml.safe_load((ROOT / 'whitelist.yaml').read_text(encoding='utf-8')) or {}
    allowed = {str(x).strip().lower() for x in (wl.get('allowed_commands') or []) if str(x).strip()}
    brain = {str(x).strip().lower() for x in (wl.get('brain_allowed_commands') or []) if str(x).strip()}
    assert get_execution_allowed_tools() == allowed
    assert set(get_planner_visible_tools('core')) == brain
    assert {str(x).strip().lower() for x in get_runtime_allowed_tools()} == allowed
    assert {str(x).strip().lower() for x in get_runtime_brain_allowed_tools('core')} == brain


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


def test_save_tool_registry_state_persists_selected_profile(tmp_path: Path, monkeypatch) -> None:
    state_path = tmp_path / '.tool_registry.state.json'
    monkeypatch.setattr(tr, 'TOOL_REGISTRY_STATE_PATH', state_path)
    saved = save_tool_registry_state('extended')
    state = get_active_planner_profile_state()
    assert saved['selected_profile'] == 'extended'
    assert state['active_profile'] == 'extended'
    assert state['source'] == 'config'
    assert 'extended' in state['resolved_profiles']
