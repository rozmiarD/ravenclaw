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


def test_openclaw_readiness_status_passes_for_current_contracts() -> None:
    status = readiness.openclaw_readiness_status()

    assert status['status'] == 'passed'
    assert status['failed_checks'] == []
