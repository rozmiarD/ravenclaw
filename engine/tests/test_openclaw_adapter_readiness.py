from __future__ import annotations

import json
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import openclaw_adapter_readiness as readiness


def test_openclaw_readiness_contracts_are_json_safe_and_not_adapter_work() -> None:
    matrix = readiness.openclaw_redaction_matrix()
    ux = readiness.openclaw_approval_ux_sketch()

    assert matrix['adapter_status'] == 'not_implemented'
    assert ux['adapter_status'] == 'not_implemented'
    assert json.loads(json.dumps(matrix)) == matrix
    assert json.loads(json.dumps(ux)) == ux


def test_openclaw_redaction_matrix_blocks_sensitive_fields_for_public_outputs() -> None:
    matrix = readiness.openclaw_redaction_matrix()

    for output in matrix['outputs']:
        assert output['requires_redaction_before_send'] is True
        if output['public_safe']:
            assert set(readiness.ALWAYS_REDACT) <= set(output['blocked_fields'])
            assert 'raw_stdout' not in output['allowed_fields']
            assert 'operator_memory' not in output['allowed_fields']
            assert set(readiness.REQUIRED_NON_CLAIMS) <= set(output['non_claims_required'])


def test_openclaw_approval_ux_preserves_authority_order() -> None:
    ux = readiness.openclaw_approval_ux_sketch()
    step_order = [step['step'] for step in ux['steps']]

    assert step_order == list(readiness.APPROVAL_UX_STEPS)
    assert step_order.index('show_prepared_spec_as_proposal') < step_order.index(
        'show_approved_spec_as_authority_boundary'
    )
    assert step_order.index('show_runner_supervision_state') < step_order.index('show_dry_run_live_truth')


def test_openclaw_readiness_status_rejects_adapter_or_redaction_drift() -> None:
    matrix = readiness.openclaw_redaction_matrix()
    ux = readiness.openclaw_approval_ux_sketch()
    matrix['adapter_status'] = 'implemented'
    matrix['outputs'][0]['blocked_fields'] = []

    status = readiness.evaluate_openclaw_readiness(matrix, ux)

    assert status['status'] == 'failed'
    assert 'adapter_not_implemented' in status['failed_checks']
    assert 'public_outputs_block_secrets' in status['failed_checks']


def test_command_authority_policy_blocks_chat_text_and_missing_boundaries() -> None:
    policy = readiness.openclaw_command_authority_policy()
    decision = readiness.evaluate_command_authority_request({
        'chat_text_contains_command': True,
        'policy_decision': 'approved',
        'prepared_spec_ref': 'prepared-1',
        'approved_spec_ref': 'approved-1',
        'runner_supervision_status': 'ready',
    })
    missing = readiness.evaluate_command_authority_request({
        'chat_text_contains_command': False,
        'policy_decision': 'approved',
        'prepared_spec_ref': 'prepared-1',
        'runner_supervision_status': 'ready',
    })

    assert policy['adapter_status'] == 'not_implemented'
    assert decision['status'] == 'blocked'
    assert decision['stop_reasons'] == ['chat_text_contains_command']
    assert missing['status'] == 'blocked'
    assert 'missing_approved_spec' in missing['stop_reasons']


def test_command_authority_policy_allows_only_complete_structured_chain() -> None:
    decision = readiness.evaluate_command_authority_request({
        'chat_text_contains_command': False,
        'policy_decision': 'approved',
        'prepared_spec_ref': 'prepared-1',
        'approved_spec_ref': 'approved-1',
        'runner_supervision_status': 'ready',
    })

    assert decision['status'] == 'ready_for_ravenclaw_execution_engine'
    assert decision['stop_reasons'] == []


def test_command_authority_rejects_prepared_spec_as_approval_alias() -> None:
    decision = readiness.evaluate_command_authority_request({
        'chat_text_contains_command': False,
        'policy_decision': 'approved',
        'prepared_spec_ref': 'spec-1',
        'approved_spec_ref': 'spec-1',
        'runner_supervision_status': 'ready',
    })

    assert decision['status'] == 'blocked'
    assert 'prepared_spec_treated_as_approved' in decision['stop_reasons']


def test_rollback_stop_contract_requires_operator_visible_structured_reason() -> None:
    contract = readiness.openclaw_rollback_stop_contract()
    blocked = readiness.evaluate_rollback_stop_signal({
        'state': 'pause_requested',
        'operator_visible': False,
        'reason_code': '',
    })
    propagated = readiness.evaluate_rollback_stop_signal({
        'state': 'abort_requested',
        'operator_visible': True,
        'reason_code': 'operator_abort',
    })

    assert contract['adapter_status'] == 'not_implemented'
    assert blocked['status'] == 'blocked'
    assert set(blocked['failed_checks']) == {'not_operator_visible', 'missing_structured_reason'}
    assert propagated['status'] == 'propagated'
    assert propagated['failed_checks'] == []


def test_validation_failure_stop_requires_receipt_reference() -> None:
    blocked = readiness.evaluate_rollback_stop_signal({
        'state': 'validation_failed',
        'operator_visible': True,
        'reason_code': 'public_validation_failed',
    })
    propagated = readiness.evaluate_rollback_stop_signal({
        'state': 'validation_failed',
        'operator_visible': True,
        'reason_code': 'public_validation_failed',
        'validation_receipt_ref': 'receipt-1',
    })

    assert blocked['status'] == 'blocked'
    assert 'missing_validation_receipt_ref' in blocked['failed_checks']
    assert propagated['status'] == 'propagated'


def test_openclaw_readiness_status_passes_for_current_contracts() -> None:
    status = readiness.openclaw_readiness_status()

    assert status['status'] == 'passed'
    assert status['failed_checks'] == []
