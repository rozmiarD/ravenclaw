from __future__ import annotations

from typing import Any, Callable, Dict

from auto_campaign_targets import host_from_target  # type: ignore
from govengine_security_helpers import build_analysis_contract  # type: ignore
from auto_campaign_health_policy import apply_transport_cooldowns  # type: ignore


PostDict = Dict[str, Any]


def post_result_common(
    *,
    task_ctx: dict,
    result: dict,
    objective: str,
    target: str,
    mode: str,
    summary_text: str,
    classification: str,
    auditor: str,
    engine_status: str,
    run_index: int,
    plan_name: str | None,
    owner_override: bool,
    owner_auth: bool,
    aggression: int,
    inspect_json_signal_from_command: Callable[[object], dict],
    parse_rc_metrics: Callable[[str], dict],
    run_control_comparison: Callable[[object, int], dict],
    attack_family_fn: Callable[[str, str, str], str],
    host_family_owner_gate: dict,
    host_cooldown_until: dict[str, float],
    host_code000_streak: dict[str, int],
    host_code000_total: dict[str, int],
    host_403_streak: dict[str, int],
    host_fail_streak: dict[str, int],
    host_fail_count: dict[str, int],
    host_success_count: dict[str, int],
    code000_streak_threshold: int,
    code000_cooldown_sec: int,
    code000_session_cap: int,
    transport_observation_cooldown_sec: int = 600,
    http_403_streak_threshold: int = 4,
    http_403_cooldown_sec: int = 1800,
    code000_session_cooldown_sec: int = 86400,
) -> PostDict:
    reason_code = str((result.get('reason_code') if isinstance(result, dict) else '') or '')
    success_eval_status = str(((result.get('success_criteria') or {}).get('status') if isinstance(result, dict) and isinstance(result.get('success_criteria'), dict) else '') or '').lower()
    fam_gate = attack_family_fn(objective, target, str(task_ctx.get('task_family') or ''))
    hfg = (host_from_target(target), fam_gate)
    if auditor == 'owner_approval_required':
        host_family_owner_gate[hfg] = host_family_owner_gate.get(hfg, 0) + 1
    else:
        host_family_owner_gate[hfg] = 0
    planned_cmd = result.get('planned_command') if isinstance(result, dict) else None
    execution_lineage = result.get('execution_lineage') if isinstance(result.get('execution_lineage'), dict) else {}
    approved_execution_spec = result.get('approved_execution_spec') if isinstance(result.get('approved_execution_spec'), dict) else {}
    execution_truth = approved_execution_spec.get('execution_truth') if isinstance(approved_execution_spec.get('execution_truth'), dict) else {}
    command_input_summary = {}
    if isinstance(execution_lineage.get('approved_command_input_summary'), dict):
        command_input_summary = dict(execution_lineage.get('approved_command_input_summary') or {})
    elif isinstance(execution_truth.get('command_input_summary'), dict):
        command_input_summary = dict(execution_truth.get('command_input_summary') or {})
    json_sig = inspect_json_signal_from_command(planned_cmd)
    if json_sig.get('info'):
        summary_text = f"{summary_text} | Signals: {', '.join(i.get('code','info') for i in json_sig.get('info',[])[:2])}"
    if json_sig.get('findings'):
        top = json_sig.get('findings', [])[0]
        summary_text = f"{summary_text} | Potential finding: {top.get('code')}"
    if json_sig.get('signal') and classification in {'unknown', 'low'}:
        classification = str(json_sig.get('severity') or 'mid')
    sh = host_from_target(target)
    if sh:
        apply_transport_cooldowns(
            summary_text=summary_text,
            host=sh,
            host_cooldown_until=host_cooldown_until,
            host_code000_streak=host_code000_streak,
            host_code000_total=host_code000_total,
            host_403_streak=host_403_streak,
            code000_streak_threshold=code000_streak_threshold,
            code000_session_cap=code000_session_cap,
            code000_cooldown_sec=code000_cooldown_sec,
            transport_observation_cooldown_sec=transport_observation_cooldown_sec,
            http_403_streak_threshold=http_403_streak_threshold,
            http_403_cooldown_sec=http_403_cooldown_sec,
            code000_session_cooldown_sec=code000_session_cooldown_sec,
        )
        if engine_status in {'failed', 'error', 'timeout'}:
            host_fail_streak[sh] = host_fail_streak.get(sh, 0) + 1
            host_fail_count[sh] = host_fail_count.get(sh, 0) + 1
        else:
            host_fail_streak[sh] = 0
            host_success_count[sh] = host_success_count.get(sh, 0) + 1
    if reason_code and not summary_text.startswith('['):
        summary_text = f'[{reason_code}] {summary_text}'
    if planned_cmd:
        cmd_txt = ' '.join(str(x) for x in planned_cmd) if isinstance(planned_cmd, list) else str(planned_cmd)
        summary_text = f'{summary_text} | CMD: {cmd_txt}'
    if command_input_summary.get('target_delivery_mode') == 'stdin':
        stdin_preview = str(command_input_summary.get('stdin_preview') or '').replace('\n', '\\n')[:120]
        summary_text = f'{summary_text} | INPUT: stdin:{stdin_preview or "<present>"}'
    signal_codes = [str(f.get('code') or '') for f in (json_sig.get('findings') or []) if isinstance(f, dict)]
    metrics_obj = parse_rc_metrics(str(((result.get('engine') or {}).get('stdout') if isinstance(result, dict) else '') or '') + '\n' + str(((result.get('engine') or {}).get('stderr') if isinstance(result, dict) else '') or ''))
    control_cmp = run_control_comparison(planned_cmd, 20)
    analysis_contract = build_analysis_contract(
        result=result if isinstance(result, dict) else {},
        task_ctx=task_ctx if isinstance(task_ctx, dict) else {},
        success_eval_status=success_eval_status,
        engine_status=engine_status,
    )
    success_block = result.get('success_criteria') if isinstance(result.get('success_criteria'), dict) else {}
    task_success_semantics = task_ctx.get('success_semantics') if isinstance(task_ctx.get('success_semantics'), dict) else {}
    request_shape_hygiene = result.get('request_shape_hygiene') if isinstance(result.get('request_shape_hygiene'), dict) else {}
    merged_success_semantics = {
        'execution_success': bool(analysis_contract.get('execution_success', False)),
        'expected_signal_observed': str(analysis_contract.get('expected_signal_observed') or 'unknown'),
        'evidence_goal_met': str(analysis_contract.get('evidence_goal_met') or 'unknown'),
        'hypothesis_support': str(analysis_contract.get('hypothesis_support') or 'inconclusive'),
        'semantic_execution_fit': str(analysis_contract.get('semantic_execution_fit') or 'unknown'),
        'typed_family_eval': str(success_block.get('typed_family_eval') or analysis_contract.get('typed_family_eval') or 'generic'),
        'success_gap': str(success_block.get('gap') or analysis_contract.get('success_gap') or ''),
        'success_evidence': list(success_block.get('evidence') or analysis_contract.get('success_evidence') or [])[:6],
        'success_model': str(success_block.get('success_model') or analysis_contract.get('success_model') or task_success_semantics.get('success_model') or ''),
        'expected_signal_type': str(success_block.get('expected_signal_type') or analysis_contract.get('expected_signal_type') or task_success_semantics.get('expected_signal_type') or ''),
        'evidence_goal_type': str(success_block.get('evidence_goal_type') or analysis_contract.get('evidence_goal_type') or task_success_semantics.get('evidence_goal_type') or ''),
        'acceptance_checks_eval': list(success_block.get('acceptance_checks_eval') or []),
        'evidence_required_eval': list(success_block.get('evidence_required_eval') or []),
        'required_evidence_hits': list(success_block.get('required_evidence_hits') or []),
    }
    return {
        'reason_code': reason_code,
        'success_eval_status': success_eval_status,
        'summary_text': summary_text,
        'classification': classification,
        'planned_cmd': planned_cmd,
        'json_sig': json_sig,
        'signal_codes': signal_codes,
        'metrics_obj': metrics_obj,
        'control_cmp': control_cmp,
        'analysis_contract': analysis_contract,
        'run_info': {
            'index': run_index,
            'objective': objective,
            'target': target,
            'mode': mode,
            'aggression': aggression,
            'plan_name': plan_name,
            'success_criteria': str(task_ctx.get('task_success_criteria') or ''),
            'campaign_success_criteria': str(task_ctx.get('campaign_success_criteria') or ''),
            'task_family': str(task_ctx.get('task_family') or 'generic'),
            'success_criteria_eval': success_eval_status,
            'owner_override': owner_override,
            'owner_approved_auth': owner_auth,
            'auditor_decision': auditor,
            'engine_status': engine_status,
            'classification': classification,
            'engine_stdout_preview': summary_text,
            'reason_code': reason_code,
            'command_preview': (' '.join(str(x) for x in planned_cmd) if isinstance(planned_cmd, list) else (str(planned_cmd) if planned_cmd else '')),
            'command_input_summary': dict(command_input_summary),
            'metrics': metrics_obj,
            'signals': json_sig,
            'control_comparison': control_cmp,
            'analysis_contract': analysis_contract,
            'success_semantics': merged_success_semantics,
            'request_shape_hygiene': dict(request_shape_hygiene),
        },
    }
