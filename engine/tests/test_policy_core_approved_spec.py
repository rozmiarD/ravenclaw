from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from policy_core import get_approved_spec_allowed_tools, get_runtime_allowed_tools  # type: ignore


def test_approved_spec_allowed_tools_excludes_operator_shell_tools() -> None:
    runtime_allowed = get_runtime_allowed_tools()
    approved_allowed = get_approved_spec_allowed_tools()
    assert approved_allowed <= runtime_allowed
    assert 'bash' not in approved_allowed
    assert 'python3' not in approved_allowed


def test_approved_spec_allowed_tools_keep_core_research_tools() -> None:
    approved_allowed = get_approved_spec_allowed_tools()
    assert 'curl' in approved_allowed
    assert 'httpx' in approved_allowed
