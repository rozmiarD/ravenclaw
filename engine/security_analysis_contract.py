from __future__ import annotations

from typing import Any, Dict


def build_analysis_contract(*, result: dict, task_ctx: dict, success_eval_status: str, engine_status: str) -> dict:
    brain = result.get('brain') if isinstance(result.get('brain'), dict) else {}
    compiler = result.get('engine_compiler') if isinstance(result.get('engine_compiler'), dict) else {}
    success_block = result.get('success_criteria') if isinstance(result.get('success_criteria'), dict) else {}
    task_success_semantics = task_ctx.get('success_semantics') if isinstance(task_ctx.get('success_semantics'), dict) else {}
    success_contract = success_block.get('success_semantics') if isinstance(success_block.get('success_semantics'), dict) else task_success_semantics
    action_type = str(brain.get('action_type') or (compiler.get('action_type') or 'single_probe'))
    expected_signal = str(brain.get('expected_signal') or success_contract.get('expected_signal_type') or '').strip()
    evidence_goal = str(brain.get('evidence_goal') or success_contract.get('evidence_goal_type') or '').strip()
    status = str(success_eval_status or '').strip().lower()
    execution_success = str(engine_status or '').strip().lower() not in {'failed', 'error', 'timeout'}
    if status == 'met':
        expected_signal_observed = 'yes'
        evidence_goal_met = 'yes'
        hypothesis_support = 'strengthened'
    elif status == 'partial':
        expected_signal_observed = 'partial'
        evidence_goal_met = 'partial'
        hypothesis_support = 'inconclusive'
    elif status == 'not_met':
        expected_signal_observed = 'no'
        evidence_goal_met = 'no'
        hypothesis_support = 'weakened'
    else:
        expected_signal_observed = 'unknown'
        evidence_goal_met = 'unknown'
        hypothesis_support = 'inconclusive'
    semantic_policy = compiler.get('semantic_loss_policy') if isinstance(compiler.get('semantic_loss_policy'), dict) else {}
    semantic_execution_fit = 'degraded' if bool(compiler.get('semantic_loss_detected', False)) else 'exact'
    return {
        'action_type': action_type,
        'hypothesis': str(brain.get('hypothesis') or ''),
        'why_now': str(brain.get('why_now') or ''),
        'expected_signal': expected_signal,
        'evidence_goal': evidence_goal,
        'planner_alignment': str(brain.get('planner_alignment') or 'unknown'),
        'planner_override_reason': str(brain.get('planner_override_reason') or ''),
        'redundancy_risk': str(brain.get('redundancy_risk') or 'unknown'),
        'execution_success': execution_success,
        'expected_signal_observed': expected_signal_observed,
        'evidence_goal_met': evidence_goal_met,
        'hypothesis_support': hypothesis_support,
        'semantic_execution_fit': semantic_execution_fit,
        'semantic_loss_class': str(semantic_policy.get('loss_class') or 'none'),
        'semantic_loss_policy_response': str(semantic_policy.get('policy_response') or 'proceed'),
        'approved_under_degradation': bool(semantic_policy.get('approved_under_degradation', False)),
        'compiler_strategy': str(compiler.get('compiler_strategy') or ''),
        'compiler_variant_count': int(compiler.get('compiler_variant_count', 1) or 1),
        'task_family': str(task_ctx.get('task_family') or 'generic'),
        'typed_family_eval': str(success_block.get('typed_family_eval') or 'generic'),
        'success_gap': str(success_block.get('gap') or ''),
        'success_evidence': list(success_block.get('evidence') or [])[:6],
        'success_model': str(success_block.get('success_model') or success_contract.get('success_model') or ''),
        'expected_signal_type': str(success_block.get('expected_signal_type') or success_contract.get('expected_signal_type') or ''),
        'evidence_goal_type': str(success_block.get('evidence_goal_type') or success_contract.get('evidence_goal_type') or ''),
        'acceptance_checks_eval': list(success_block.get('acceptance_checks_eval') or []),
        'evidence_required_eval': list(success_block.get('evidence_required_eval') or []),
        'required_evidence_hits': list(success_block.get('required_evidence_hits') or []),
    }
