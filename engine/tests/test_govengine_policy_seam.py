from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from govengine.policy import core as gov_policy


def test_govengine_policy_runtime_policy_is_available() -> None:
    gov_result = gov_policy.get_runtime_tool_policy()

    assert isinstance(gov_result['execution_allowed_tools'], set)
    assert isinstance(gov_result['approved_spec_allowed_tools'], set)
    assert isinstance(gov_result['planner_allowed_tools'], tuple)
    assert gov_policy.contains_banned_patterns(['--flood'])[0] is True
