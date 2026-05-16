from __future__ import annotations

"""Ravenclaw compatibility check for GovEngine kernel/profile boundary reports."""

from importlib import import_module
from typing import Any, Mapping


EXPECTED_SURFACES = (
    'artifact_governance_core',
    'controlled_execution_core',
    'security_profile_helpers',
)


def govengine_boundary_report_available() -> bool:
    return _boundary_report_factory() is not None


def ravenclaw_boundary_status() -> dict[str, Any]:
    factory = _boundary_report_factory()
    if factory is None:
        return {
            'status': 'unavailable',
            'source': None,
            'reason_code': 'govengine_boundary_report_unavailable',
            'expected_entrypoint': 'govengine.kernel_boundary_report',
            'non_claims': [
                'Does not require unreleased GovEngine main for public install validation.',
                'Does not authorize live execution or adapter work.',
            ],
        }
    report = factory()
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


def _boundary_report_factory():
    try:
        govengine = import_module('govengine')
    except ModuleNotFoundError:
        return None
    return getattr(govengine, 'kernel_boundary_report', None)
