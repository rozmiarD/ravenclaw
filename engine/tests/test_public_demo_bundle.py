from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import public_demo_bundle as pdb  # type: ignore
import run_pipeline  # type: ignore
import security_contract_layer as compatibility_layer  # type: ignore


def test_run_pipeline_uses_sample_scope_fallback_in_demo_mode(monkeypatch) -> None:
    monkeypatch.setenv('RAVENCLAW_MODE', 'demo')
    monkeypatch.setattr(run_pipeline, 'load_planner_ui_state', lambda: {})
    assert run_pipeline._selected_scope_path().as_posix().endswith('engine/planer/examples/sample_scope.txt')



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
    assert 'execution_ticket.json' in summary['lifecycle_trace_files']
    assert 'artifact_chain_manifest.json' in summary['lifecycle_trace_files']
    assert summary['review_bundle_dir'] == 'review_bundle'


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
    assert 'execution_ticket.json' in text
    assert 'artifact_chain_manifest.json' in text
    assert 'review_bundle/verification_receipt.json' in text
    assert 'intent -> policy decision -> execution contract -> scoped execution ticket' in text


def test_legacy_compatibility_trace_redacts_public_sensitive_values() -> None:
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
    artifacts = compatibility_layer.build_proof_trace_artifacts(pipeline_data)
    approved_text = str(artifacts['approved_execution_spec.json'])
    receipt = artifacts['execution_receipt.json']
    assert 'secret' not in approved_text
    assert str(Path.home()) not in approved_text
    assert receipt['stdout_present'] is True
    assert 'planned_commands' not in receipt
    assert artifacts['policy_decision.json']['decision'] == 'allow_prepare'
    assert artifacts['evidence_bundle.json']['artifact_type'] == 'evidence_bundle'
    assert artifacts['evidence_bundle.json']['public_safety']['raw_live_evidence_included'] is False


def test_build_current_lifecycle_artifacts_redacts_and_links_public_chain(tmp_path: Path) -> None:
    pipeline_data = {
        'run_id': 'demo-chain-001',
        'created_at': '2026-05-06T18:31:00+00:00',
        'settings': {'runtime_mode': 'demo'},
        'policy_gate': {'pass': True, 'reason': 'ok'},
        'auditor': {'owner_gate': False, 'constraints': {'aggression': 3}},
        'prepared_execution_spec': {
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'action_type': 'single_probe',
            'resolved_tool': 'curl',
            'normalized_args': ['-H', 'X-Bug-Bounty: secret', 'https://example.com'],
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
            'scope_facts': {'target': 'https://example.com', 'target_host': 'example.com', 'target_in_scope': True},
        },
        'approved_execution_spec': {
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'resolved_tool': 'curl',
            'normalized_args': ['https://example.com'],
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
            'approval': {'decision': 'approve', 'reason': 'ok', 'approval_source': 'auditor'},
            'execution_truth': {'artifact_type': 'approved_execution_spec', 'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}], 'normalized_args': ['https://example.com']},
        },
        'engine': {'status': 'dry-run', 'returncode': 0, 'reason': 'mock_execution_adapter', 'execution_source': 'mock_adapter', 'stdout': 'secret output', 'planned_commands': [['curl', 'https://example.com']], 'executed_commands': []},
    }
    artifacts = pdb.build_current_lifecycle_artifacts(pipeline_data)
    for filename, artifact in artifacts.items():
        (tmp_path / filename).write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    from sclite.integrity import verify_artifact_chain_manifest

    result = verify_artifact_chain_manifest(artifacts['artifact_chain_manifest.json'], root=tmp_path)
    serialized = json.dumps(artifacts, sort_keys=True)
    assert result['entry_count'] == 6
    assert 'X-Bug-Bounty: secret' not in serialized
    assert artifacts['execution_ticket.json']['schema_version'] == 'v0.3'
    assert artifacts['execution_ticket.json']['integrity']['ticket_binds_execution_contract_digest']


def test_current_demo_lifecycle_uses_scoped_ticket_and_passed_review_bundle(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(pdb, 'repo_root', lambda: tmp_path)
    monkeypatch.setattr(pdb.demo_entry, 'build_demo_commands', lambda python_bin: [['python', 'plan'], ['python', 'run']])
    pipeline_data = {
        'run_id': 'current-demo',
        'created_at': '2026-05-23T00:00:00+00:00',
        'settings': {'runtime_mode': 'demo'},
        'policy_gate': {'pass': True, 'reason': 'ok'},
        'auditor': {'owner_gate': False, 'constraints': {}},
        'prepared_execution_spec': {
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'action_type': 'single_probe',
            'resolved_tool': 'curl',
            'normalized_args': ['https://example.com'],
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
        },
        'approved_execution_spec': {
            'target': 'https://example.com',
            'target_host': 'example.com',
            'target_in_scope': True,
            'resolved_tool': 'curl',
            'normalized_args': ['https://example.com'],
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
            'approval': {'decision': 'approve', 'approval_source': 'auditor'},
            'execution_truth': {'artifact_type': 'approved_execution_spec', 'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}]},
        },
        'engine': {'status': 'dry-run', 'returncode': 0, 'planned_commands': [['curl', 'https://example.com']], 'executed_commands': []},
        'delivery_profile': {},
        'integration_adapters': {'execution': {'mode': 'mock'}},
    }
    monkeypatch.setattr(pdb, '_run_json_command', lambda command, cwd, env: {} if command[-1] == 'plan' else pipeline_data)

    result = pdb.generate_bundle(output_dir='out')
    review = json.loads((tmp_path / 'out' / 'review_bundle' / 'verification_receipt.json').read_text(encoding='utf-8'))

    assert result['summary']['review_bundle_dir'] == 'review_bundle'
    assert review['verdict'] == 'pass'
    assert json.loads((tmp_path / 'out' / 'execution_ticket.json').read_text(encoding='utf-8'))['schema_version'] == 'v0.3'
