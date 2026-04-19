from __future__ import annotations

import re
from typing import Any, Dict, List


AUTH_FAMILIES = {'authz', 'auth_flow'}
INPUT_FAMILIES = {'client_input', 'input_tamper', 'redirect_trust', 'logic'}
INVENTORY_FAMILIES = {'recon', 'content_discovery', 'historical_url_mining', 'subdomain_expansion', 'tls_assessment', 'secret_hunt'}


def _safe_text(value: Any) -> str:
    return str(value or '').strip().lower()


def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def _normalize_listish(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip().lower() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [part.strip().lower() for part in value.split(',') if part.strip()]
    return []


def _typed_family_eval(task_family: str, success_semantics: Dict[str, Any] | None = None) -> str:
    success_semantics = success_semantics if isinstance(success_semantics, dict) else {}
    success_model = _safe_text(success_semantics.get('success_model'))
    evidence_goal_type = _safe_text(success_semantics.get('evidence_goal_type'))
    expected_signal_type = _safe_text(success_semantics.get('expected_signal_type'))
    if success_model == 'differential_or_stateful_signal' or evidence_goal_type == 'controlled_comparison':
        return 'authz_boundary'
    if success_model == 'surface_expansion' or evidence_goal_type == 'enumeration_gain':
        return 'inventory_growth'
    if expected_signal_type in {'behavior_delta', 'reflection_or_behavior_delta'}:
        return 'input_validation'
    fam = _safe_text(task_family)
    if fam in AUTH_FAMILIES:
        return 'authz_boundary'
    if fam in INPUT_FAMILIES:
        return 'input_validation'
    if fam in INVENTORY_FAMILIES:
        return 'inventory_growth'
    return 'generic'


def high_signal(engine_res: Dict[str, Any], analysis_min_bytes: int = 64) -> bool:
    status = str(engine_res.get('status') or '').lower()
    if status in {'failed', 'error', 'timeout'}:
        return True
    txt = ((engine_res.get('stdout') or '') + ' ' + (engine_res.get('stderr') or '')).lower()
    if len(txt) >= analysis_min_bytes and any(k in txt for k in ['xss', 'idor', 'sqli', 'sql injection', 'csrf', 'ssrf', 'token', 'leak', 'bypass', 'unauthorized', 'forbidden']):
        return True
    return False


def extract_http_codes(engine_res: Dict[str, Any]) -> List[int]:
    txt = f"{engine_res.get('stdout') or ''}\n{engine_res.get('stderr') or ''}"
    codes: List[int] = []
    for m in re.finditer(r"code=(\d{3})", txt):
        try:
            codes.append(int(m.group(1)))
        except Exception:
            pass
    return codes


def interesting_http_signal(engine_res: Dict[str, Any], objective: str) -> bool:
    codes = extract_http_codes(engine_res)
    obj = str(objective or '').lower()
    auth_like = any(k in obj for k in ['auth', 'authz', 'token', 'csrf', 'xss', 'input', 'redirect'])
    if not codes:
        return bool(auth_like)
    if auth_like and any(c in {302, 307, 308, 401, 403} for c in codes):
        return True
    if any(c >= 400 for c in codes):
        return True
    return False


def evaluate_success_criteria(
    criteria: str,
    engine_res: Dict[str, Any],
    summary_text: str,
    analysis: Dict[str, Any] | None = None,
    *,
    task_family: str = '',
    acceptance_checks: Any | None = None,
    evidence_required: Any | None = None,
    success_semantics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    crit = str(criteria or '').strip()
    success_semantics = success_semantics if isinstance(success_semantics, dict) else {}
    typed_family_eval = _typed_family_eval(task_family, success_semantics)
    if not crit:
        return {
            'status': 'not_provided',
            'met': False,
            'evidence': [],
            'gap': 'missing_success_criteria',
            'typed_family_eval': typed_family_eval,
            'success_model': _safe_text(success_semantics.get('success_model')),
            'expected_signal_type': _safe_text(success_semantics.get('expected_signal_type')),
            'evidence_goal_type': _safe_text(success_semantics.get('evidence_goal_type')),
            'acceptance_checks_eval': _normalize_listish(acceptance_checks),
            'evidence_required_eval': _normalize_listish(evidence_required),
        }

    status = _safe_text(engine_res.get('status'))
    rc = engine_res.get('returncode')
    txt = f"{summary_text} {(engine_res.get('stdout') or '')[:1200]} {(engine_res.get('stderr') or '')[:700]}".lower()
    findings = analysis.get('findings', []) if isinstance(analysis, dict) and isinstance(analysis.get('findings'), list) else []
    risk = _safe_text((analysis or {}).get('risk')) if isinstance(analysis, dict) else ''
    security_signals = analysis.get('security_signals', []) if isinstance(analysis, dict) and isinstance(analysis.get('security_signals'), list) else []
    observations = analysis.get('observations', []) if isinstance(analysis, dict) and isinstance(analysis.get('observations'), list) else []

    acceptance_checks_norm = _normalize_listish(acceptance_checks)
    evidence_required_norm = _normalize_listish(evidence_required)
    success_model = _safe_text(success_semantics.get('success_model'))
    expected_signal_type = _safe_text(success_semantics.get('expected_signal_type'))
    evidence_goal_type = _safe_text(success_semantics.get('evidence_goal_type'))

    evidence: List[str] = []
    if status in {'ok', 'success'} and rc in {0, None}:
        evidence.append('engine_ok')
    if any(k in txt for k in ['xss', 'idor', 'sqli', 'sql injection', 'csrf', 'ssrf', 'unauthorized', 'forbidden', 'bypass']):
        evidence.append('security_signal_detected')
    if findings:
        evidence.append('analysis_findings_present')
    if security_signals:
        evidence.append('analysis_security_signals_present')
    if observations:
        evidence.append('analysis_observations_present')
    if risk in {'medium', 'high', 'critical'}:
        evidence.append(f'analysis_risk_{risk}')
    if any(k in txt for k in ['harden', 'mitigation', 'recommendation', 'negative proof']):
        evidence.append('hardening_or_negative_proof')
    if acceptance_checks_norm:
        evidence.append('acceptance_checks_supplied')
    if evidence_required_norm:
        evidence.append('evidence_requirements_supplied')
    if success_model:
        evidence.append(f'success_model:{success_model}')
    if expected_signal_type:
        evidence.append(f'expected_signal_type:{expected_signal_type}')
    if evidence_goal_type:
        evidence.append(f'evidence_goal_type:{evidence_goal_type}')

    evidence_set = set(evidence)
    auth_like_signal = _contains_any(txt, ['401', '403', 'forbidden', 'unauthorized', 'allow', 'deny', 'bypass', 'delta', 'difference'])
    inventory_like_signal = _contains_any(txt, ['endpoint', 'parameter', 'route', 'path', 'subdomain', 'host', 'inventory', 'discovered', 'header']) or bool(observations)
    input_like_signal = _contains_any(txt, ['reflection', 'validation', 'sanit', 'encoding', 'redirect', 'payload', 'control']) or 'analysis_security_signals_present' in evidence_set
    response_diff_signal = _contains_any(txt, ['response diff', 'behavior delta', 'allow/deny', 'asymmetry', 'delta', 'difference', 'mismatch'])
    status_signal = bool(extract_http_codes(engine_res))
    required_hits = set()
    if 'http_status' in evidence_required_norm and status_signal:
        required_hits.add('http_status')
    if 'response_diff' in evidence_required_norm and (response_diff_signal or auth_like_signal):
        required_hits.add('response_diff')
    if 'endpoint_or_header_inventory' in evidence_required_norm and inventory_like_signal:
        required_hits.add('endpoint_or_header_inventory')
    if 'reflection_or_behavior_delta' in evidence_required_norm and (input_like_signal or response_diff_signal):
        required_hits.add('reflection_or_behavior_delta')

    def _result(status_value: str, met: bool, gap: str, evidence_items: List[str]) -> Dict[str, Any]:
        return {
            'status': status_value,
            'met': met,
            'evidence': evidence_items[:8],
            'gap': gap,
            'typed_family_eval': typed_family_eval,
            'success_model': success_model,
            'expected_signal_type': expected_signal_type,
            'evidence_goal_type': evidence_goal_type,
            'acceptance_checks_eval': acceptance_checks_norm,
            'evidence_required_eval': evidence_required_norm,
            'required_evidence_hits': sorted(required_hits),
        }

    if typed_family_eval == 'authz_boundary':
        if 'engine_ok' in evidence_set and (({'http_status', 'response_diff'}.issubset(required_hits)) or auth_like_signal or 'security_signal_detected' in evidence_set or 'analysis_findings_present' in evidence_set):
            return _result('met', True, '', evidence)
        if evidence:
            return _result('partial', False, 'need_clear_allow_deny_or_boundary_evidence', evidence)
        return _result('not_met', False, 'no_authz_boundary_evidence', [])

    if typed_family_eval == 'inventory_growth':
        if 'engine_ok' in evidence_set and (('endpoint_or_header_inventory' in required_hits) or inventory_like_signal):
            return _result('met', True, '', evidence)
        if 'engine_ok' in evidence_set or evidence:
            return _result('partial', False, 'need_reproducible_inventory_growth_evidence', evidence)
        return _result('not_met', False, 'no_inventory_growth_evidence', [])

    if typed_family_eval == 'input_validation':
        if 'engine_ok' in evidence_set and (('reflection_or_behavior_delta' in required_hits) or input_like_signal or 'security_signal_detected' in evidence_set or 'analysis_findings_present' in evidence_set):
            return _result('met', True, '', evidence)
        if evidence:
            return _result('partial', False, 'need_clear_input_or_trust_boundary_evidence', evidence)
        return _result('not_met', False, 'no_input_validation_evidence', [])

    if {'engine_ok', 'security_signal_detected'}.issubset(evidence_set) or {'analysis_findings_present', 'analysis_risk_high'}.issubset(evidence_set) or bool(required_hits):
        return _result('met', True, '', evidence)
    if evidence:
        return _result('partial', False, 'need_stronger_repro_or_impact_evidence', evidence)
    return _result('not_met', False, 'no_security_signal_or_repro_evidence', [])
