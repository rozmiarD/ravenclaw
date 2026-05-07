from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import policy_core as engine_policy  # type: ignore
from govengine.policy import core as gov_policy


def test_policy_core_is_govengine_compat_wrapper() -> None:
    assert engine_policy.get_runtime_allowed_tools is gov_policy.get_runtime_allowed_tools
    assert engine_policy.get_approved_spec_allowed_tools is gov_policy.get_approved_spec_allowed_tools
    assert engine_policy.contains_banned_patterns is gov_policy.contains_banned_patterns
    assert engine_policy.check_credentials_policy is gov_policy.check_credentials_policy


def test_govengine_policy_runtime_policy_matches_engine_wrapper() -> None:
    engine_result = engine_policy.get_runtime_tool_policy()
    gov_result = gov_policy.get_runtime_tool_policy()

    assert engine_result['execution_allowed_tools'] == gov_result['execution_allowed_tools']
    assert engine_result['approved_spec_allowed_tools'] == gov_result['approved_spec_allowed_tools']
    assert engine_result['planner_allowed_tools'] == gov_result['planner_allowed_tools']
