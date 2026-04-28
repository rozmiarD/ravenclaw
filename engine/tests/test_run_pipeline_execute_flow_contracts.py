from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import run_pipeline as rp  # type: ignore


def _base_args(*, aggression: int = 7, target: str = 'https://target.example/') -> argparse.Namespace:
    return argparse.Namespace(
        objective='Probe target',
        target=target,
        aggression=aggression,
        success_criteria='',
        task_success_criteria='',
        campaign_success_criteria='',
        task_family='content_discovery',
        acceptance_checks='',
        evidence_required='',
        success_semantics_json='',
        experiment_intent_id='',
        capability_candidates_json='',
        recommended_action_types_json='',
        hypothesis_candidates_json='',
        planner_constraints_json='',
        planner_preferences_json='',
        open_questions_json='',
        dry_run=False,
        owner_approved_auth=False,
        owner_override=False,
        verbose_commands=None,
    )



def test_normalize_runtime_aggression_centralizes_all_transforms_without_mutating_input(monkeypatch) -> None:
    args = _base_args(aggression=99, target='https://outside.example/')
    cfg = {
        'out_of_scope_aggression_cap': 5,
        'out_of_scope_allowed_aggression': 7,
    }
    monkeypatch.setattr(rp, 'clamp_aggression', lambda n: 8)
    monkeypatch.setattr(rp, 'host_in_scope', lambda host, domains: False)
    monkeypatch.setattr(rp, 'load_scope_domains', lambda: ['target.example'])

    effective_args, state = rp.normalize_runtime_aggression(
        args,
        cfg=cfg,
        target=args.target,
        raw_action_spec={
            'tool': 'katana',
            'action_type': 'enumeration_probe',
            'task_family': 'content_discovery',
        },
        creds_policy={
            'request_decoration': {
                'mode': 'campaign_required',
                'headers': [{'name': 'X-HackerOne-Research', 'value': 'researcher-example'}],
                'cookies': [],
                'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''},
            },
        },
    )

    assert args.aggression == 99
    assert effective_args.aggression == 3
    assert state['requested_aggression'] == 99
    assert state['effective_aggression'] == 3
    assert [step['stage'] for step in state['chain']] == ['global_clamp', 'out_of_scope_cap', 'policy_remap']
    assert state['chain'][0]['before'] == 99
    assert state['chain'][0]['after'] == 8
    assert state['chain'][1]['after'] == 5
    assert state['chain'][2]['reason'] == 'credentialed_crawler_policy_cap'



