from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine_control_gate_adapter import evaluate_govengine_control_gate  # type: ignore
from sclite.integrity import artifact_descriptor  # type: ignore


def _ticket_and_contract() -> tuple[dict, dict, dict]:
    execution_contract = {
        'artifact_type': 'execution_contract',
        'schema_version': 'v0.2',
        'contract_id': 'test-contract',
        'execution_shape': {'plan': [{'tool': 'curl', 'args': ['https://example.com']}]},
    }
    digest = artifact_descriptor(execution_contract)['digest']
    execution_ticket = {
        'artifact_type': 'execution_ticket',
        'schema_version': 'v0.2',
        'ticket_id': 'test-ticket',
        'approval': {'status': 'approve'},
        'execution_limits': {'one_shot': True, 'max_runs': 1},
        'integrity': {'ticket_binds_execution_contract_digest': digest, 'profile': 'test-integrity-only'},
        'signature': {'mode': 'not_signed_integrity_only', 'identity_signature_required': False},
    }
    ticket_gate = {'status': 'passed', 'ticket_id': 'test-ticket', 'execution_contract_digest': digest}
    return execution_ticket, execution_contract, ticket_gate


def test_control_gate_adapter_allows_dry_run_with_published_govengine_gate() -> None:
    ticket, contract, ticket_gate = _ticket_and_contract()

    result = evaluate_govengine_control_gate(
        dry_run=True,
        require_execution_ticket=True,
        execution_ticket_gate=ticket_gate,
        execution_ticket=ticket,
        execution_contract=contract,
    )

    assert result['status'] == 'allowed'
    assert result['available'] is True
    assert result['allowed'] is True
    assert result['runner_profile'] == 'dry-run'
    assert result['state_index']['status'] == 'ready'
    assert result['signature_gate']['allowed'] is True


def test_control_gate_adapter_marks_ravenclaw_as_host_runner_for_live_profile() -> None:
    ticket, contract, ticket_gate = _ticket_and_contract()

    result = evaluate_govengine_control_gate(
        dry_run=False,
        require_execution_ticket=True,
        execution_ticket_gate=ticket_gate,
        execution_ticket=ticket,
        execution_contract=contract,
    )

    assert result['status'] == 'allowed'
    assert result['runner_profile'] == 'ravenclaw-host'
    assert result['allowed'] is True


def test_control_gate_adapter_stays_out_when_ticket_gate_not_required() -> None:
    result = evaluate_govengine_control_gate(
        dry_run=True,
        require_execution_ticket=False,
        execution_ticket_gate=None,
        execution_ticket=None,
        execution_contract=None,
    )

    assert result == {
        'status': 'not_required',
        'reason_code': 'execution_ticket_not_required',
        'available': False,
    }
