from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

from govengine.review import (
    qualify_evidence_claim,
    validate_evidence_claim,
    validate_evidence_requirement,
    validate_review_result,
)


def _text(value: Any, default: str = '') -> str:
    out = str(value if value is not None else '').strip()
    return out if out else default


def _subject_ref(value: Any) -> tuple[str, bool]:
    raw = _text(value)
    if not raw:
        return 'sha256:' + sha256(b'ravenclaw-evidence-review').hexdigest()[:24], False
    return 'sha256:' + sha256(raw.encode('utf-8')).hexdigest()[:24], True


def build_gov_review_projection(
    *,
    subject: Any,
    receipt_ref: str,
    receipt_status: str,
    claim_type: str = 'execution_truth',
    claim_id: str = 'ravenclaw-claim',
    requirement_id: str = 'ravenclaw-requirement',
) -> dict[str, Any]:
    subject_ref, redacted = _subject_ref(subject)
    requirement = validate_evidence_requirement({
        'requirement_id': requirement_id,
        'subject_ref': subject_ref,
        'min_receipt_status': 'dry-run',
        'metadata': {'source': 'ravenclaw_review_projection', 'subject_redacted': redacted},
    })
    claim = validate_evidence_claim({
        'claim_id': claim_id,
        'subject_ref': subject_ref,
        'claim_type': claim_type,
        'receipt_refs': [receipt_ref],
        'metadata': {'source': 'ravenclaw_review_projection', 'subject_redacted': redacted},
    })
    qualification = qualify_evidence_claim(claim, requirement, receipt_status=receipt_status)
    review = validate_review_result({
        'review_id': f'{claim_id}:review',
        'subject_ref': subject_ref,
        'verdict': 'passed' if qualification.result == 'supported' else 'failed',
        'qualification_refs': [qualification.qualification_id],
        'metadata': {'source': 'ravenclaw_review_projection', 'subject_redacted': redacted},
    })
    return {
        'artifact_type': 'ravenclaw_govengine_review_projection',
        'profile': 'ravenclaw-security',
        'evidence_requirement': requirement.as_dict(),
        'evidence_claim': claim.as_dict(),
        'evidence_qualification': qualification.as_dict(),
        'review_result': review.as_dict(),
        'non_claims': [
            'ravenclaw_owns_finding_taxonomy',
            'sclite_owns_review_bundle_verdicts',
            'does_not_expose_raw_target_or_output_to_govengine',
        ],
    }
