from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import run_pipeline as rp  # type: ignore


def test_record_approval_transform_tracks_before_after_and_source() -> None:
    before = {'decision': 'owner_approval_required', 'reason': 'needs owner', 'reason_code': 'owner_approval_required_auth'}
    after = {'decision': 'approve', 'reason': 'owner override', 'reason_code': 'owner_override'}
    chain = []
    rp.record_approval_transform(chain, source='owner_override', before=before, after=after)
    assert len(chain) == 1
    assert chain[0]['source'] == 'owner_override'
    assert chain[0]['before']['decision'] == 'owner_approval_required'
    assert chain[0]['after']['decision'] == 'approve'


def test_execute_flow_marks_semantic_loss_rereview_on_approved_degraded_run(monkeypatch) -> None:
    class FakeEngine:
        def build_command(self, action_spec):
            return ['curl', '-I', action_spec.get('target') or 'https://api.example.com/']

        def execute_approved_spec(self, action_spec, dry_run=False):
            return self.execute(action_spec, dry_run=dry_run)

        def execute(self, action_spec, dry_run=False):
            return {
                'status': 'succeeded',
                'returncode': 0,
                'stdout': 'HTTP/1.1 403 Forbidden',
                'stderr': '',
                'compiled_action': {
                    'action_type': 'fingerprint_probe',
                    'compiler_strategy': 'passthrough',
                    'compiler_tool_choice': 'curl',
                    'compiler_tool_choice_source': 'explicit_tool',
                    'compiler_variant_count': 1,
                    'recipe_name': '',
                    'execution_mode': 'normalized',
                    'semantic_loss_detected': True,
                    'normalization_reason': 'fingerprint_probe_lowered_to_single_probe',
                    'semantic_loss_policy': {
                        'loss_class': 'degraded_semantics',
                        'severity': 'high',
                        'policy_response': 'auditor_rereview',
                        'approved_under_degradation': True,
                        'operator_visibility': 'prominent',
                        'reason_code': 'semantic_loss_fingerprint_lowered',
                        'normalization_reason': 'fingerprint_probe_lowered_to_single_probe',
                    },
                },
            }

    def fake_ask_json(agent, **kwargs):
        if agent == 'brain':
            return {
                'action_type': 'fingerprint_probe',
                'capability': 'http_probe',
                'tool': 'curl',
                'args': ['-I', 'https://api.example.com/'],
                'constraints': {'aggression': 2},
            }
        if agent == 'auditor':
            return {
                'decision': 'approve',
                'reason': 'compiled degraded variant reviewed and acceptable in scope',
                'reason_code': 'approve_in_scope',
                'risk_band': 'medium',
                'owner_gate': False,
                'constraints': {'aggression': 2},
            }
        raise AssertionError(f'unexpected agent: {agent}')

    def fake_prepare(raw_action_spec, *, target, creds, execution_mode):
        final_spec = dict(raw_action_spec)
        final_spec['tool'] = 'curl'
        final_spec['target'] = target
        final_spec['args'] = ['-I', target]
        final_spec['tool_chain'] = [{'tool': 'curl', 'role': 'probe', 'args': ['-I', target]}]
        compiled = {
            'action_type': 'fingerprint_probe',
            'capability': 'http_probe',
            'compiler_strategy': 'passthrough',
            'compiler_tool_choice': 'curl',
            'compiler_tool_choice_source': 'explicit_tool',
            'compiler_variant_count': 1,
            'recipe_name': '',
            'semantic_loss_detected': True,
            'normalization_reason': 'fingerprint_probe_lowered_to_single_probe',
            'semantic_loss_policy': {
                'loss_class': 'degraded_semantics',
                'severity': 'high',
                'policy_response': 'auditor_rereview',
                'approved_under_degradation': True,
                'operator_visibility': 'prominent',
                'reason_code': 'semantic_loss_fingerprint_lowered',
                'normalization_reason': 'fingerprint_probe_lowered_to_single_probe',
            },
            'execution_mode': execution_mode,
            'tool_candidates': ['curl'],
        }
        return final_spec, compiled

    monkeypatch.setattr(rp, 'ask_json', fake_ask_json)
    monkeypatch.setattr(rp, 'prepare_action_spec_for_execution', fake_prepare)
    monkeypatch.setattr(rp, 'evaluate_action_spec', lambda *args, **kwargs: {'pass': True, 'reason': 'ok'})
    monkeypatch.setattr(rp, 'load_credentials_runtime_policy', lambda: {})
    monkeypatch.setattr(rp, 'load_planner_hints', lambda **kwargs: {'preferred_vectors_for_target': [], 'deprioritized_task_families': [], 'ambiguities': [], 'interpretation_conflicts': [], 'task_family_context': {}, 'target_profile': {}})
    monkeypatch.setattr(rp, 'ExecutionEngine', FakeEngine)

    args = argparse.Namespace(
        objective='Probe target',
        target='https://api.example.com/',
        aggression=2,
        task_family='authz',
        task_success_criteria='',
        campaign_success_criteria='',
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
        cost_band='',
    )
    cfg = {
        'execution_mode': 'normalized',
        'json_contract_retries': 0,
        'experimental_payloads': False,
        'strict_deterministic': True,
        'prompt_token_budget': 0,
        'verbose_commands': False,
        'enable_analysis': False,
    }
    output, status, _reason = rp.execute_flow(args, cfg, recent_context=[], context_limit=0)
    assert status in {'succeeded', 'success', 'completed', 'warning'}
    assert output['semantic_loss_rereview_required'] is True
    assert output['semantic_loss_rereview_completed'] is True
    assert output['semantic_loss_rereview_decision'] == 'approve'
    assert output['approval_source'] == 'auditor_rereview'
    assert output['approved_execution_spec']['approval']['semantic_loss_rereview_required'] is True
    assert output['approved_execution_spec']['approval']['semantic_loss_rereview_completed'] is True
    assert output['approved_execution_spec']['approval']['approved_under_degradation'] is True
