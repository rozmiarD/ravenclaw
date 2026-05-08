from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from campaign_utils import extract_host_from_url, host_in_scope  # type: ignore
from executor import ExecutionEngine  # type: ignore
from govengine.execution.command_shape import enforce_scope, extract_hosts_from_text
from govengine.scope import FunctionalScopePort, GovScopePort
from policy_core import normalize_tool  # type: ignore


def test_functional_scope_port_wraps_ravenclaw_scope_helpers() -> None:
    port: GovScopePort = FunctionalScopePort(extract_host_from_url, host_in_scope)
    scope = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}

    assert port.extract_host('https://EXAMPLE.com/path') == 'example.com'
    assert port.host_in_scope('example.com', scope) is True
    assert port.host_in_scope('evil.com', scope) is False


def test_command_shape_accepts_scope_port_without_raw_scope_functions() -> None:
    port = FunctionalScopePort(extract_host_from_url, host_in_scope)
    text = 'Host: evil.com https://example.com/path'

    assert extract_hosts_from_text(text, scope_port=port) == ['evil.com', 'example.com']


def test_executor_uses_scope_port_for_scope_enforcement() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    argv = ['curl', '-q', '-H', 'Host: evil.com', 'https://example.com']

    with pytest.raises(ValueError, match='out_of_scope_target:evil.com'):
        engine._enforce_scope(argv)
    with pytest.raises(ValueError, match='out_of_scope_target:evil.com'):
        enforce_scope(
            argv,
            scope_domains=engine.scope_domains,
            tool_catalog=engine.tool_catalog,
            normalize_tool=normalize_tool,
            scope_port=engine.scope_port,
        )
