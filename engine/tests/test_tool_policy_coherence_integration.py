from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from contracts import get_contract_allowed_tools  # type: ignore
from govengine.policy.core import get_runtime_brain_allowed_tools, get_runtime_tool_policy  # type: ignore
from tool_registry import get_planner_visible_tools  # type: ignore


def test_extended_profile_contract_and_runtime_policy_align() -> None:
    runtime_policy = get_runtime_tool_policy('extended')
    planner_runtime = {str(x).strip().lower() for x in runtime_policy['planner_allowed_tools']}
    planner_registry = {str(x).strip().lower() for x in get_planner_visible_tools('extended')}
    planner_contract = {str(x).strip().lower() for x in get_contract_allowed_tools('extended')}
    planner_core_accessor = {str(x).strip().lower() for x in get_runtime_brain_allowed_tools('extended')}

    assert planner_runtime == planner_registry
    assert planner_runtime == planner_contract
    assert planner_runtime == planner_core_accessor
