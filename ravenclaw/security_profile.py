from __future__ import annotations

"""Ravenclaw security-profile boundary metadata.

This module is Ravenclaw-owned.  It describes the security runtime/profile that
consumes GovEngine and SCLite surfaces; it does not create a carrier adapter or
move Ravenclaw security semantics into GovEngine.
"""

from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 'v0.1'
PROFILE_NAME = 'ravenclaw-security'
PROFILE_DOMAIN = 'security-research-runtime'

REQUIRED_GOVENGINE_SURFACES = (
    'artifact_governance_core',
    'planning_contracts_core',
    'admission_policy_core',
    'evidence_review_core',
    'controlled_execution_core',
    'security_profile_helpers',
)

REQUIRED_REFERENCE_PATHS = (
    'references/ravenclaw-security-profile-boundary.md',
    'references/openclaw-adapter-readiness-packet-2026-05-20.md',
    'references/openclaw-redaction-output-matrix.md',
    'references/openclaw-approval-ux-sketch.md',
    'references/openclaw-command-authority-and-rollback-tests.md',
    'references/carrier-readiness-checklist.md',
    'references/openclaw-adapter-contract-map.md',
)

OWNED_SEMANTICS = (
    'security_research_runtime_profile',
    'finding_taxonomy',
    'scope_and_policy_interpretation',
    'logdash_operator_visibility',
    'public_demo_and_snapshot_projection',
    'host_adapter_projection',
)

EXTERNAL_AUTHORITIES = {
    'govengine': (
        'kernel_boundary_report',
        'runtime_shell',
        'planning',
        'admission',
        'execution.supervision',
        'review',
        'security_profile',
    ),
    'sclite': (
        'lifecycle_schema_validation',
        'artifact_chain_validation',
        'review_bundle_verdicts',
    ),
}

ADAPTER_READINESS_GATES = (
    'scope_ux',
    'redaction',
    'command_authority',
    'lifecycle_artifacts',
    'rollback',
    'public_private_boundary',
)

FORBIDDEN_PROFILE_CLAIMS = (
    'govengine_kernel_ownership',
    'sclite_schema_authority',
    'carrier_adapter_implementation',
    'live_execution_authority',
    'credential_or_key_store',
    'production_deployment_readiness',
)


def security_profile_manifest() -> dict[str, Any]:
    return {
        'artifact_type': 'ravenclaw_security_profile_manifest',
        'schema_version': SCHEMA_VERSION,
        'profile': {
            'name': PROFILE_NAME,
            'domain': PROFILE_DOMAIN,
            'role': 'reference_security_runtime_profile',
            'runtime_owner': 'ravenclaw',
        },
        'package_chain': {
            'ravenclaw': '0.16.0',
            'govengine': '>=0.7.0,<0.8',
            'sclite-core': '>=0.5.1,<0.6',
        },
        'required_govengine_surfaces': list(REQUIRED_GOVENGINE_SURFACES),
        'owned_semantics': list(OWNED_SEMANTICS),
        'external_authorities': {key: list(value) for key, value in EXTERNAL_AUTHORITIES.items()},
        'adapter_readiness': {
            'target_carrier': 'openclaw',
            'status': 'readiness_packet_only',
            'packet_path': 'references/openclaw-adapter-readiness-packet-2026-05-20.md',
            'required_gates': list(ADAPTER_READINESS_GATES),
            'carrier_order': ['openclaw', 'mcp_later', 'a2a_last_or_example_first'],
        },
        'required_reference_paths': list(REQUIRED_REFERENCE_PATHS),
        'forbidden_profile_claims': list(FORBIDDEN_PROFILE_CLAIMS),
        'non_claims': [
            'Does not make Ravenclaw own GovEngine kernel APIs.',
            'Does not make Ravenclaw own SCLite schemas or review-bundle verdict authority.',
            'Does not implement OpenClaw, MCP, or A2A adapters.',
            'Does not authorize live target execution.',
            'Does not claim production deployment readiness.',
        ],
    }


def evaluate_security_profile_manifest(
    manifest: Mapping[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    profile = manifest.get('profile') if isinstance(manifest.get('profile'), Mapping) else {}
    adapter = manifest.get('adapter_readiness') if isinstance(manifest.get('adapter_readiness'), Mapping) else {}
    package_chain = manifest.get('package_chain') if isinstance(manifest.get('package_chain'), Mapping) else {}
    required_paths = [str(path) for path in manifest.get('required_reference_paths', [])]

    checks = {
        'artifact_type': manifest.get('artifact_type') == 'ravenclaw_security_profile_manifest',
        'schema_version': manifest.get('schema_version') == SCHEMA_VERSION,
        'profile_name': profile.get('name') == PROFILE_NAME,
        'profile_domain': profile.get('domain') == PROFILE_DOMAIN,
        'package_chain': package_chain.get('govengine') == '>=0.7.0,<0.8'
        and package_chain.get('sclite-core') == '>=0.5.1,<0.6',
        'govengine_surfaces': list(manifest.get('required_govengine_surfaces', [])) == list(REQUIRED_GOVENGINE_SURFACES),
        'ravenclaw_owned_semantics': set(OWNED_SEMANTICS).issubset(set(str(item) for item in manifest.get('owned_semantics', []))),
        'adapter_readiness_packet_only': adapter.get('status') == 'readiness_packet_only',
        'adapter_readiness_gates': list(adapter.get('required_gates', [])) == list(ADAPTER_READINESS_GATES),
        'carrier_order': list(adapter.get('carrier_order', [])) == ['openclaw', 'mcp_later', 'a2a_last_or_example_first'],
        'forbidden_claims': set(FORBIDDEN_PROFILE_CLAIMS).issubset(
            set(str(item) for item in manifest.get('forbidden_profile_claims', []))
        ),
    }
    missing_paths: list[str] = []
    if root is not None:
        missing_paths = [path for path in required_paths if not (root / path).exists()]
        checks['required_reference_paths'] = not missing_paths
    failed = [name for name, passed in checks.items() if not passed]
    return {
        'status': 'passed' if not failed else 'failed',
        'profile_name': profile.get('name'),
        'profile_domain': profile.get('domain'),
        'checks': checks,
        'failed_checks': failed,
        'missing_paths': missing_paths,
        'non_claims': list(manifest.get('non_claims', [])),
    }


def ravenclaw_security_profile_status(root: Path | None = None) -> dict[str, Any]:
    return evaluate_security_profile_manifest(security_profile_manifest(), root=root)
