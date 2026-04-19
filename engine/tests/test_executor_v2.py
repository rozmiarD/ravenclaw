from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from executor import ExecutionEngine  # type: ignore
from policy_core import get_approved_spec_allowed_tools, get_runtime_allowed_tools  # type: ignore


def test_execution_engine_dry_run_returns_planned_commands_for_chain() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    res = engine.execute(
        {
            'action_type': 'state_transition_probe',
            'capability': 'http_probe',
            'tool': 'curl',
            'args': ['https://example.com/login'],
            'tool_chain': [
                {'tool': 'curl', 'role': 'probe', 'args': ['https://example.com/login']},
                {'tool': 'curl', 'role': 'validate', 'args': ['https://example.com/account']},
            ],
            'probe_recipe': {'sequence_steps': ['login', 'account'], 'evidence_goal': 'state transition'},
        },
        dry_run=True,
    )
    assert res['status'] == 'dry-run'
    assert len(res['planned_commands']) == 2
    assert res['planned_commands'][0][0] == 'curl'
    assert res['planned_commands'][1][0] == 'curl'


def test_execution_engine_executes_bounded_python_chain(tmp_path: Path) -> None:
    if 'python3' not in get_runtime_allowed_tools():
        pytest.skip('python3 not available in executor allowlist')
    marker = tmp_path / 'marker.txt'
    engine = ExecutionEngine()
    res = engine.execute(
        {
            'action_type': 'state_transition_probe',
            'capability': 'http_probe',
            'tool': 'python3',
            'args': ['-c', 'print("seed")'],
            'tool_chain': [
                {
                    'tool': 'python3',
                    'role': 'probe',
                    'args': ['-c', f'from pathlib import Path; Path(r"{marker}").write_text("ok", encoding="utf-8")'],
                },
                {
                    'tool': 'python3',
                    'role': 'validate',
                    'args': ['-c', f'from pathlib import Path; print(Path(r"{marker}").read_text(encoding="utf-8"))'],
                },
            ],
            'probe_recipe': {'sequence_steps': ['write', 'read'], 'evidence_goal': 'bounded chain'},
        },
        dry_run=False,
    )
    assert res['status'] == 'succeeded'
    assert marker.read_text(encoding='utf-8') == 'ok'
    assert '=== step_2:python3 ===' in res['stdout']
    assert 'ok' in res['stdout']


def test_execute_approved_spec_runs_safe_curl_chain(tmp_path: Path) -> None:
    if 'curl' not in get_approved_spec_allowed_tools():
        pytest.skip('curl not available in approved-spec allowlist')
    first = tmp_path / 'first.txt'
    second = tmp_path / 'second.txt'
    first.write_text('one', encoding='utf-8')
    second.write_text('two', encoding='utf-8')
    engine = ExecutionEngine()
    approved = {
        'action_type': 'state_transition_probe',
        'capability': 'http_probe',
        'resolved_tool': 'curl',
        'execution_mode': 'normalized',
        'compiler': {'semantic_loss_policy': {'loss_class': 'none', 'policy_response': 'proceed'}},
        'execution_truth': {
            'execution_plan': [
                {'tool': 'curl', 'args': [first.as_uri()]},
                {'tool': 'curl', 'args': [second.as_uri()]},
            ],
        },
    }
    res = engine.execute_approved_spec(approved, dry_run=False)
    assert res['status'] == 'succeeded'
    assert res['execution_source'] == 'approved_execution_spec'
    assert len(res['executed_commands']) == 2
    assert res['executed_commands'][0][0] == 'curl'
    assert res['executed_commands'][0][1] == '-q'
    assert 'one' in res['stdout']
    assert 'two' in res['stdout']


def test_build_execution_plan_from_approved_spec_disables_user_curlrc() -> None:
    if 'curl' not in get_approved_spec_allowed_tools():
        pytest.skip('curl not available in approved-spec allowlist')
    engine = ExecutionEngine()
    approved = {
        'resolved_tool': 'curl',
        'execution_truth': {
            'execution_plan': [
                {'tool': 'curl', 'args': ['https://example.com']},
            ],
        },
    }
    plan = engine.build_execution_plan_from_approved_spec(approved)
    assert plan[0][:2] == ['curl', '-q']


def test_execute_approved_spec_rejects_operator_shell_meta_tools() -> None:
    engine = ExecutionEngine()
    approved = {
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'resolved_tool': 'python3',
        'execution_mode': 'normalized',
        'execution_truth': {
            'execution_plan': [
                {'tool': 'python3', 'args': ['-c', 'print("blocked")']},
            ],
        },
    }
    with pytest.raises(ValueError, match='tool_not_allowed_for_approved_spec:python3'):
        engine.execute_approved_spec(approved, dry_run=True)
