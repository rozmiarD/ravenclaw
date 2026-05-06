from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import run_pipeline as rp  # type: ignore


def test_mock_execution_result_uses_canonical_approved_command_preview_only() -> None:
    res = rp._mock_execution_result(
        {
            'resolved_tool': 'hakrawler',
            'normalized_args': ['-d', '2', '-u'],
            'execution_truth': {
                'artifact_type': 'approved_execution_spec',
                'command_preview': [],
                'command_input_summary': {'preview_source': 'none'},
            },
        },
        effective_dry_run=True,
    )
    assert res['compiled_action']['compiler_tool_choice'] == 'hakrawler'
    assert res['planned_commands'] == []
    assert res['executed_commands'] == []
    assert res['command_input_summary']['preview_source'] == 'none'



def test_execute_flow_demo_mode_uses_local_adapters_and_forces_dry_run(monkeypatch) -> None:
    args = argparse.Namespace(
        objective='Fetch the homepage and summarize visible technologies',
        target='https://example.com/',
        aggression=6,
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
        owner_override=False,
        owner_approved_auth=False,
        dry_run=False,
        verbose_commands=None,
        runtime_mode='demo',
        cost_band='',
    )
    cfg = {
        'json_contract_retries': 0,
        'experimental_payloads': True,
        'strict_deterministic': True,
        'execution_mode': 'faithful',
        'prompt_token_budget': 64,
        'auditor_prompt_token_budget': 64,
        'verbose_commands': True,
        'enable_analysis': True,
        'enable_light': True,
        'analysis_min_bytes': 0,
        'policy_diag_logging': False,
        'out_of_scope_aggression_cap': 1,
        'out_of_scope_allowed_aggression': 1,
    }

    engine_calls: list[bool] = []

    monkeypatch.setattr(rp, 'log_stage', lambda *a, **k: None)
    monkeypatch.setattr(rp, 'host_in_scope', lambda host, domains: True)
    monkeypatch.setattr(rp, 'load_scope_domains', lambda: ['example.com'])
    monkeypatch.setattr(rp, 'load_planner_hints', lambda **kwargs: {})
    monkeypatch.setattr(rp, 'contextual_brain_tooling', lambda task_family='': {'profiles': ['core'], 'tools': ['curl']})
    monkeypatch.setattr(rp, 'preferred_tools_for_task_family', lambda *a, **k: ['curl'])
    monkeypatch.setattr(rp, 'apply_intent_guidance_to_brain', lambda brain, *a, **k: brain)
    monkeypatch.setattr(rp, 'enforce_brain_tool_whitelist', lambda brain, *a, **k: (brain, None))
    monkeypatch.setattr(rp, 'load_credentials_runtime_policy', lambda: {})
    monkeypatch.setattr(rp, 'evaluate_action_spec', lambda *a, **k: {'pass': True})
    monkeypatch.setattr(rp, 'redact_prepared_execution_spec_for_auditor', lambda spec: spec)
    monkeypatch.setattr(rp, '_compact_prepared_execution_spec_for_auditor', lambda spec: spec)
    monkeypatch.setattr(rp, '_build_auditor_context_summary', lambda **kwargs: {})
    monkeypatch.setattr(rp, 'append_context_entry', lambda *a, **k: None)
    monkeypatch.setattr(rp, 'run_analysis_stage', lambda **kwargs: (None, None, None))
    monkeypatch.setattr(rp, 'run_light_stage', lambda **kwargs: (None, None, None))
    monkeypatch.setattr(rp, 'high_signal', lambda *a, **k: False)
    monkeypatch.setattr(rp, 'interesting_http_signal', lambda *a, **k: False)
    monkeypatch.setattr(rp, 'evaluate_success_criteria', lambda *a, **k: {'success_criteria_eval': 'not_met'})
    monkeypatch.setattr(
        rp,
        'fallback_brain_action',
        lambda *a, **k: {
            'action_type': 'single_probe',
            'capability': 'http_probe',
            'tool': 'curl',
            'args': ['-sS', '-I', 'https://example.com/'],
            'constraints': {'aggression': 2},
            'planner_alignment': 'aligned',
            'expected_signal': 'demo-safe header preview',
            'redundancy_risk': 'low',
        },
    )
    monkeypatch.setattr(rp, 'ask_json', lambda *a, **k: (_ for _ in ()).throw(AssertionError('ask_json should not be used in demo mode')))

    class FakeEngine:
        def execute_approved_spec(self, approved_spec, dry_run: bool = False, **kwargs):
            engine_calls.append(bool(dry_run))
            preview = list((approved_spec.get('execution_truth') or {}).get('command_preview') or [])
            return {
                'status': 'dry-run' if dry_run else 'success',
                'returncode': 0,
                'stdout': '',
                'stderr': '',
                'compiled_action': {
                    'compiler_tool_choice': str(approved_spec.get('resolved_tool') or 'curl'),
                    'execution_mode': str(approved_spec.get('execution_mode') or 'normalized'),
                    'recipe_name': '',
                },
                'planned_commands': [preview] if preview else [],
                'executed_commands': [],
            }

    monkeypatch.setattr(rp, 'ExecutionEngine', FakeEngine)

    output, final_status, _summary = rp.execute_flow(args, cfg, recent_context=[], context_limit=0)

    assert final_status in {'success', 'warning'}
    assert engine_calls == []
    assert output['settings']['runtime_mode'] == 'demo'
    assert output['settings']['forced_dry_run'] is True
    assert output['settings']['execution_mode'] == 'normalized'
    assert output['settings']['enable_analysis'] is False
    assert output['settings']['enable_light'] is False
    assert output['integration_adapters']['brain']['mode'] == 'local'
    assert output['integration_adapters']['auditor']['mode'] == 'local'
    assert output['integration_adapters']['execution']['mode'] == 'mock'
    assert output['delivery_notes']['dry_run_forced'] is True
    assert output['auditor']['decision'] == 'approve'
    assert output['engine']['status'] == 'dry-run'
    assert output['execution_lineage']['approved_command_preview'][0] == 'curl'
