from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.policy.core import get_runtime_allowed_tools  # type: ignore
from run_pipeline import enforce_brain_tool_whitelist, fallback_brain_action, preferred_tools_for_task_family, prepare_action_spec_for_execution  # type: ignore
from executor import ExecutionEngine  # type: ignore


def test_enforce_brain_tool_whitelist_allows_capability_first_when_tool_is_omitted() -> None:
    brain = {
        'action_type': 'differential_probe',
        'capability': 'http_probe',
        'task_family': 'authz',
        'resolved_planner_profiles': ['core'],
        'args': ['https://example.com/account'],
        'probe_recipe': {'comparison_mode': 'header_status', 'variant_count': 2, 'evidence_goal': 'compare'},
    }
    out, meta = enforce_brain_tool_whitelist(
        brain,
        objective='authz boundary probe',
        target='https://example.com/account',
        aggression=2,
        task_family='authz',
        execution_mode='normalized',
    )
    assert out == brain
    assert meta is None


def test_fallback_brain_action_prefers_capability_recipe_over_family_heuristic() -> None:
    out = fallback_brain_action(
        objective='generic probe',
        target='https://example.com/app',
        aggression=2,
        task_family='recon',
        recent_context=[],
        intent_context={
            'capability_candidates': ['content_discovery'],
            'recommended_action_types': ['enumeration_probe'],
        },
    )
    assert out['tool'] == 'katana'
    assert out['capability'] == 'content_discovery'
    assert out['action_type'] == 'enumeration_probe'
    assert out['intent'] == 'capability_content_discovery_fallback'


def test_fallback_brain_action_derives_capability_from_action_type_when_needed() -> None:
    out = fallback_brain_action(
        objective='generic probe',
        target='https://example.com/account',
        aggression=2,
        task_family='authz',
        recent_context=[],
        intent_context={
            'capability_candidates': ['response_diff'],
            'recommended_action_types': ['differential_probe'],
        },
    )
    assert out['tool'] == 'curl'
    assert out['capability'] == 'http_probe'
    assert out['action_type'] == 'differential_probe'
    assert out['intent'] == 'capability_http_probe_fallback'


def test_fallback_brain_action_normalizes_bare_host_to_url_for_url_only_tool() -> None:
    out = fallback_brain_action(
        objective='generic probe',
        target='example.com',
        aggression=2,
        task_family='recon',
        recent_context=[],
        intent_context={
            'capability_candidates': ['content_discovery'],
            'recommended_action_types': ['enumeration_probe'],
        },
    )
    assert out['tool'] == 'katana'
    assert out['args'][:2] == ['-u', 'https://example.com']


def test_fallback_brain_action_capability_first_normalizes_url_to_host_for_host_only_tool() -> None:
    out = fallback_brain_action(
        objective='subdomain collection',
        target='https://example.com/app',
        aggression=2,
        task_family='subdomain_expansion',
        recent_context=[],
        intent_context={
            'capability_candidates': ['passive_subdomain_discovery'],
            'recommended_action_types': ['enumeration_probe'],
        },
    )
    assert out['tool'] == 'subfinder'
    assert out['args'] == ['example.com']


def test_fallback_brain_action_uses_nslookup_host_only_shape(monkeypatch) -> None:
    monkeypatch.setattr('run_pipeline.contextual_brain_tooling', lambda *a, **k: {'profiles': ['core'], 'tools': ['nslookup']})
    out = fallback_brain_action(
        objective='dns recon',
        target='https://example.com/path',
        aggression=2,
        task_family='dns',
        recent_context=[],
        intent_context={},
    )
    assert out['tool'] == 'nslookup'
    assert out['args'] == ['example.com']


def test_fallback_brain_action_uses_bounded_hakrawler_stdin_adapter(monkeypatch) -> None:
    monkeypatch.setattr('run_pipeline.contextual_brain_tooling', lambda *a, **k: {'profiles': ['core'], 'tools': ['hakrawler']})
    out = fallback_brain_action(
        objective='crawl recon',
        target='https://example.com/app',
        aggression=2,
        task_family='recon',
        recent_context=[{'summary': 'crawl spider route discovery'}],
        intent_context={},
    )
    assert out['tool'] == 'hakrawler'
    assert out['args'] == ['-d', '2', '-u']
    assert out['stdin'] == 'https://example.com/app\n'
    assert '-url' not in out['args']
    assert '-depth' not in out['args']
    assert '-plain' not in out['args']


