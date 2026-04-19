from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Tuple



def truncate_text(value: str, limit: int = 4000) -> str:
    if not value:
        return ''
    value = str(value)
    if len(value) <= limit:
        return value
    return value[:limit] + '...<truncated>'



def run_analysis_stage(
    *,
    cfg: Dict[str, Any],
    engine_res: Dict[str, Any],
    objective: str,
    target: str,
    task_success_criteria: str,
    campaign_success_criteria: str,
    task_family: str,
    acceptance_checks: str,
    evidence_required: str,
    recent_context: List[Dict[str, Any]],
    json_retries: int,
    prompt_token_budget: int,
    analysis_bytes: int,
    min_bytes: int,
    signal: bool,
    interesting_http: bool,
    ask_json_fn: Callable[..., Dict[str, Any]],
    log_stage_fn: Callable[[str, str, str, str], None],
) -> Tuple[Dict[str, Any], Dict[str, Any], float | None]:
    should_analyze = (
        cfg.get('enable_analysis', False)
        and engine_res.get('status') not in {None, 'dry-run'}
        and (analysis_bytes >= min_bytes or interesting_http)
        and (signal or interesting_http)
    )
    stdout_snip = engine_res.get('stdout') or ''
    stderr_snip = engine_res.get('stderr') or ''
    if should_analyze:
        analysis_payload = {
            'objective': objective,
            'target': target,
            'task_success_criteria': task_success_criteria,
            'campaign_success_criteria': campaign_success_criteria,
            'task_family': task_family,
            'acceptance_checks': acceptance_checks,
            'evidence_required': evidence_required,
            'engine_status': engine_res.get('status'),
            'returncode': engine_res.get('returncode'),
            'stdout_excerpt': truncate_text(stdout_snip, 3000),
            'stderr_excerpt': truncate_text(stderr_snip, 1200),
            'recent_context': recent_context[-3:],
        }
        try:
            t0 = time.perf_counter()
            analysis = ask_json_fn(
                'analysis',
                base_prompt=(
                    "You are ANALYSIS in RAVEN-CLAW strict pipeline. "
                    "Separate facts from hypotheses. "
                    "Return observations as direct evidence only; return evidence_artifacts as concrete reproducible artifacts; return security_signals as cautious interpretations derived from those observations; do not overclaim impact. "
                    "Include next_family_hint when a family pivot is justified by evidence. next_step must be conservative and evidence-driven. "
                    f"Payload: {json.dumps(analysis_payload, ensure_ascii=False)}"
                ),
                contract_hint='{"observations":["..."],"evidence_artifacts":["..."],"security_signals":["..."],"findings":["..."],"risk":"low|medium|high","confidence":"low|medium|high","next_family_hint":"recon|subdomain_expansion|historical_url_mining|content_discovery|tls_assessment|secret_hunt|authz|auth_flow|logic|client_input|input_tamper|redirect_trust|generic","next_step":"...","success_criteria_eval":"met|partial|not_met","success_evidence":["..."],"success_gap":"..."}',
                retries=json_retries,
                prompt_token_budget=prompt_token_budget,
            )
            context_analysis = {
                'observations': analysis.get('observations', [])[:3],
                'evidence_artifacts': analysis.get('evidence_artifacts', [])[:3],
                'security_signals': analysis.get('security_signals', [])[:3],
                'findings': analysis.get('findings', [])[:3],
                'risk': analysis.get('risk'),
                'confidence': analysis.get('confidence'),
                'next_family_hint': analysis.get('next_family_hint'),
            }
            log_stage_fn('ANALYSIS', 'analysis', 'success', json.dumps(analysis, ensure_ascii=False)[:240])
            return analysis, context_analysis, round(time.perf_counter() - t0, 4)
        except Exception as e:
            log_stage_fn('ANALYSIS', 'analysis', 'failed', str(e))
            log_stage_fn('ANALYSIS', 'analysis_contract_failure', 'warning', str(e)[:220])
            return {'error': 'analysis_contract_failure', 'detail': str(e)}, {'error': 'analysis_contract_failure'}, None
    status = 'disabled' if not cfg.get('enable_analysis', False) else 'skipped'
    if engine_res.get('status') == 'dry-run':
        reason = 'dry_run'
    elif analysis_bytes < min_bytes and not interesting_http:
        reason = 'insufficient_output'
    elif not signal and not interesting_http:
        reason = 'low_signal'
    elif interesting_http:
        reason = 'interesting_http_signal_analyzed'
    else:
        reason = 'no_signal'
    log_stage_fn('ANALYSIS', 'analysis', status, reason)
    return {'status': status, 'reason': reason}, {}, None



