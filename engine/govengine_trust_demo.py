from __future__ import annotations

"""Ravenclaw host-side demo trust helpers for GovEngine signing ports.

This module keeps production PKI out of Ravenclaw/GovEngine. It uses the
GovEngine demo signing ports when available, and a compatibility fallback with
the same public-safe shape for environments pinned to an older GovEngine line.
"""

from hashlib import sha256
from typing import Any, Mapping

from govengine.core import ArtifactDescriptor
from govengine.signing import SignatureEnvelope, SigningRequest, SigningResult, VerificationResult


def _artifact_descriptor_from_sclite(descriptor: Mapping[str, Any], *, fallback_type: str = 'artifact') -> ArtifactDescriptor:
    return ArtifactDescriptor(
        artifact_type=str(descriptor.get('artifact_type') or fallback_type),
        schema_version=str(descriptor.get('schema_version') or ''),
        digest=str(descriptor.get('digest') or ''),
    )


def _fallback_demo_sign_and_verify(
    descriptor: ArtifactDescriptor,
    *,
    purpose: str,
    signer_id: str,
    verifier_id: str,
) -> tuple[SigningResult, VerificationResult]:
    payload = f"{descriptor.digest}|{signer_id}|{purpose}".encode('utf-8')
    signature = SignatureEnvelope(
        mode='detached_demo_digest',
        signer_id=signer_id,
        signature='demo:' + sha256(payload).hexdigest(),
        binds_digest=descriptor.digest,
        algorithm='demo-sha256-digest-binding',
        metadata={'purpose': purpose, 'demo_only': True, 'source': 'ravenclaw_compat_demo'},
    )
    signing = SigningResult(status='signed', signature=signature)
    verification = VerificationResult(
        status='passed',
        trust_status='trusted',
        verifier_id=verifier_id,
        metadata={'demo_only': True, 'signer_id': signer_id, 'purpose': purpose, 'source': 'ravenclaw_compat_demo'},
    )
    return signing, verification


def demo_sign_execution_contract(
    execution_contract_descriptor: Mapping[str, Any],
    *,
    purpose: str = 'execution_contract_ticket_binding',
    signer_id: str = 'ravenclaw-demo-signer',
    verifier_id: str = 'ravenclaw-demo-verifier',
) -> dict[str, Any]:
    """Return public-safe demo signature/trust metadata for an execution contract.

    The signature binds to the SCLite descriptor digest. It is a fixture/demo
    trust example only; it does not prove real-world signer identity.
    """

    descriptor = _artifact_descriptor_from_sclite(execution_contract_descriptor, fallback_type='execution_contract')
    source = 'ravenclaw_compat_demo'
    try:
        from govengine.signing import DemoDigestSigner, DemoDigestVerifier  # type: ignore

        signer = DemoDigestSigner(signer_id=signer_id)
        signing = signer.sign(SigningRequest(descriptor=descriptor, purpose=purpose, metadata={'demo_only': True}))
        verification = DemoDigestVerifier(verifier_id=verifier_id, allowed_signer_ids=(signer_id,)).verify(descriptor, signing.signature)
        source = 'govengine_demo_ports'
    except (ImportError, AttributeError):
        signing, verification = _fallback_demo_sign_and_verify(descriptor, purpose=purpose, signer_id=signer_id, verifier_id=verifier_id)

    signature = signing.signature.as_dict()
    trust = verification.as_dict()
    signature['source'] = source
    trust['source'] = source
    return {
        'signature': signature,
        'trust_decision': trust,
        'non_claims': [
            'demo_signature_does_not_prove_real_world_identity',
            'no_pki_ca_kms_or_key_store_in_govengine',
            'signature_binds_descriptor_digest_for_fixture_review_only',
        ],
    }