def test_execute_flow_mocked_harness_applies_auth_sanitization_and_aggression_remap(monkeypatch) -> None:
    args = _base_args(aggression=7)
    cfg = {
        'json_contract_retries': 1,
        'experimental_payloads': False,
        'strict_deterministic': True,
        'execution_mode': 'normalized',
        'prompt_token_budget': 256,
        'auditor_prompt_token_budget': 256,
        'verbose_commands': True,
        'enable_analysis': False,
        'enable_light': False,
        'analysis_min_bytes': 0,
        'policy_diag_logging': True,
        'out_of_scope_aggression_cap': 1,
        'out_of_scope_allowed_aggression': 1,
    }

    logs: list[tuple] = []
    auditor_context_aggression: list[int] = []
    captured_engine_spec: dict = {}

    monkeypatch.setattr(rp, 'log_stage', lambda *a, **k: logs.append(a))
    monkeypatch.setattr(rp, 'host_in_scope', lambda host, domains: True)
    monkeypatch.setattr(rp, 'load_scope_domains', lambda: ['target.example'])
    monkeypatch.setattr(rp, 'load_planner_hints', lambda **kwargs: {})
    monkeypatch.setattr(rp, 'contextual_brain_tooling', lambda task_family='': {'profiles': ['core'], 'tools': ['katana', 'curl']})
    monkeypatch.setattr(rp, 'preferred_tools_for_task_family', lambda *a, **k: ['katana'])
    monkeypatch.setattr(rp, 'apply_intent_guidance_to_brain', lambda brain, *a, **k: brain)
    monkeypatch.setattr(rp, 'enforce_brain_tool_whitelist', lambda brain, *a, **k: (brain, None))
    monkeypatch.setattr(
        rp,
        'load_credentials_runtime_policy',
        lambda: {
            'credentials_required': False,
            'allow_auth_header': False,
            'allow_cookie_header': False,
            'allow_basic_auth': False,
            'credentials_owner_approved': False,
            'request_decoration': {
                'mode': 'campaign_required',
                'headers': [{'name': 'X-HackerOne-Research', 'value': 'researcher-example'}],
                'cookies': [],
                'basic_auth': {'enabled': False, 'username': '', 'password': '', 'password_ref': ''},
                'provenance_notes': [],
            },
            'resolved_campaign_key': 'camp-1',
            'bug_bounty_username': 'researcher-example',
            'test_account_email': '',
        },
    )
    monkeypatch.setattr(rp, 'evaluate_action_spec', lambda *a, **k: {'pass': True})
    monkeypatch.setattr(rp, '_build_auditor_context_summary', lambda *, args, **kwargs: auditor_context_aggression.append(args.aggression) or {})
    monkeypatch.setattr(rp, 'redact_prepared_execution_spec_for_auditor', lambda spec: spec)
    monkeypatch.setattr(rp, '_compact_prepared_execution_spec_for_auditor', lambda spec: spec)
    monkeypatch.setattr(rp, 'append_context_entry', lambda *a, **k: None)
    monkeypatch.setattr(rp, 'run_analysis_stage', lambda **kwargs: (None, None, None))
    monkeypatch.setattr(rp, 'run_light_stage', lambda **kwargs: (None, None, None))
    monkeypatch.setattr(rp, 'high_signal', lambda *a, **k: False)
    monkeypatch.setattr(rp, 'interesting_http_signal', lambda *a, **k: False)
    monkeypatch.setattr(rp, 'evaluate_success_criteria', lambda *a, **k: {'success_criteria_eval': 'not_met'})

    def fake_ask_json(role: str, **kwargs):
        if role == 'brain':
            return {
                'action_type': 'enumeration_probe',
                'tool': 'katana',
                'args': ['-u', 'user:pass', 'https://target.example/'],
                'tool_chain': [{'tool': 'katana', 'args': ['-u', 'user:pass', 'https://target.example/']}],
                'probe_recipe': {'variant_count': 1},
                'hypothesis': 'credentialed crawler may expose more inventory',
                'why_now': 'campaign allows program identification but not basic auth transport',
                'planner_alignment': 'aligned',
                'planner_override_reason': '',
                'expected_signal': 'inventory growth under bounded enumeration',
                'evidence_goal': 'bounded content discovery',
                'next_if_positive': 'confirm a narrower interesting path',
                'next_if_negative': 'return to recon',
                'redundancy_risk': 'low',
            }
        assert role == 'auditor'
        return {
            'decision': 'approve',
            'reason': 'approve bounded in-scope enumeration',
            'reason_code': 'approve_in_scope',
            'risk_band': 'low',
            'owner_gate': False,
            'constraints': {'aggression': auditor_context_aggression[-1]},
        }

    monkeypatch.setattr(rp, 'ask_json', fake_ask_json)

    class FakeEngine:
        def execute_approved_spec(self, approved_spec, dry_run: bool = False):
            captured_engine_spec['approved_spec'] = approved_spec
            return {
                'status': 'success',
                'returncode': 0,
                'stdout': 'ok',
                'stderr': '',
                'compiled_action': {
                    'compiler_tool_choice': str(approved_spec.get('resolved_tool') or 'katana'),
                    'execution_mode': 'normalized',
                    'recipe_name': '',
                },
                'planned_commands': [list((approved_spec.get('execution_truth') or {}).get('command_preview') or [])],
                'executed_commands': [list((approved_spec.get('execution_truth') or {}).get('command_preview') or [])],
            }

    monkeypatch.setattr(rp, 'ExecutionEngine', FakeEngine)

    output, final_status, final_summary = rp.execute_flow(args, cfg, recent_context=[], context_limit=0)

    assert final_status == 'success'
    assert final_summary == 'ok'
    assert args.aggression == 7
    assert output['brain']['args'] == ['https://target.example/']
    assert output['requested_aggression'] == 7
    assert output['effective_aggression'] == 3
    assert output['aggression_normalization']['effective_aggression'] == 3
    assert [step['stage'] for step in output['aggression_normalization']['chain']] == ['policy_remap']
    assert output['policy_aggression_remap']['reason'] == 'credentialed_crawler_policy_cap'
    assert auditor_context_aggression == [3]
    assert output['approved_execution_spec']['approval']['constraints']['aggression'] == 3
    assert '-u' not in output['approved_execution_spec']['execution_truth']['normalized_args']
    assert output['execution_lineage']['approved_command_input_summary']['target_delivery_mode'] == 'argv'
    assert captured_engine_spec['approved_spec']['approval']['constraints']['aggression'] == 3
    assert any(item[1] == 'contract_auth_mode_sanitized' for item in logs)
    assert any(item[1] == 'aggression_remapped' for item in logs)