def run_light_stage(
    *,
    cfg: Dict[str, Any],
    signal: bool,
    analysis_payload_for_light: Dict[str, Any],
    engine_res: Dict[str, Any],
    objective: str,
    target: str,
    recent_context: List[Dict[str, Any]],
    json_retries: int,
    prompt_token_budget: int,
    ask_json_fn: Callable[..., Dict[str, Any]],
    log_stage_fn: Callable[[str, str, str, str], None],
) -> Tuple[Dict[str, Any], Dict[str, Any], float | None]:
    should_light = cfg.get('enable_light', False) and bool(signal)
    stdout_snip = engine_res.get('stdout') or ''
    stderr_snip = engine_res.get('stderr') or ''
    if should_light:
        light_context = {
            'analysis': analysis_payload_for_light,
            'engine': {
                'status': engine_res.get('status'),
                'returncode': engine_res.get('returncode'),
                'stdout_excerpt': truncate_text(stdout_snip, 1200),
                'stderr_excerpt': truncate_text(stderr_snip, 600),
            },
            'objective': objective,
            'target': target,
            'recent_context': recent_context[-2:],
        }
        try:
            log_stage_fn('LIGHT', 'light_wait', 'in_progress', 'waiting_for_light_response timeout=45s')
            t0 = time.perf_counter()
            light = ask_json_fn(
                'light',
                base_prompt=(
                    "Return ONLY JSON. You are LIGHT, a formatter not a decision-maker. "
                    "Summarize only facts already present in engine/analysis. "
                    "Do not introduce new conclusions, risks, or attack ideas. "
                    "Produce one concise operator summary and one conservative next_step. "
                    f"Context: {json.dumps(light_context, ensure_ascii=False)}"
                ),
                contract_hint='{"summary":"...","next_step":"..."}',
                retries=max(0, json_retries - 1),
                timeout=45,
                prompt_token_budget=prompt_token_budget,
            )
            context_light = {'summary': light.get('summary'), 'next_step': light.get('next_step')}
            log_stage_fn('LIGHT', 'light_summary', 'success', json.dumps(light, ensure_ascii=False)[:240])
            return light, context_light, round(time.perf_counter() - t0, 4)
        except Exception as e1:
            try:
                log_stage_fn('LIGHT', 'light_fallback_wait', 'in_progress', 'waiting_for_analysis_fallback timeout=35s')
                light = ask_json_fn(
                    'analysis',
                    base_prompt=(
                        "Return ONLY JSON in LIGHT contract: summary + next_step. "
                        "Summarize facts only; no new conclusions. "
                        f"Context: {json.dumps(light_context, ensure_ascii=False)}"
                    ),
                    contract_hint='{"summary":"...","next_step":"..."}',
                    retries=0,
                    timeout=35,
                    prompt_token_budget=prompt_token_budget,
                )
                out = {**light, 'source': 'analysis_fallback'}
                context_light = {'summary': light.get('summary'), 'next_step': light.get('next_step'), 'source': 'analysis_fallback'}
                log_stage_fn('LIGHT', 'light_summary', 'warning', 'light_non_json -> analysis_fallback')
                log_stage_fn('LIGHT', 'light_fallback_used', 'warning', 'source=analysis_fallback')
                return out, context_light, None
            except Exception as e2:
                fallback_summary = (
                    f"Execution status: {engine_res.get('status') or 'unknown'}; "
                    f"auditor: unknown; "
                    f"objective: {objective}"
                )
                fallback_reco = 'Review engine output and continue only with already-approved, evidence-driven next steps.'
                out = {'summary': fallback_summary, 'next_step': fallback_reco, 'source': 'fallback_after_contract_failure'}
                context_light = {'error': 'light_contract_failure', 'fallback': True}
                log_stage_fn('LIGHT', 'light_summary', 'warning', f"fallback_used: {str(e1)[:120]} | {str(e2)[:120]}")
                log_stage_fn('LIGHT', 'light_fallback_used', 'warning', 'source=local_fallback_after_contract_failure')
                return out, context_light, None
    log_stage_fn('LIGHT', 'light_summary', 'disabled', 'light_disabled')
    return {'status': 'disabled', 'reason': 'light_disabled'}, {}, None
