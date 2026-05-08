from __future__ import annotations

from dataclasses import dataclass, field

from govengine.execution.runner_protocol import GovRunnerReceipt, GovRunnerRequest, GovRunnerStepResult, runner_request_from_approved_spec
from govengine.ooda import GovObservation, GovOodaController, GovOrientation


def _approved_spec_with_two_steps() -> dict:
    return {
        'spec_version': '2026-03-18.approved.v1',
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'resolved_tool': 'curl',
        'execution_mode': 'normalized',
        'compiler': {'semantic_loss_policy': {'loss_class': 'none', 'policy_response': 'proceed'}},
        'approval': {'decision': 'approve', 'reason': 'ok'},
        'execution_truth': {
            'artifact_type': 'approved_execution_spec',
            'execution_plan': [
                {'tool': 'curl', 'args': ['https://example.com/one']},
                {'tool': 'curl', 'args': ['https://example.com/two']},
            ],
        },
    }


@dataclass
class RavenclawOodaRunnerAdapter:
    """Minimal Ravenclaw host-runner seam for GovEngine OODA decisions.

    The test adapter intentionally does not execute subprocesses. It proves the
    host-side contract: evaluate OODA before each next step, stop scheduling
    when an interrupting decision appears, and preserve the decision in the
    receipt Ravenclaw would hand to evidence/reporting code.
    """

    controller: GovOodaController = field(default_factory=GovOodaController)
    orientations: list[GovOrientation] = field(default_factory=list)

    def run(self, request: GovRunnerRequest) -> GovRunnerReceipt:
        results: list[GovRunnerStepResult] = []
        decisions: list[dict] = []
        for step in request.steps:
            orientation = self.orientations.pop(0) if self.orientations else GovOrientation()
            decision = self.controller.decide(
                observations=[GovObservation(kind='before_step', subject=step.tool, facts={'step_index': step.index})],
                orientation=orientation,
            )
            decisions.append(decision.as_dict())
            if decision.interrupting:
                return GovRunnerReceipt(
                    status='interrupted',
                    request_id=request.request_id,
                    source=request.source,
                    step_results=tuple(results),
                    reason_code=decision.reason_code,
                    control_decisions=tuple(decisions),
                )
            results.append(GovRunnerStepResult(index=step.index, status='dry-run', reason_code='adapter_dry_run'))
        return GovRunnerReceipt(
            status='dry-run',
            request_id=request.request_id,
            source=request.source,
            step_results=tuple(results),
            reason_code='ok',
            control_decisions=tuple(decisions),
        )


def test_ravenclaw_runner_adapter_honors_ooda_pause_between_steps() -> None:
    request = runner_request_from_approved_spec(_approved_spec_with_two_steps(), request_id='pause-demo')
    runner = RavenclawOodaRunnerAdapter(orientations=[GovOrientation(), GovOrientation(operator_control='pause')])

    receipt = runner.run(request)

    assert receipt.status == 'interrupted'
    assert receipt.reason_code == 'operator_pause_requested'
    assert [result.index for result in receipt.step_results] == [0]
    assert receipt.control_decisions[-1]['decision'] == 'pause'


def test_ravenclaw_runner_adapter_honors_ooda_abort_before_first_step() -> None:
    request = runner_request_from_approved_spec(_approved_spec_with_two_steps(), request_id='abort-demo')
    runner = RavenclawOodaRunnerAdapter(orientations=[GovOrientation(scope_ok=False)])

    receipt = runner.run(request)

    assert receipt.status == 'interrupted'
    assert receipt.reason_code == 'scope_drift_detected'
    assert receipt.step_results == ()
    assert receipt.control_decisions[0]['decision'] == 'abort'


def test_ravenclaw_runner_adapter_honors_ooda_cooldown_between_steps() -> None:
    request = runner_request_from_approved_spec(_approved_spec_with_two_steps(), request_id='cooldown-demo')
    runner = RavenclawOodaRunnerAdapter(orientations=[GovOrientation(), GovOrientation(host_health='transport_noise')])

    receipt = runner.run(request)

    assert receipt.status == 'interrupted'
    assert receipt.reason_code == 'host_health_transport_noise'
    assert [result.index for result in receipt.step_results] == [0]
    assert receipt.control_decisions[-1]['decision'] == 'cooldown'
