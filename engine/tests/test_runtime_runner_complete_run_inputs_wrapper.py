from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import runtime_runner_complete_run_inputs_wrapper as rrcriw  # type: ignore


def test_build_complete_runtime_run_inputs_delegates() -> None:
    captured = {}

    def fake_build_complete_runtime_run_inputs(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return object()

    out = rrcriw.build_complete_runtime_run_inputs(
        build_complete_runtime_run_inputs_fn=fake_build_complete_runtime_run_inputs,
        task_ctx={},
        result={},
        qual={},
        classification='info',
        auditor='approve',
        engine_status='success',
        success_eval_status='ok',
        summary_text='ok',
        reason_code='ok',
        target='https://example.com',
        objective='Probe',
        aggression=4,
        owner_auth=True,
        owner_override=False,
        mode='fast',
        confirm_total=0,
        promising=False,
        run_info={},
        runner_deps=object(),
        record_and_persist_run_fn=lambda run_info: None,
        toggles={},
        state=object(),
    )
    assert out is not None
    assert captured['objective'] == 'Probe'
