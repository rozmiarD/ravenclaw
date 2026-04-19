from __future__ import annotations

import json
from typing import Any, Callable


def finalize_runner_outputs(
    *,
    runs: list[dict],
    campaign_validation: dict,
    run_started,
    max_runs: int,
    time_budget_min: int,
    retry_policy: str,
    out_path: str,
    reports_dir,
    archive_root,
    output_quality_telemetry: dict,
    finalize_outputs_fn: Callable[..., dict],
    flush_precheck_summary_fn: Callable[..., None],
    flush_dns_skip_summary_fn: Callable[..., None],
    flush_host_cooldown_summary_fn: Callable[..., None],
    flush_execution_gate_summary_fn: Callable[..., None],
    log_operation_fn: Callable[..., None],
    success: bool = True,
    error: Exception | None = None,
) -> dict | None:
    if success:
        summary = finalize_outputs_fn(
            runs=runs,
            campaign_validation=campaign_validation,
            run_started=run_started,
            max_runs=max_runs,
            time_budget_min=time_budget_min,
            retry_policy=retry_policy,
            out_path=out_path,
            reports_dir=reports_dir,
            archive_root=archive_root,
        )
        try:
            summary['quality_telemetry'] = output_quality_telemetry
            with open(out_path, 'w', encoding='utf-8') as handle:
                json.dump(summary, handle, ensure_ascii=False, indent=2)
        except Exception:
            pass
        flush_precheck_summary_fn(force=True)
        flush_dns_skip_summary_fn(force=True)
        flush_host_cooldown_summary_fn(force=True)
        flush_execution_gate_summary_fn(force=True)
        log_operation_fn('AUTO_CAMPAIGN', 'AUTO CAMPAIGN', 'end', actor='auto_campaign', note=f'executed={len(runs)}/{max_runs}', success=True)
        return summary

    flush_precheck_summary_fn(force=True)
    flush_dns_skip_summary_fn(force=True)
    flush_host_cooldown_summary_fn(force=True)
    flush_execution_gate_summary_fn(force=True)
    log_operation_fn('AUTO_CAMPAIGN', 'AUTO CAMPAIGN', 'end', actor='auto_campaign', note=f"error: {str(error)[:140] if error else 'unknown'}", success=False)
    return None
