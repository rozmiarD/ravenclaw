from __future__ import annotations

from typing import Any, Dict

from runtime_decision_engine import build_runtime_decision  # type: ignore
from runtime_decision_contracts import canonical_action_flags_from_mapping  # type: ignore


def build_post_run_decision_record(
    task: Dict[str, Any],
    result: Dict[str, Any],
    qual: Dict[str, Any],
    classification: str,
    auditor: str,
    engine_status: str,
    success_eval_status: str,
    toggles: Dict[str, Any],
    mode: str = '',
) -> Dict[str, Any]:
    del classification
    signal_contract = {}
    if isinstance(result.get('signal_contract'), dict):
        signal_contract = result.get('signal_contract') or {}
    elif isinstance(task.get('signal_contract'), dict):
        signal_contract = task.get('signal_contract') or {}
    runtime_task = task.get('runtime_task') if isinstance(task.get('runtime_task'), dict) else {}
    record = build_runtime_decision(
        qual=qual,
        auditor=auditor,
        engine_status=engine_status,
        success_eval_status=success_eval_status,
        toggles=toggles,
        mode=mode,
        signal_contract=signal_contract,
        task_family=str(task.get('task_family') or runtime_task.get('task_family') or ''),
        runtime_task=runtime_task,
    )
    return record.as_dict()


def post_run_decision(
    task: Dict[str, Any],
    result: Dict[str, Any],
    qual: Dict[str, Any],
    classification: str,
    auditor: str,
    engine_status: str,
    success_eval_status: str,
    toggles: Dict[str, Any],
    mode: str = '',
) -> Dict[str, bool]:
    record = build_post_run_decision_record(
        task,
        result,
        qual,
        classification,
        auditor,
        engine_status,
        success_eval_status,
        toggles,
        mode=mode,
    )
    flags, _source = canonical_action_flags_from_mapping(record)
    return {
        'retry': bool((flags or {}).get('retry', False)),
        'confirm': bool((flags or {}).get('confirm', False)),
        'followup': bool((flags or {}).get('followup', False)),
        'precision': bool((flags or {}).get('precision', False)),
    }
