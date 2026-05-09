from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from executor import ExecutionEngine  # type: ignore
from sclite.integrity import artifact_descriptor  # type: ignore
from policy_core import get_approved_spec_allowed_tools, get_runtime_allowed_tools  # type: ignore




def _execution_ticket_for(approved_spec: dict) -> tuple[dict, dict]:
    execution_plan = list((approved_spec.get('execution_truth') or {}).get('execution_plan') or [])
    execution_contract = {
        'artifact_type': 'execution_contract',
        'schema_version': 'v0.2',
        'contract_id': 'test-contract',
        'execution_shape': {'plan': execution_plan},
    }
    digest = artifact_descriptor(execution_contract)['digest']
    execution_ticket = {
        'artifact_type': 'execution_ticket',
        'schema_version': 'v0.2',
        'ticket_id': 'test-ticket',
        'approval': {'status': 'approve'},
        'execution_limits': {'one_shot': True, 'max_runs': 1},
        'integrity': {'ticket_binds_execution_contract_digest': digest, 'profile': 'test-integrity-only'},
    }
    return execution_ticket, execution_contract

def _approved_spec(*, tool: str, execution_plan: list[dict], action_type: str = 'single_probe', capability: str = 'http_probe', execution_mode: str = 'normalized') -> dict:
    return {
        'spec_version': '2026-03-18.approved.v1',
        'action_type': action_type,
        'capability': capability,
        'resolved_tool': tool,
        'execution_mode': execution_mode,
        'compiler': {'semantic_loss_policy': {'loss_class': 'none', 'policy_response': 'proceed'}},
        'approval': {'decision': 'approve', 'reason': 'ok', 'reason_code': 'approve_in_scope', 'constraints': {}},
        'execution_truth': {
            'artifact_type': 'approved_execution_spec',
            'execution_plan': execution_plan,
        },
    }


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
    assert res['execution_source'] == 'legacy_direct_action_spec'
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
    assert res['execution_source'] == 'legacy_direct_action_spec'
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
    approved = _approved_spec(
        tool='curl',
        action_type='state_transition_probe',
        execution_plan=[
            {'tool': 'curl', 'args': [first.as_uri()]},
            {'tool': 'curl', 'args': [second.as_uri()]},
        ],
    )
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
    approved = _approved_spec(
        tool='curl',
        execution_plan=[
            {'tool': 'curl', 'args': ['https://example.com']},
        ],
    )
    plan = engine.build_execution_plan_from_approved_spec(approved)
    assert plan[0][:2] == ['curl', '-q']


def test_execute_approved_spec_rejects_operator_shell_meta_tools() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec(
        tool='python3',
        execution_plan=[
            {'tool': 'python3', 'args': ['-c', 'print("blocked")']},
        ],
    )
    with pytest.raises(ValueError, match='tool_not_allowed_for_approved_spec:python3'):
        engine.execute_approved_spec(approved, dry_run=True)


def test_execute_approved_spec_rejects_missing_spec_version() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec(tool='curl', execution_plan=[{'tool': 'curl', 'args': ['https://example.com']}])
    approved.pop('spec_version', None)
    with pytest.raises(ValueError, match='invalid_approved_execution_spec_version:missing'):
        engine.execute_approved_spec(approved, dry_run=True)


def test_execute_approved_spec_rejects_non_approved_decision() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec(tool='curl', execution_plan=[{'tool': 'curl', 'args': ['https://example.com']}])
    approved['approval'] = {'decision': 'reject', 'reason': 'no', 'reason_code': 'blocked', 'constraints': {}}
    with pytest.raises(ValueError, match='invalid_approved_execution_decision:reject'):
        engine.execute_approved_spec(approved, dry_run=True)


