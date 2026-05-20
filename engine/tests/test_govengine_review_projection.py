from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.review import validate_evidence_claim, validate_review_result  # type: ignore
from govengine_review_projection import build_gov_review_projection  # type: ignore


def test_review_projection_supports_execution_truth_from_dry_run_receipt_without_raw_target() -> None:
    projection = build_gov_review_projection(
        subject='https://api.example.com/account/123',
        receipt_ref='receipt-1',
        receipt_status='dry-run',
        claim_type='execution_truth',
        claim_id='claim-1',
    )

    claim = validate_evidence_claim(projection['evidence_claim'])
    review = validate_review_result(projection['review_result'])

    assert claim.subject_ref.startswith('sha256:')
    assert projection['evidence_qualification']['result'] == 'supported'
    assert review.verdict == 'passed'
    assert 'api.example.com' not in str(projection)


def test_review_projection_rejects_live_vulnerability_claim_from_dry_run_receipt() -> None:
    projection = build_gov_review_projection(
        subject='https://api.example.com/account/123',
        receipt_ref='receipt-1',
        receipt_status='dry-run',
        claim_type='live_vulnerability',
        claim_id='claim-live',
    )

    assert projection['evidence_qualification']['result'] == 'rejected'
    assert projection['evidence_qualification']['reason_code'] == 'live_claim_not_supported_by_receipt'
    assert projection['review_result']['verdict'] == 'failed'