def test_execute_flow_prefers_approved_execution_spec_path_even_if_raw_execute_exists(monkeypatch) -> None:
    args = _base_args(aggression=4)
    cfg = {
        'json_contract_retries': 1,
        'experimental_payloads': False,
        'strict_deterministic': True,
        'execution_mode': 'normalized',
        'prompt_token_budget': 256,
        'auditor_prompt_token_budget': 256,
        'verbose_commands': True,
        'enable_analysis': False,
        'enable_light': False,
        'analysis_min_bytes': 0,
        'policy_diag_logging': False,
        'out_of_scope_aggression_cap': 1,
        'out_of_scope_allowed_aggression': 1,
    }

    monkeypatch.setattr(rp, 'log_stage', lambda *a, **k: None)
    monkeypatch.setattr(rp, 'host_in_scope', lambda host, domains: True)
    monkeypatch.setattr(rp, 'load_scope_domains', lambda: ['target.example'])
    monkeypatch.setattr(rp, 'load_planner_hints', lambda **kwargs: {})
    monkeypatch.setattr(rp, 'contextual_brain_tooling', lambda task_family='': {'profiles': ['core'], 'tools': ['curl']})
    monkeypatch.setattr(rp, 'preferred_tools_for_task_family', lambda *a, **k: ['curl'])
    monkeypatch.setattr(rp, 'apply_intent_guidance_to_brain', lambda brain, *a, **k: brain)
    monkeypatch.setattr(rp, 'enforce_brain_tool_whitelist', lambda brain, *a, **k: (brain, None))
    monkeypatch.setattr(rp, 'load_credentials_runtime_policy', lambda: {})
    monkeypatch.setattr(rp, 'evaluate_action_spec', lambda *a, **k: {'pass': True})
    monkeypatch.setattr(rp, '_build_auditor_context_summary', lambda **kwargs: {})
    monkeypatch.setattr(rp, 'redact_prepared_execution_spec_for_auditor', lambda spec: spec)
    monkeypatch.setattr(rp, '_compact_prepared_execution_spec_for_auditor', lambda spec: spec)
    monkeypatch.setattr(rp, 'append_context_entry', lambda *a, **k: None)
    monkeypatch.setattr(rp, 'run_analysis_stage', lambda **kwargs: (None, None, None))
    monkeypatch.setattr(rp, 'run_light_stage', lambda **kwargs: (None, None, None))
    monkeypatch.setattr(rp, 'high_signal', lambda *a, **k: False)
    monkeypatch.setattr(rp, 'interesting_http_signal', lambda *a, **k: False)
    monkeypatch.setattr(rp, 'evaluate_success_criteria', lambda *a, **k: {'success_criteria_eval': 'not_met'})

    def fake_ask_json(role: str, **kwargs):
        if role == 'brain':
            return {
                'action_type': 'single_probe',
                'capability': 'http_probe',
                'tool': 'curl',
                'args': ['-sS', '-I', 'https://target.example/'],
                'tool_chain': [{'tool': 'curl', 'args': ['-sS', '-I', 'https://target.example/']}],
                'constraints': {'aggression': 4},
                'planner_alignment': 'aligned',
                'expected_signal': 'header preview',
                'redundancy_risk': 'low',
            }
        return {
            'decision': 'approve',
            'reason': 'approve bounded in-scope probe',
            'reason_code': 'approve_in_scope',
            'risk_band': 'low',
            'owner_gate': False,
            'constraints': {'aggression': 4},
        }

    monkeypatch.setattr(rp, 'ask_json', fake_ask_json)

    class FakeEngine:
        def execute_approved_spec(self, approved_spec, dry_run: bool = False):
            preview = list((approved_spec.get('execution_truth') or {}).get('command_preview') or [])
            return {
                'status': 'success',
                'returncode': 0,
                'stdout': 'ok',
                'stderr': '',
                'compiled_action': {
                    'compiler_tool_choice': str(approved_spec.get('resolved_tool') or 'curl'),
                    'execution_mode': str(approved_spec.get('execution_mode') or 'normalized'),
                    'recipe_name': '',
                },
                'planned_commands': [preview] if preview else [],
                'executed_commands': [preview] if preview else [],
            }

        def execute(self, action_spec, dry_run: bool = False):
            raise AssertionError('raw_action_spec_execute_should_not_be_used')

    monkeypatch.setattr(rp, 'ExecutionEngine', FakeEngine)

    output, final_status, final_summary = rp.execute_flow(args, cfg, recent_context=[], context_limit=0)

    assert final_status == 'success'
    assert final_summary == 'ok'
    assert output['engine']['status'] == 'success'
    assert output['approved_execution_spec']['approval']['decision'] == 'approve'
    assert output['execution_lineage']['approved_command_preview'][0] == 'curl'