def test_fallback_brain_action_capability_first_uses_hakrawler_adapter(monkeypatch) -> None:
    monkeypatch.setattr('run_pipeline.contextual_brain_tooling', lambda *a, **k: {'profiles': ['core'], 'tools': ['hakrawler']})
    out = fallback_brain_action(
        objective='crawler route discovery',
        target='https://example.com/app',
        aggression=2,
        task_family='content_discovery',
        recent_context=[],
        intent_context={
            'capability_candidates': ['crawler_route_discovery'],
            'recommended_action_types': ['enumeration_probe'],
        },
    )
    assert out['tool'] == 'hakrawler'
    assert out['args'] == ['-d', '2', '-u']
    assert out['stdin'] == 'https://example.com/app\n'


def test_preferred_tools_for_task_family_derives_capability_from_action_type_when_candidates_are_noncanonical() -> None:
    tools = preferred_tools_for_task_family(
        'authz',
        'generic probe',
        recent_context=[],
        capability_candidates=['response_diff'],
        recommended_action_types=['differential_probe'],
    )
    assert tools
    assert tools[0] == 'curl'


def test_prepare_action_spec_for_execution_normalized_mode_uses_compiled_curl_behavior() -> None:
    action_spec, compiled = prepare_action_spec_for_execution(
        {
            'action_type': 'differential_probe',
            'capability': 'http_probe',
            'task_family': 'authz',
            'args': ['-s'],
            'probe_recipe': {'comparison_mode': 'header_status', 'variant_count': 2, 'evidence_goal': 'compare'},
        },
        target='https://example.com/account',
        creds={},
        execution_mode='normalized',
    )
    assert compiled['compiler_tool_choice'] == 'curl'
    assert action_spec['tool_chain'][0]['tool'] == 'curl'
    args = action_spec['tool_chain'][0]['args']
    assert 'https://example.com/account' in args
    assert '-o' in args
    assert '-w' in args
    assert '--connect-timeout' in args


def test_prepare_action_spec_for_execution_faithful_mode_preserves_curl_shape() -> None:
    action_spec, compiled = prepare_action_spec_for_execution(
        {
            'action_type': 'differential_probe',
            'capability': 'http_probe',
            'task_family': 'authz',
            'args': ['-s'],
            'probe_recipe': {'comparison_mode': 'header_status', 'variant_count': 2, 'evidence_goal': 'compare'},
        },
        target='https://example.com/account',
        creds={},
        execution_mode='faithful',
    )
    assert compiled['compiler_tool_choice'] == 'curl'
    args = action_spec['tool_chain'][0]['args']
    assert 'https://example.com/account' in args
    assert '-o' not in args
    assert '-w' not in args
    assert '--connect-timeout' not in args


def test_prepare_action_spec_for_execution_preserves_stdin_target_shape() -> None:
    action_spec, compiled = prepare_action_spec_for_execution(
        {
            'action_type': 'enumeration_probe',
            'capability': 'crawler_route_discovery',
            'task_family': 'content_discovery',
            'tool': 'hakrawler',
            'args': ['-d', '2', '-u'],
            'stdin': 'https://example.com/app\n',
        },
        target='https://example.com/app',
        creds={},
        execution_mode='normalized',
    )
    assert compiled['compiler_tool_choice'] == 'hakrawler'
    assert action_spec['tool_chain'][0]['args'] == ['-d', '2', '-u']
    assert action_spec['tool_chain'][0]['stdin'] == 'https://example.com/app\n'
    assert action_spec['args'] == ['-d', '2', '-u']
    assert action_spec['stdin'] == 'https://example.com/app\n'


def test_execution_engine_expands_prev_stdout_path_handoff(tmp_path: Path) -> None:
    if 'python3' not in get_runtime_allowed_tools():
        pytest.skip('python3 not available in executor allowlist')
    engine = ExecutionEngine()
    res = engine.execute(
        {
            'action_type': 'state_transition_probe',
            'capability': 'http_probe',
            'tool': 'python3',
            'args': ['-c', 'print("seed")'],
            'tool_chain': [
                {'tool': 'python3', 'role': 'probe', 'args': ['-c', 'print("handoff-ok")']},
                {
                    'tool': 'python3',
                    'role': 'validate',
                    'args': ['-c', 'from pathlib import Path; import sys; print(Path(sys.argv[1]).read_text(encoding="utf-8").strip())', '{prev_stdout_path}'],
                },
            ],
            'probe_recipe': {'sequence_steps': ['emit', 'consume'], 'evidence_goal': 'bounded handoff'},
        },
        dry_run=False,
    )
    assert res['status'] == 'succeeded'
    assert len(res['step_artifacts']) == 2
    assert 'handoff-ok' in res['stdout']
