from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from campaign_utils import extract_host_from_url, host_in_scope  # type: ignore
from executor import ExecutionEngine  # type: ignore
from govengine.policy.core import contains_tool_restricted_patterns, get_approved_spec_allowed_tools, normalize_tool  # type: ignore
from govengine.execution.command_shape import (
    arg_target_observations,
    enforce_scope,
    enforce_target_semantics,
    extract_hosts_from_text,
    normalize_argv,
)


def test_command_shape_normalize_argv_matches_engine_wrapper() -> None:
    engine = ExecutionEngine()
    allowed = get_approved_spec_allowed_tools()

    assert engine._normalize_argv('curl', ['https://example.com'], approved_spec=True) == normalize_argv(
        'curl',
        ['https://example.com'],
        allowed_tools=allowed,
        contains_tool_restricted_patterns=contains_tool_restricted_patterns,
        normalize_tool=normalize_tool,
        approved_spec=True,
    )


def test_command_shape_host_extraction_matches_engine_wrapper() -> None:
    engine = ExecutionEngine()
    text = 'Host: evil.com https://example.com/path file:///tmp/input.txt'

    assert engine._extract_hosts_from_text(text) == extract_hosts_from_text(text, extract_host_from_url=extract_host_from_url)


def test_command_shape_target_observations_match_engine_wrapper() -> None:
    engine = ExecutionEngine()
    argv = ['hakrawler', '-d', '2', '-u']
    stdin_text = 'https://example.com/app\n'

    assert engine._arg_target_observations(argv, stdin_text=stdin_text) == arg_target_observations(
        argv,
        extract_host_from_url=extract_host_from_url,
        stdin_text=stdin_text,
    )


def test_command_shape_enforce_target_semantics_matches_engine_wrapper() -> None:
    engine = ExecutionEngine()
    argv = ['gau', 'https://example.com']

    with pytest.raises(ValueError, match='invalid_target_kind:gau:url'):
        engine._enforce_target_semantics(argv)
    with pytest.raises(ValueError, match='invalid_target_kind:gau:url'):
        enforce_target_semantics(
            argv,
            tool_catalog=engine.tool_catalog,
            normalize_tool=normalize_tool,
            extract_host_from_url=extract_host_from_url,
        )


def test_command_shape_scope_enforcement_matches_engine_wrapper() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    argv = ['curl', '-q', '-H', 'Host: evil.com', 'https://example.com']

    with pytest.raises(ValueError, match='out_of_scope_target:evil.com'):
        engine._enforce_scope(argv)
    with pytest.raises(ValueError, match='out_of_scope_target:evil.com'):
        enforce_scope(
            argv,
            scope_domains=engine.scope_domains,
            host_in_scope=host_in_scope,
            tool_catalog=engine.tool_catalog,
            normalize_tool=normalize_tool,
            extract_host_from_url=extract_host_from_url,
        )
