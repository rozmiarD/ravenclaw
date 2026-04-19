from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_run_completion import complete_runtime_run  # type: ignore
from runtime_runner_deps import RuntimeRunnerDeps  # type: ignore


def test_complete_runtime_run_records_and_triggers_reconsult_when_promising() -> None:
    events = []
    recorded = []
    promising_hits_ref = [0]

    run_info = {'runtime_decision': {'intent_flags': {'confirm': True}}, 'decision_explain': {}}
    task_ctx = {'execution_gate': {'reason_code': 'allowed'}}

    deps = RuntimeRunnerDeps(
        apply_post_run_actions_fn=lambda **kwargs: (1, {'effective_status': 'applied', 'effective_flags': {'confirm': True}, 'effective_reasons': {'confirm': 'confirm_job_queued'}, 'effective_blockers': {}, 'effective_summary': 'selected=confirm'}),
        project_runtime_decision_to_run_info_fn=lambda run_info, effective_decision: dict(run_info, decision_effective_status=effective_decision['effective_status'], runtime_decision={'intent_flags': {'confirm': True}, 'effective_status': effective_decision['effective_status']}),
        maybe_reconsult_planner_fn=lambda toggles, runs, hits, host_state: 'deep' if hits >= 1 else None,
        refresh_planner_hints_and_reprioritize_fn=lambda reason, tier: events.append((reason, tier)),
        precheck_and_prepare_task_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: run_info.setdefault('adaptation_applied', True),
    )

    confirm_total, out, tier = complete_runtime_run(
        run_info=run_info,
        task_ctx=task_ctx,
        result={},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='partial',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        mode='fast',
        confirm_total=0,
        promising=True,
        runtime_decision={'intent_flags': {'confirm': True}},
        deps=deps,
        record_and_persist_run_fn=lambda payload: recorded.append(payload),
        toggles={},
        runs=[],
        promising_hits_ref=promising_hits_ref,
        host_state={},
    )

    assert confirm_total == 1
    assert out['decision_effective_status'] == 'applied'
    assert tier == 'deep'
    assert promising_hits_ref[0] == 1
    assert recorded
    assert events == [('high_signal_threshold', 'deep')]


def test_complete_runtime_run_uses_signal_contract_for_reconsult_hits() -> None:
    events = []
    promising_hits_ref = [0]

    deps = RuntimeRunnerDeps(
        apply_post_run_actions_fn=lambda **kwargs: (0, {'effective_status': 'applied', 'effective_flags': {}, 'effective_reasons': {}, 'effective_blockers': {}, 'effective_summary': 'selected=none'}),
        project_runtime_decision_to_run_info_fn=lambda run_info, effective_decision: dict(run_info, decision_effective_status=effective_decision['effective_status']),
        maybe_reconsult_planner_fn=lambda toggles, runs, hits, host_state: 'light' if hits >= 1 else None,
        refresh_planner_hints_and_reprioritize_fn=lambda reason, tier: events.append((reason, tier)),
        precheck_and_prepare_task_fn=lambda **kwargs: {},
        prepare_curated_task_fn=lambda *args, **kwargs: None,
        prepare_runtime_task_fn=lambda *args, **kwargs: None,
        reprioritize_queues_fn=lambda: None,
        persist_recorded_run_fn=lambda **kwargs: 0.0,
        apply_runtime_adaptation_fn=lambda run_info: None,
    )

    confirm_total, out, tier = complete_runtime_run(
        run_info={
            'signal_contract': {
                'adaptation_feedback': {'planner_reconsult_worthy': True},
            },
            'runtime_decision': {'intent_flags': {}},
        },
        task_ctx={'execution_gate': {}},
        result={},
        qual={'verdict': 'probable'},
        classification='medium',
        auditor='approve',
        engine_status='ok',
        success_eval_status='partial',
        summary_text='partial',
        reason_code='interesting',
        target='https://api.example.com/',
        objective='Probe',
        aggression=5,
        owner_auth=False,
        owner_override=False,
        mode='fast',
        confirm_total=0,
        promising=False,
        runtime_decision={'intent_flags': {}},
        deps=deps,
        record_and_persist_run_fn=lambda payload: None,
        toggles={},
        runs=[],
        promising_hits_ref=promising_hits_ref,
        host_state={},
    )

    assert confirm_total == 0
    assert out['decision_effective_status'] == 'applied'
    assert tier == 'light'
    assert promising_hits_ref[0] == 1
    assert events == [('high_signal_threshold', 'light')]
