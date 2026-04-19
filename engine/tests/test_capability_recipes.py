from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from capability_recipes import (  # type: ignore
    get_preferred_tools_for_task_family,
    list_candidate_tools_for_capability,
    resolve_action_tooling,
    resolve_contextual_planner_profiles,
)


def test_resolve_contextual_planner_profiles_expands_tls_to_extended() -> None:
    state = resolve_contextual_planner_profiles('tls_assessment')
    assert 'core' in state['profiles']
    assert 'extended' in state['profiles']
    assert 'lab' not in state['profiles']


def test_list_candidate_tools_for_capability_orders_tls_posture_tools() -> None:
    tools = list_candidate_tools_for_capability('tls_posture_check', task_family='tls_assessment')
    assert tools[:2] == ['httpx-pd', 'testssl.sh']


def test_resolve_action_tooling_selects_capability_recipe_tool_without_explicit_tool() -> None:
    res = resolve_action_tooling({'action_type': 'differential_probe', 'capability': 'http_probe', 'task_family': 'authz'})
    assert res['selected_tool'] == 'curl'
    assert res['resolution_source'] == 'capability_recipe'
    assert 'httpx' in res['candidate_tools']


def test_get_preferred_tools_for_secret_hunt_uses_profile_expansion() -> None:
    tools = get_preferred_tools_for_task_family('secret_hunt', objective='secret hunt on repo surface')
    assert 'gitleaks' in tools or 'trufflehog' in tools
