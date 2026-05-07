from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sclite.integrity import artifact_descriptor

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from executor import ExecutionEngine  # type: ignore
from govengine.execution.approved_spec import approved_execution_steps, validate_approved_execution_spec
from govengine.execution.ticket_gate import APPROVED_TICKET_STATUSES, validate_execution_ticket_gate


def _approved_spec() -> dict:
    return {
        'spec_version': '2026-03-18.approved.v1',
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'resolved_tool': 'curl',
        'execution_mode': 'normalized',
        'approval': {'decision': 'approve', 'reason': 'ok'},
        'execution_truth': {
            'artifact_type': 'approved_execution_spec',
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
        },
    }


def _ticket_for(raw_steps: list[dict], *, status: str = 'approved_for_dry_run') -> tuple[dict, dict]:
    execution_contract = {
        'artifact_type': 'execution_contract',
        'schema_version': 'v0.2',
        'contract_id': 'contract-1',
        'execution_shape': {'plan': raw_steps},
    }
    digest = artifact_descriptor(execution_contract)['digest']
    execution_ticket = {
        'artifact_type': 'execution_ticket',
        'schema_version': 'v0.2',
        'ticket_id': 'ticket-1',
        'approval': {'status': status},
        'execution_limits': {'one_shot': True, 'max_runs': 1},
        'integrity': {'ticket_binds_execution_contract_digest': digest, 'profile': 'test'},
    }
    return execution_ticket, execution_contract


def test_govengine_approved_spec_helpers_match_engine_wrapper() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec()

    assert engine._validate_approved_execution_spec(approved) == validate_approved_execution_spec(approved)
    assert engine._approved_execution_steps(approved) == approved_execution_steps(approved)


def test_govengine_ticket_gate_matches_engine_wrapper() -> None:
    engine = ExecutionEngine()
    approved = _approved_spec()
    raw_steps = approved_execution_steps(approved)
    ticket, contract = _ticket_for(raw_steps)

    assert 'approved_for_dry_run' in APPROVED_TICKET_STATUSES
    assert engine._validate_execution_ticket_gate(
        approved,
        execution_ticket=ticket,
        execution_contract=contract,
        raw_steps=raw_steps,
    ) == validate_execution_ticket_gate(
        approved,
        execution_ticket=ticket,
        execution_contract=contract,
        raw_steps=raw_steps,
    )


@pytest.mark.parametrize('status', ['approve', 'approved', 'approved_for_dry_run'])
def test_govengine_ticket_gate_accepts_positive_statuses(status: str) -> None:
    approved = _approved_spec()
    raw_steps = approved_execution_steps(approved)
    ticket, contract = _ticket_for(raw_steps, status=status)

    result = validate_execution_ticket_gate(approved, execution_ticket=ticket, execution_contract=contract, raw_steps=raw_steps)

    assert result['status'] == 'passed'
    assert result['ticket_id'] == 'ticket-1'


def test_govengine_ticket_gate_rejects_shape_mismatch() -> None:
    approved = _approved_spec()
    raw_steps = approved_execution_steps(approved)
    ticket, contract = _ticket_for([{'tool': 'curl', 'args': ['https://different.example']}])

    with pytest.raises(ValueError, match='execution_ticket_args_mismatch:1'):
        validate_execution_ticket_gate(approved, execution_ticket=ticket, execution_contract=contract, raw_steps=raw_steps)
