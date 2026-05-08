from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from executor import ExecutionEngine  # type: ignore
from govengine.execution.runner import approved_spec_compiled_action, approved_spec_dry_run_result, legacy_action_spec_dry_run_result


def _approved_spec() -> dict:
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
            'execution_plan': [{'tool': 'curl', 'args': ['https://example.com']}],
        },
    }


def test_approved_spec_compiled_action_shape() -> None:
    approved = _approved_spec()

    assert approved_spec_compiled_action(approved) == {
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'compiler_tool_choice': 'curl',
        'compiler_tool_choice_source': 'approved_execution_spec',
        'execution_mode': 'normalized',
        'semantic_loss_policy': {'loss_class': 'none', 'policy_response': 'proceed'},
    }


def test_approved_spec_dry_run_result_matches_executor() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    approved = _approved_spec()
    plan = engine.build_execution_plan_from_approved_spec(approved)

    assert engine.execute_approved_spec(approved, dry_run=True) == approved_spec_dry_run_result(
        approved_execution_spec=approved,
        planned_commands=plan,
        execution_ticket_gate={'status': 'not_required'},
    )


def test_legacy_action_spec_dry_run_result_matches_executor() -> None:
    engine = ExecutionEngine()
    engine.scope_domains = {'exact': ['example.com'], 'suffix': [], 'exclude_exact': [], 'exclude_suffix': []}
    action = {
        'action_type': 'single_probe',
        'capability': 'http_probe',
        'tool': 'curl',
        'args': ['https://example.com'],
        'tool_chain': [],
        'probe_recipe': {'sequence_steps': ['single'], 'evidence_goal': 'dry run'},
    }
    result = engine.execute(action, dry_run=True)

    assert result == legacy_action_spec_dry_run_result(
        compiled_action=result['compiled_action'],
        planned_commands=result['planned_commands'],
    )
