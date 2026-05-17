from __future__ import annotations

"""Ravenclaw host-side demo trust helpers for GovEngine signing ports.

This module keeps production PKI out of Ravenclaw/GovEngine. The current
published GovEngine package owns the demo signer/verifier ports; Ravenclaw only
projects their public-safe result into demo artifacts.
"""
from typing import Any, Mapping

from govengine.core import ArtifactDescriptor
from govengine.signing import DemoDigestSigner, DemoDigestVerifier, SigningRequest


def _artifact_descriptor_from_sclite(descriptor: Mapping[str, Any], *, fallback_type: str = 'artifact') -> ArtifactDescriptor:
    return ArtifactDescriptor(
        artifact_type=str(descriptor.get('artifact_type') or fallback_type),
        schema_version=str(descriptor.get('schema_version') or ''),
        digest=str(descriptor.get('digest') or ''),
    )


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
    signer = DemoDigestSigner(signer_id=signer_id)
    signing = signer.sign(SigningRequest(descriptor=descriptor, purpose=purpose, metadata={'demo_only': True}))
    verification = DemoDigestVerifier(verifier_id=verifier_id, allowed_signer_ids=(signer_id,)).verify(descriptor, signing.signature)

    signature = signing.signature.as_dict()
    trust = verification.as_dict()
    signature['source'] = 'govengine_demo_ports'
    trust['source'] = 'govengine_demo_ports'
    return {
        'signature': signature,
        'trust_decision': trust,
        'non_claims': [
            'demo_signature_does_not_prove_real_world_identity',
            'no_pki_ca_kms_or_key_store_in_govengine',
            'signature_binds_descriptor_digest_for_fixture_review_only',
        ],
    }
