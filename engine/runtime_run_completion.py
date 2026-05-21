from __future__ import annotations

from typing import Any, Callable, Dict

from runtime_runner_deps import RuntimeRunnerDeps  # type: ignore
from govengine_security_helpers import signal_contract_planner_reconsult_worthy  # type: ignore


def complete_runtime_run(
    *,
    run_info: Dict[str, Any],
    task_ctx: Dict[str, Any],
    result: Dict[str, Any],
    qual: Dict[str, Any],
    classification: str,
    auditor: str,
    engine_status: str,
    success_eval_status: str,
    summary_text: str,
    reason_code: str,
    target: str,
    objective: str,
    aggression: int,
    owner_auth: bool,
    owner_override: bool,
    mode: str,
    confirm_total: int,
    promising: bool,
    runtime_decision: Dict[str, Any] | None,
    deps: RuntimeRunnerDeps,
    record_and_persist_run_fn: Callable[[Dict[str, Any]], None],
    toggles: dict,
    runs: list[dict],
    promising_hits_ref: list[int],
    host_state: dict,
) -> tuple[int, Dict[str, Any], str | None]:
    run_info['execution_gate'] = dict(task_ctx.get('execution_gate') or {}) if isinstance(task_ctx.get('execution_gate'), dict) else {}
    confirm_total, effective_decision = deps.apply_post_run_actions_fn(
        task_ctx=task_ctx,
        result=(result if isinstance(result, dict) else {}),
        qual=qual,
        classification=classification,
        auditor=auditor,
        engine_status=engine_status,
        success_eval_status=success_eval_status,
        summary_text=summary_text,
        reason_code=reason_code,
        target=target,
        objective=objective,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        mode=str(mode),
        confirm_total=confirm_total,
        promising=bool(promising),
        signal_contract=(run_info.get('signal_contract') if isinstance(run_info.get('signal_contract'), dict) else {}),
        runtime_decision=(runtime_decision if isinstance(runtime_decision, dict) else {}),
    )
    confirm_total = int(confirm_total) if isinstance(confirm_total, int) else confirm_total
    run_info = deps.project_runtime_decision_to_run_info_fn(
        run_info=run_info,
        effective_decision=(effective_decision if isinstance(effective_decision, dict) else {}),
    )
    record_and_persist_run_fn(run_info)
    deps.apply_runtime_adaptation_fn(run_info)
    reconsult_worthy = signal_contract_planner_reconsult_worthy(run_info.get('signal_contract')) if isinstance(run_info.get('signal_contract'), dict) else bool(promising)
    if reconsult_worthy:
        promising_hits_ref[0] += 1
    tier = deps.maybe_reconsult_planner_fn(toggles, runs, promising_hits_ref[0], host_state)
    if tier:
        deps.refresh_planner_hints_and_reprioritize_fn('high_signal_threshold', tier)
    return confirm_total, run_info, tier
