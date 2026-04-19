from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from auto_campaign_targets import host_from_target  # type: ignore
from auto_campaign_qualification import compute_signal_assessment  # type: ignore
from runtime_decision_engine import build_runtime_decision  # type: ignore
from signal_contract import (  # type: ignore
    build_signal_contract,
    signal_contract_adaptation_positive,
    signal_contract_host_promise_positive,
    signal_contract_promising,
    signal_contract_signal_positive,
    signal_contract_workflow_promotable,
)


FinalizeResult = Tuple[dict, bool, dict]


def qualify_and_finalize_run(
    *,
    post: Dict[str, Any],
    objective: str,
    target: str,
    mode: str,
    run_index: int,
    decision_label: str,
    owner_override: bool,
    aggression: int,
    error_flag: bool,
    policy_diag_logging: bool,
    force_auth_like_weak_on_http_controls: bool,
    repeated_consistency: bool,
    host_weak_count: dict[str, int],
    quality_telemetry: dict[str, int],
    decision_toggles: Dict[str, Any],
    qualification_mode: str,
    qualification_promising_threshold: str,
    qualify_fn: Callable[[dict], Any],
    can_be_confirmed_fn: Callable[[dict], bool],
    compute_promising_fn: Callable[[dict, str, str], bool],
    finding_lifecycle_fn: Callable[[str, dict], str],
    adaptive_aggression_fn: Callable[[int, str, str, bool], int],
    normalize_pipeline_status_fn: Callable[[str, str, bool], str],
    log_event_fn: Callable[..., None],
) -> FinalizeResult:
    reason_code = str(post['reason_code'])
    summary_text = str(post['summary_text'])
    classification = str(post['classification'])
    planned_cmd = post['planned_cmd']
    signal_codes = post['signal_codes']
    metrics_obj = post['metrics_obj']
    control_cmp = post['control_cmp']
    if policy_diag_logging:
        log_event_fn(
            'AUTO_CAMPAIGN',
            'qualification_input_diag',
            'in_progress',
            f"http_code={metrics_obj.get('code') or '-'};control_cmp={bool(control_cmp.get('performed',False))};control_delta={bool(control_cmp.get('control_delta_observed',False))};repeat={repeated_consistency};force_weak={bool(force_auth_like_weak_on_http_controls)}",
            actor='auto_campaign',
            row_type='service',
        )
    qual = qualify_fn({
        'objective': objective,
        'reason_code': reason_code,
        'signal_codes': signal_codes,
        'summary_text': summary_text,
        'task_family': str(post['run_info'].get('task_family') or post.get('task_family') or ''),
        'http_code': metrics_obj.get('code'),
        'engine_status': str(post['run_info'].get('engine_status') or ''),
        'auditor_decision': str(post['run_info'].get('auditor_decision') or ''),
        'probe_id': f'{run_index}:{mode}',
        'request_fingerprint': (' '.join(str(x) for x in planned_cmd) if isinstance(planned_cmd, list) else str(planned_cmd or ''))[:220],
        'in_scope': True,
        'control_comparison_performed': bool(control_cmp.get('performed', False)),
        'control_delta_observed': bool(control_cmp.get('control_delta_observed', False)),
        'repeated_consistency': repeated_consistency,
        'force_auth_like_weak_on_http_controls': bool(force_auth_like_weak_on_http_controls),
    })
    hkey = host_from_target(target)
    vqv = str(qual.get('verdict') or 'none')
    if hkey and vqv == 'weak_signal':
        host_weak_count[hkey] = host_weak_count.get(hkey, 0) + 1
    elif hkey and vqv in {'probable', 'confirmed'}:
        host_weak_count[hkey] = 0
    if qual.get('verdict') == 'confirmed' and not can_be_confirmed_fn(qual):
        qual['verdict'] = 'probable'
        quality_telemetry['downgraded_confirm'] = int(quality_telemetry.get('downgraded_confirm', 0)) + 1
    if str(qual.get('verdict') or '') == 'probable':
        quality_telemetry['probable'] = int(quality_telemetry.get('probable', 0)) + 1
    if str(qual.get('verdict') or '') == 'confirmed':
        quality_telemetry['confirmed'] = int(quality_telemetry.get('confirmed', 0)) + 1
    signal_assessment = compute_signal_assessment(
        qual,
        summary_text,
        classification,
        qualification_mode,
        qualification_promising_threshold,
        shadow_workflow_bridge_enabled=bool(decision_toggles.get('qualification_shadow_workflow_bridge', True)),
    )
    log_event_fn(
        'AUTO_CAMPAIGN',
        'qualification_verdict',
        'in_progress',
        f"verdict={qual.get('verdict')};confidence={qual.get('confidence')};reason={qual.get('reason_code')}",
        actor='auto_campaign',
        row_type='service',
    )
    log_event_fn(
        'AUTO_CAMPAIGN',
        'control_comparison',
        'in_progress',
        f"performed={bool(control_cmp.get('performed'))};delta={bool(control_cmp.get('control_delta_observed'))};reason={control_cmp.get('reason')}",
        actor='auto_campaign',
        row_type='service',
    )
    log_event_fn(
        'AUTO_CAMPAIGN',
        decision_label,
        normalize_pipeline_status_fn(str(post['run_info'].get('engine_status') or ''), str(post['run_info'].get('auditor_decision') or ''), bool(error_flag)),
        summary_text,
        actor='auto_campaign',
        highlight=bool(signal_assessment.get('workflow_promotable', False)),
    )
    signal_contract = build_signal_contract(
        engine_status=str(post['run_info'].get('engine_status') or ''),
        auditor_decision=str(post['run_info'].get('auditor_decision') or ''),
        success_eval_status=str(post['run_info'].get('success_criteria_eval') or post['run_info'].get('success_eval_status') or ''),
        qual=qual,
        signal_assessment=signal_assessment,
        runtime_decision={},
        summary_text=summary_text,
        reason_code=reason_code,
        control_cmp=control_cmp,
        metrics_obj=metrics_obj,
        success_semantics=post['run_info'].get('success_semantics') if isinstance(post['run_info'].get('success_semantics'), dict) else {},
        weak_signal_positive_bridge_enabled=bool(decision_toggles.get('weak_signal_positive_bridge', True)),
    )
    runtime_decision = build_runtime_decision(
        qual=qual,
        auditor=str(post['run_info'].get('auditor_decision') or ''),
        engine_status=str(post['run_info'].get('engine_status') or ''),
        success_eval_status=str(post['run_info'].get('success_criteria_eval') or post['run_info'].get('success_eval_status') or ''),
        toggles=(decision_toggles if isinstance(decision_toggles, dict) else {}),
        mode=str(mode),
        signal_contract=signal_contract,
        task_family=str(post['run_info'].get('task_family') or ''),
    )
    runtime_decision_dict = runtime_decision.as_dict()
    intent_flags = runtime_decision.action_flags()
    signal_contract = build_signal_contract(
        engine_status=str(post['run_info'].get('engine_status') or ''),
        auditor_decision=str(post['run_info'].get('auditor_decision') or ''),
        success_eval_status=str(post['run_info'].get('success_criteria_eval') or post['run_info'].get('success_eval_status') or ''),
        qual=qual,
        signal_assessment=signal_assessment,
        runtime_decision=runtime_decision_dict,
        summary_text=summary_text,
        reason_code=reason_code,
        control_cmp=control_cmp,
        metrics_obj=metrics_obj,
        success_semantics=post['run_info'].get('success_semantics') if isinstance(post['run_info'].get('success_semantics'), dict) else {},
        weak_signal_positive_bridge_enabled=bool(decision_toggles.get('weak_signal_positive_bridge', True)),
    )
    promising = signal_contract_promising(signal_contract)
    run_info = dict(post['run_info'])
    run_info.update({
        'signal_contract': signal_contract,
        'promising': promising,
        'signal_positive': signal_contract_signal_positive(signal_contract),
        'workflow_promotable': signal_contract_workflow_promotable(signal_contract),
        'adaptation_positive': signal_contract_adaptation_positive(signal_contract),
        'host_promise_positive': signal_contract_host_promise_positive(signal_contract),
        'qualification': qual,
        'finding_lifecycle': finding_lifecycle_fn(str(mode), qual),
        'signal_assessment': signal_assessment,
        'runtime_decision': runtime_decision_dict,
        'decision_intent_flags': intent_flags,
        'decision_flags': intent_flags,
        'decision_eligibility': dict(runtime_decision_dict.get('eligibility') or {}),
        'decision_selected_action': str(runtime_decision_dict.get('selected_primary_action') or ''),
        'decision_selection_reason': str(runtime_decision_dict.get('selection_reason') or ''),
        'decision_explain': runtime_decision.explain,
        'decision_economics': runtime_decision.economics,
        'decision_effective_status': str(runtime_decision_dict.get('effective_status') or 'pending'),
        'decision_effective_flags': dict(runtime_decision_dict.get('effective_flags') or {}),
        'decision_effective_reasons': dict(runtime_decision_dict.get('effective_reasons') or {}),
        'decision_effective_blockers': dict(runtime_decision_dict.get('effective_blockers') or {}),
        'decision_effective_summary': str(runtime_decision_dict.get('effective_summary') or ''),
    })
    if str(mode) != 'confirm':
        run_info['next_aggression_hint'] = adaptive_aggression_fn(int(aggression) + 1, classification, reason_code, owner_override)
    return qual, promising, run_info
