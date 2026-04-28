from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from policy_core import (  # type: ignore
    get_runtime_allowed_tools,
    get_runtime_brain_allowed_tools,
    get_runtime_tool_policy,
)


def test_runtime_tool_policy_matches_current_core_registry_shape() -> None:
    assert isinstance(get_runtime_allowed_tools(), set)
    assert isinstance(tuple(get_runtime_brain_allowed_tools('core')), tuple)
    assert len(get_runtime_allowed_tools()) > 0
    assert len(tuple(get_runtime_brain_allowed_tools('core'))) > 0


def test_runtime_tool_policy_supports_profile_specific_reads() -> None:
    policy = get_runtime_tool_policy('extended')
    assert 'execution_allowed_tools' in policy
    assert 'planner_allowed_tools' in policy
    assert isinstance(policy['execution_allowed_tools'], set)
    assert isinstance(policy['planner_allowed_tools'], tuple)
    assert 'extended' in policy['profiles']
    assert len(policy['planner_allowed_tools']) >= len(tuple(get_runtime_brain_allowed_tools('core')))


def test_runtime_allowed_tools_exclude_operator_and_high_risk_public_boundary_tools() -> None:
    allowed = get_runtime_allowed_tools()
    assert 'bash' not in allowed
    assert 'python3' not in allowed
    assert 'ssh' not in allowed
    assert 'masscan' not in allowed
    assert 'curl' in allowed
    assert 'httpx' in allowed
