from __future__ import annotations

"""Ravenclaw required check for GovEngine kernel/profile boundary reports."""

from typing import Any, Mapping

from govengine import kernel_boundary_report


EXPECTED_SURFACES = (
    'artifact_governance_core',
    'planning_contracts_core',
    'admission_policy_core',
    'evidence_review_core',
    'domain_profile_sdk',
    'runtime_contract_proofs',
    'controlled_execution_core',
    'security_profile_helpers',
)


def govengine_boundary_report_available() -> bool:
    return callable(kernel_boundary_report)


def ravenclaw_boundary_status() -> dict[str, Any]:
    report = kernel_boundary_report()
    payload = report.as_dict() if hasattr(report, 'as_dict') else dict(report)
    return evaluate_boundary_report(payload, source='govengine.kernel_boundary_report')


def evaluate_boundary_report(report: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    profiles = list(report.get('profiles') or [])
    surfaces = list(report.get('surfaces') or [])
    boundary = report.get('boundary') if isinstance(report.get('boundary'), Mapping) else {}
    profile_names = [str(profile.get('name')) for profile in profiles if isinstance(profile, Mapping)]
    surface_names = [str(surface.get('name')) for surface in surfaces if isinstance(surface, Mapping)]
    forbidden = [str(item) for item in boundary.get('forbidden_profile_ownership', [])] if isinstance(boundary, Mapping) else []

    checks = {
        'artifact_type': report.get('artifact_type') == 'govengine_boundary_report',
        'ravenclaw_profile_present': 'ravenclaw' in profile_names,
        'surface_index_matches': surface_names == list(EXPECTED_SURFACES),
        'live_execution_forbidden': 'live_execution_authority' in forbidden,
        'carrier_adapter_forbidden': 'carrier_adapter_ownership' in forbidden,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        'status': 'passed' if not failed else 'failed',
        'source': source,
        'profile_names': profile_names,
        'surface_names': surface_names,
        'checks': checks,
        'failed_checks': failed,
        'summary': report.get('summary') if isinstance(report.get('summary'), Mapping) else {},
        'non_claims': [
            'Boundary report consumption does not make Ravenclaw own GovEngine kernel APIs.',
            'Boundary report consumption does not authorize live execution or adapter work.',
        ],
    }
