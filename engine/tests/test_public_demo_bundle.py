from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import public_demo_bundle as pdb  # type: ignore


def test_parse_first_json_document_tolerates_trailing_text() -> None:
    payload = '{"ok": true}\n{"ignored": true}\n'
    parsed = pdb._parse_first_json_document(payload)
    assert parsed == {'ok': True}



def test_build_bundle_summary_surfaces_runtime_and_adapter_truth() -> None:
    summary = pdb.build_bundle_summary(
        plan_data={'scope_targets': 25, 'valid_targets': 25},
        pipeline_data={
            'settings': {'runtime_mode': 'demo'},
            'delivery_profile': {'runtime_mode': 'demo'},
            'integration_adapters': {
                'brain': {'mode': 'local'},
                'auditor': {'mode': 'local'},
                'execution': {'mode': 'mock'},
            },
            'engine': {'status': 'dry-run'},
            'final_status': 'warning',
            'planned_command': ['curl', 'https://example.com'],
        },
        commands=[['python3', 'engine/plan_campaign.py'], ['python3', 'engine/run_pipeline.py']],
    )
    assert summary['runtime_mode'] == 'demo'
    assert summary['engine_status'] == 'dry-run'
    assert summary['final_status'] == 'warning'
    assert summary['integration_adapters']['execution']['mode'] == 'mock'
    assert summary['plan_summary']['scope_targets'] == 25
    assert 'approved_execution_spec.json' in summary['proof_trace_files']
    assert 'evidence_bundle.json' in summary['proof_trace_files']


def test_build_bundle_summary_redacts_local_command_paths() -> None:
    local_private = str(Path.home() / '.openclaw' / 'workspace' / 'engine' / 'run_pipeline.py')
    summary = pdb.build_bundle_summary(
        plan_data={},
        pipeline_data={
            'settings': {'runtime_mode': 'demo'},
            'delivery_profile': {'runtime_mode': 'demo'},
            'integration_adapters': {},
            'engine': {'status': 'dry-run'},
            'final_status': 'warning',
            'planned_command': [local_private, 'https://example.com'],
        },
        commands=[[local_private, '--dry-run']],
    )
    assert str(Path.home()) not in str(summary['planned_command'])
    assert str(Path.home()) not in str(summary['demo_commands'])


def test_build_bundle_markdown_mentions_generated_files() -> None:
    text = pdb.build_bundle_markdown(
        {
            'bundle_version': pdb.BUNDLE_VERSION,
            'runtime_mode': 'demo',
            'final_status': 'warning',
            'engine_status': 'dry-run',
            'integration_adapters': {
                'brain': {'mode': 'local'},
                'auditor': {'mode': 'local'},
                'execution': {'mode': 'mock'},
            },
        }
    )
    assert '# Ravenclaw Public Demo Bundle' in text
    assert 'execution_adapter: `mock`' in text
    assert 'run_pipeline.demo.json' in text
    assert 'approved_execution_spec.json' in text
    assert 'evidence_bundle.json' in text
    assert 'scope/input -> policy decision' in text


def test_build_proof_trace_artifacts_redacts_public_sensitive_values() -> None:
    pipeline_data = {
        'settings': {'runtime_mode': 'demo'},
        'policy_gate': {'pass': True, 'reason': 'ok'},
        'auditor': {'owner_gate': False, 'constraints': {'aggression': 3}},
        'prepared_execution_spec': {
            'spec_version': '2026-03-18.prepared.v1',
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'action_type': 'single_probe',
            'resolved_tool': 'curl',
            'normalized_args': ['-H', 'X-Bug-Bounty: secret', '-b', 'session=abc', '-o', str(Path.home() / 'private.txt')],
            'execution_plan': [{'tool': 'curl', 'role': 'probe', 'args': ['-H', 'X-Test-Account-Email: secret@example.com', '-b', 'session=abc']}],
            'scope_facts': {'target': 'https://example.com', 'target_host': 'example.com', 'target_in_scope': True},
            'compiler': {'semantic_loss_policy': {'policy_response': 'proceed'}},
        },
        'approved_execution_spec': {
            'spec_version': '2026-03-18.approved.v1',
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'resolved_tool': 'curl',
            'normalized_args': ['-H', 'X-Bug-Bounty: secret', '-b', 'session=abc', '-o', str(Path.home() / 'private.txt')],
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
            'scope_facts': {'target': 'https://example.com', 'target_host': 'example.com', 'target_in_scope': True},
            'approval': {'decision': 'approve', 'reason': 'ok', 'reason_code': 'approve_in_scope', 'constraints': {}, 'approval_source': 'auditor', 'owner_override_applied': False, 'approval_transform_chain': []},
            'execution_truth': {'artifact_type': 'approved_execution_spec', 'resolved_tool': 'curl', 'normalized_args': ['-H', 'X-Bug-Bounty: secret'], 'execution_plan': [], 'command_preview': [], 'command_input_summary': {'preview_source': 'none', 'target_delivery_mode': 'argv', 'tool': 'curl', 'stdin_present': False}, 'execution_input_summaries': [], 'target_host_match_status': 'exact', 'request_shape_hygiene_status': 'clean'},
        },
        'engine': {'status': 'dry-run', 'returncode': 0, 'reason': 'mock_execution_adapter', 'execution_source': 'mock_adapter', 'stdout': 'secret output', 'stderr': '', 'planned_commands': [['curl', '-o', str(Path.home() / 'private.txt')]], 'executed_commands': [], 'compiled_action': {'compiler_tool_choice': 'curl'}, 'command_input_summary': {'target_delivery_mode': 'argv'}},
        'success_criteria': {'status': 'not_provided', 'met': False, 'evidence': []},
        'final_status': 'warning',
        'reason_code': 'pipeline_warning',
    }
    artifacts = pdb.build_proof_trace_artifacts(pipeline_data)
    approved_text = str(artifacts['approved_execution_spec.json'])
    receipt = artifacts['execution_receipt.json']
    assert 'secret' not in approved_text
    assert str(Path.home()) not in approved_text
    assert receipt['stdout_present'] is True
    assert 'planned_commands' not in receipt
    assert artifacts['policy_decision.json']['decision'] == 'allow_prepare'
    assert artifacts['evidence_bundle.json']['artifact_type'] == 'evidence_bundle'
    assert artifacts['evidence_bundle.json']['public_safety']['raw_live_evidence_included'] is False
