from __future__ import annotations

from typing import Any, Dict, Iterable

from evaluation_replay import replay_decision_bundle  # type: ignore


FIXTURE_SCHEMA_VERSION = 'phase5-replay-fixture-v1'


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _safe_str(value: Any) -> str:
    return str(value or '').strip()


def validate_replay_fixture(fixture: Dict[str, Any] | None) -> Dict[str, Any]:
    raw = _safe_dict(fixture)
    if _safe_str(raw.get('schema_version') or FIXTURE_SCHEMA_VERSION) != FIXTURE_SCHEMA_VERSION:
        raise ValueError('fixture_schema_version_invalid')
    fixture_id = _safe_str(raw.get('fixture_id') or raw.get('id'))
    if not fixture_id:
        raise ValueError('fixture_missing_id')
    bundle = _safe_dict(raw.get('bundle'))
    if not bundle:
        raise ValueError('fixture_missing_bundle')
    expected = _safe_dict(raw.get('expected'))
    result = replay_decision_bundle(bundle)
    mismatches: list[str] = []
    for key in ('status', 'requested_action', 'effective_action'):
        if key in expected and str(expected.get(key)) != str(result.get(key)):
            mismatches.append(f'{key}:{result.get(key)}!={expected.get(key)}')
    for key in (
        'candidate',
        'confirmed',
        'policy_blocked',
        'owner_gate_pending',
        'contamination_excluded',
        'auth_prereq_missing',
        'state_prereq_missing',
        'lineage_complete',
        'useful_negative',
    ):
        if key in expected and bool(expected.get(key)) != bool(result.get(key)):
            mismatches.append(f'{key}:{result.get(key)}!={expected.get(key)}')
    for key in (
        'evidence_class',
        'semantic_outcome_class',
    ):
        if key in expected and str(expected.get(key)) != str(result.get(key)):
            mismatches.append(f'{key}:{result.get(key)}!={expected.get(key)}')
    contains = [str(x) for x in _safe_list(expected.get('metric_exclusion_contains')) if _safe_str(x)]
    if contains:
        exclusions = [str(x) for x in _safe_list(result.get('metric_exclusion_reasons'))]
        for item in contains:
            if item not in exclusions:
                mismatches.append(f'metric_exclusion_missing:{item}')
    return {
        'fixture_id': fixture_id,
        'passed': len(mismatches) == 0,
        'mismatches': mismatches,
        'result': result,
    }


def evaluate_fixture_corpus(fixtures: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results = [validate_replay_fixture(item) for item in fixtures if isinstance(item, dict)]
    return {
        'schema_version': 'phase5-replay-fixture-results-v1',
        'total': len(results),
        'passed': sum(1 for item in results if bool(item.get('passed', False))),
        'failed': sum(1 for item in results if not bool(item.get('passed', False))),
        'results': results,
    }