def test_execute_flow_blocks_if_engine_lacks_approved_execution_spec_path(monkeypatch) -> None:
    args = _base_args(aggression=4)
    cfg = {
        'json_contract_retries': 1,
        'experimental_payloads': False,
        'strict_deterministic': True,
        'execution_mode': 'normalized',
        'prompt_token_budget': 256,
        'auditor_prompt_token_budget': 256,
        'verbose_commands': True,
        'enable_analysis': False,
        'enable_light': False,
        'analysis_min_bytes': 0,
        'policy_diag_logging': False,
        'out_of_scope_aggression_cap': 1,
        'out_of_scope_allowed_aggression': 1,
    }

    monkeypatch.setattr(rp, 'log_stage', lambda *a, **k: None)
    monkeypatch.setattr(rp, 'host_in_scope', lambda host, domains: True)
    monkeypatch.setattr(rp, 'load_scope_domains', lambda: ['target.example'])
    monkeypatch.setattr(rp, 'load_planner_hints', lambda **kwargs: {})
    monkeypatch.setattr(rp, 'contextual_brain_tooling', lambda task_family='': {'profiles': ['core'], 'tools': ['curl']})
    monkeypatch.setattr(rp, 'preferred_tools_for_task_family', lambda *a, **k: ['curl'])
    monkeypatch.setattr(rp, 'apply_intent_guidance_to_brain', lambda brain, *a, **k: brain)
    monkeypatch.setattr(rp, 'enforce_brain_tool_whitelist', lambda brain, *a, **k: (brain, None))
    monkeypatch.setattr(rp, 'load_credentials_runtime_policy', lambda: {})
    monkeypatch.setattr(rp, 'evaluate_action_spec', lambda *a, **k: {'pass': True})
    monkeypatch.setattr(rp, '_build_auditor_context_summary', lambda **kwargs: {})
    monkeypatch.setattr(rp, 'redact_prepared_execution_spec_for_auditor', lambda spec: spec)
    monkeypatch.setattr(rp, '_compact_prepared_execution_spec_for_auditor', lambda spec: spec)
    monkeypatch.setattr(rp, 'append_context_entry', lambda *a, **k: None)
    monkeypatch.setattr(rp, 'run_analysis_stage', lambda **kwargs: (None, None, None))
    monkeypatch.setattr(rp, 'run_light_stage', lambda **kwargs: (None, None, None))
    monkeypatch.setattr(rp, 'high_signal', lambda *a, **k: False)
    monkeypatch.setattr(rp, 'interesting_http_signal', lambda *a, **k: False)
    monkeypatch.setattr(rp, 'evaluate_success_criteria', lambda *a, **k: {'success_criteria_eval': 'not_met'})

    def fake_ask_json(role: str, **kwargs):
        if role == 'brain':
            return {
                'action_type': 'single_probe',
                'capability': 'http_probe',
                'tool': 'curl',
                'args': ['-sS', '-I', 'https://target.example/'],
                'tool_chain': [{'tool': 'curl', 'args': ['-sS', '-I', 'https://target.example/']}],
                'constraints': {'aggression': 4},
                'planner_alignment': 'aligned',
                'expected_signal': 'header preview',
                'redundancy_risk': 'low',
            }
        return {
            'decision': 'approve',
            'reason': 'approve bounded in-scope probe',
            'reason_code': 'approve_in_scope',
            'risk_band': 'low',
            'owner_gate': False,
            'constraints': {'aggression': 4},
        }

    monkeypatch.setattr(rp, 'ask_json', fake_ask_json)

    class FakeEngine:
        def execute(self, action_spec, dry_run: bool = False):
            raise AssertionError('raw_action_spec_execute_should_not_be_used')

    monkeypatch.setattr(rp, 'ExecutionEngine', FakeEngine)

    output, final_status, final_summary = rp.execute_flow(args, cfg, recent_context=[], context_limit=0)

    assert final_status == 'blocked'
    assert final_summary == 'execution_adapter_error'
    assert output['reason_code'] == 'execution_adapter_error'
    assert output['engine']['reason'] == 'execution_adapter_error'
    assert 'execution_engine_missing_approved_spec_path' in output['engine']['stderr']