def test_execute_approved_spec_rejects_missing_execution_truth_artifact_type() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec(tool='curl', execution_plan=[{'tool': 'curl', 'args': ['https://example.com']}])
    approved['execution_truth'] = {'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}]}  # missing artifact_type
    with pytest.raises(ValueError, match='invalid_approved_execution_truth_artifact:missing'):
        engine.execute_approved_spec(approved, dry_run=True)


def test_execute_approved_spec_rejects_missing_execution_plan() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec(tool='curl', execution_plan=[{'tool': 'curl', 'args': ['https://example.com']}])
    approved['execution_truth'] = {'artifact_type': 'approved_execution_spec'}
    with pytest.raises(ValueError, match='missing_execution_plan'):
        engine.execute_approved_spec(approved, dry_run=True)


def test_build_execution_plan_from_approved_spec_rejects_empty_execution_plan() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec(tool='curl', execution_plan=[])
    with pytest.raises(ValueError, match='missing_execution_plan'):
        engine.build_execution_plan_from_approved_spec(approved)


def test_execution_engine_rejects_runtime_operator_shell_tools() -> None:
    engine = ExecutionEngine()
    with pytest.raises(ValueError, match='tool_not_allowed:python3'):
        engine.execute(
            {
                'action_type': 'single_probe',
                'capability': 'http_probe',
                'tool': 'python3',
                'args': ['-c', 'print("blocked")'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'blocked runtime tool'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_restricted_curl_file_output_flags() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='tool_restricted_pattern:curl:--output'):
        engine.execute(
            {
                'action_type': 'single_probe',
                'capability': 'http_probe',
                'tool': 'curl',
                'args': ['--output', 'body.txt', 'https://example.com'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'blocked file write'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_out_of_scope_host_hidden_in_header_value() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='out_of_scope_target:evil.com'):
        engine.execute(
            {
                'action_type': 'single_probe',
                'capability': 'http_probe',
                'tool': 'curl',
                'args': ['-H', 'Host: evil.com', 'https://example.com'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'hidden out-of-scope host'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_out_of_scope_bare_domain_token() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='out_of_scope_target:evil.com'):
        engine.execute(
            {
                'action_type': 'single_probe',
                'capability': 'dns_enumeration',
                'tool': 'dig',
                'args': ['evil.com'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'bare out-of-scope domain'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_katana_proxy_flag() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='tool_restricted_pattern:katana:-proxy'):
        engine.execute(
            {
                'action_type': 'enumeration_probe',
                'capability': 'content_discovery',
                'tool': 'katana',
                'args': ['-u', 'https://example.com', '-proxy', 'http://127.0.0.1:8080'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'blocked proxy use'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_whatweb_log_output_flag_case_insensitive() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='tool_restricted_pattern:whatweb:--LOG-JSON=out.json'):
        engine.execute(
            {
                'action_type': 'single_probe',
                'capability': 'http_fingerprint',
                'tool': 'whatweb',
                'args': ['--LOG-JSON=out.json', 'https://example.com'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'blocked log export'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_gau_proxy_flag() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='tool_restricted_pattern:gau:--proxy'):
        engine.execute(
            {
                'action_type': 'enumeration_probe',
                'capability': 'historical_url_collection',
                'tool': 'gau',
                'args': ['--proxy', 'http://127.0.0.1:8080', '--subs', 'example.com'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'blocked proxy use'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_dnsx_list_input_flag() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='tool_restricted_pattern:dnsx:-list'):
        engine.execute(
            {
                'action_type': 'enumeration_probe',
                'capability': 'dns_resolution',
                'tool': 'dnsx',
                'args': ['-list', 'targets.txt'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'blocked file-fed broadening'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_subfinder_config_flag() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='tool_restricted_pattern:subfinder:-config'):
        engine.execute(
            {
                'action_type': 'enumeration_probe',
                'capability': 'passive_subdomain_discovery',
                'tool': 'subfinder',
                'args': ['-config', '/tmp/subfinder.yaml', '-d', 'example.com'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'blocked config injection'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_gau_url_target_kind() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='invalid_target_kind:gau:url'):
        engine.execute(
            {
                'action_type': 'enumeration_probe',
                'capability': 'historical_url_collection',
                'tool': 'gau',
                'args': ['https://example.com'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'host-only tool given URL target'},
            },
            dry_run=True,
        )


def test_execution_engine_rejects_katana_missing_url_target_kind() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='missing_target_kind:katana:url'):
        engine.execute(
            {
                'action_type': 'enumeration_probe',
                'capability': 'content_discovery',
                'tool': 'katana',
                'args': ['example.com'],
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'url-only tool given bare host'},
            },
            dry_run=True,
        )


def test_execution_engine_allows_dig_bare_domain_target() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    res = engine.execute(
        {
            'action_type': 'enumeration_probe',
            'capability': 'dns_enumeration',
            'tool': 'dig',
            'args': ['example.com'],
            'tool_chain': [],
            'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'host/domain target remains allowed'},
        },
        dry_run=True,
    )
    assert res['status'] == 'dry-run'


def test_execution_engine_allows_hakrawler_stdin_url_target() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    res = engine.execute(
        {
            'action_type': 'enumeration_probe',
            'capability': 'crawler_route_discovery',
            'tool': 'hakrawler',
            'args': ['-d', '2', '-u'],
            'stdin': 'https://example.com/app\n',
            'tool_chain': [],
            'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'stdin-fed url target remains allowed'},
        },
        dry_run=True,
    )
    assert res['status'] == 'dry-run'


def test_execution_engine_rejects_hakrawler_out_of_scope_stdin_url_target() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    with pytest.raises(ValueError, match='out_of_scope_target:evil.com'):
        engine.execute(
            {
                'action_type': 'enumeration_probe',
                'capability': 'crawler_route_discovery',
                'tool': 'hakrawler',
                'args': ['-d', '2', '-u'],
                'stdin': 'https://evil.com/app\n',
                'tool_chain': [],
                'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'stdin-fed out-of-scope target'},
            },
            dry_run=True,
        )


def test_execute_approved_spec_runtime_ticket_gate_passes_for_bound_contract() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    approved = _approved_spec(tool='curl', execution_plan=[{'tool': 'curl', 'args': ['https://example.com']}])
    ticket, contract = _execution_ticket_for(approved)
    res = engine.execute_approved_spec(
        approved,
        dry_run=True,
        execution_ticket=ticket,
        execution_contract=contract,
        require_execution_ticket=True,
    )
    assert res['execution_ticket_gate']['status'] == 'passed'
    assert res['execution_ticket_gate']['ticket_id'] == 'test-ticket'
    assert res['govengine_control_gate']['status'] == 'allowed'
    assert res['govengine_control_gate']['runner_profile'] == 'dry-run'
    assert res['govengine_control_gate']['state_index']['status'] == 'ready'


def test_execute_approved_spec_runtime_ticket_gate_rejects_missing_ticket() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec(tool='curl', execution_plan=[{'tool': 'curl', 'args': ['https://example.com']}])
    with pytest.raises(ValueError, match='missing_execution_ticket'):
        engine.execute_approved_spec(approved, dry_run=True, require_execution_ticket=True)


def test_execute_approved_spec_runtime_ticket_gate_rejects_contract_mismatch() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec(tool='curl', execution_plan=[{'tool': 'curl', 'args': ['https://example.com']}])
    ticket, contract = _execution_ticket_for(approved)
    contract['execution_shape']['plan'][0]['args'] = ['https://different.example']
    with pytest.raises(ValueError, match='execution_ticket_contract_digest_mismatch'):
        engine.execute_approved_spec(
            approved,
            dry_run=True,
            execution_ticket=ticket,
            execution_contract=contract,
            require_execution_ticket=True,
        )
