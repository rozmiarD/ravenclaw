from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.api import GovApiError  # type: ignore
from govengine.execution.supervision import validate_supervision_plan  # type: ignore
from govengine_runner_supervision_projection import (  # type: ignore
    build_gov_runner_supervision_projection,
    validate_existing_runner_receipt_projection,
)


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
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com/']}],
        },
    }


def test_runner_supervision_projection_validates_approved_spec_dry_run_boundary() -> None:
    projection = build_gov_runner_supervision_projection(
        _approved_spec(),
        request_id='request-1',
        execution_ticket_gate={'status': 'passed'},
    )

    assert projection['artifact_type'] == 'ravenclaw_govengine_runner_supervision_projection'
    assert projection['runner_request']['request_id'] == 'request-1'
    assert projection['supervision_plan']['receipt_required'] is True
    assert projection['runner_lease']['state'] == 'active'
    assert projection['runner_receipt']['status'] == 'dry-run'
    assert 'does_not_enable_live_backend_by_default' in projection['non_claims']


def test_runner_supervision_projection_blocks_live_backend_by_default() -> None:
    with pytest.raises(GovApiError, match='live_backend_disabled'):
        build_gov_runner_supervision_projection(_approved_spec(), request_id='live-1', dry_run=False)


def test_existing_runner_receipt_projection_must_match_request_steps() -> None:
    good = {
        'status': 'dry-run',
        'request_id': 'request-1',
        'source': 'approved_execution_spec',
        'step_results': [{'index': 0, 'status': 'dry-run', 'reason_code': 'dry_run_requested'}],
    }
    checked = validate_existing_runner_receipt_projection(_approved_spec(), good, request_id='request-1')
    assert checked['request_id'] == 'request-1'

    bad = dict(good)
    bad['step_results'] = [{'index': 99, 'status': 'dry-run'}]
    with pytest.raises(GovApiError, match='runner_receipt_step_mismatch'):
        validate_existing_runner_receipt_projection(_approved_spec(), bad, request_id='request-1')


def test_supervision_metadata_rejects_raw_prompt_claims() -> None:
    with pytest.raises(GovApiError, match='forbidden_supervision_metadata:prompt'):
        validate_supervision_plan({
            'plan_id': 'bad',
            'request_id': 'request-1',
            'metadata': {'prompt': 'run this'},
        })
