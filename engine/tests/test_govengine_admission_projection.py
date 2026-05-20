from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from govengine.admission import (  # type: ignore
    validate_admission_decision,
    validate_approval_request,
    validate_audit_record,
    validate_policy_decision,
)
from govengine_admission_projection import (  # type: ignore
    build_gov_admission_bundle_projection,
    build_gov_admission_decision_projection,
    build_gov_approval_request_projection,
    build_gov_policy_decision_projection,
)
from runtime_admission_policy import PlannerRuntimeAdmissionDecision  # type: ignore
from runtime_execution_gate import HostExecutionGate  # type: ignore


def test_planner_admission_decision_projects_to_govengine_contract_without_raw_target() -> None:
    decision = PlannerRuntimeAdmissionDecision(
        allowed=False,
        reason_code='planner_activation_phase_skip',
        detail='phase=3;requires=confirmed_signal',
        blockers=['planner_phase_gate'],
        context={
            'activation_phase': 3,
            'activation_mode': 'if_confirmed',
            'target_cluster': 'api.example.com',
            'expected_depth': 'deep',
        },
        signal={'has_confirmed_signal': False},
        explainability={'synthesis_gate_relevant': True},
    )
    projection = build_gov_admission_decision_projection(decision, subject='https://api.example.com/account/123')
    checked = validate_admission_decision(projection)

    assert checked.allowed is False
    assert checked.outcome == 'denied'
    assert checked.subject_ref.startswith('sha256:')
    assert checked.context['target_cluster_ref'].startswith('sha256:')
    assert checked.context['target_cluster_redacted'] is True
    assert checked.metadata['subject_redacted'] is True
    assert 'api.example.com' not in str(projection)
    assert 'https://api.example.com/account/123' not in str(projection)


def test_host_execution_gate_projection_redacts_host_detail_and_validates_policy() -> None:
    gate = HostExecutionGate(
        allowed=False,
        host='app.example.com',
        family='workflow',
        reason_code='host_cooldown',
        detail='host=app.example.com;mode=deep',
        cooldown_until=1770000000.0,
        blockers=['cooldown_active'],
        activation_mode='if_signal',
        expected_depth='deep',
    )
    admission = build_gov_admission_decision_projection(gate)
    policy = build_gov_policy_decision_projection(gate)

    checked_admission = validate_admission_decision(admission)
    checked_policy = validate_policy_decision(policy)

    assert checked_admission.reason_code == 'host_cooldown'
    assert checked_admission.signal['cooldown_until_present'] is True
    assert checked_policy.decision == 'deny'
    assert 'app.example.com' not in str(admission)
    assert 'app.example.com' not in str(policy)


def test_admission_bundle_and_approval_request_are_valid_neutral_records() -> None:
    gate = HostExecutionGate(
        allowed=True,
        host='ok.example.com',
        family='recon',
        reason_code='allowed',
        detail='host=ok.example.com;family=recon',
    )
    bundle = build_gov_admission_bundle_projection(gate)
    approval = build_gov_approval_request_projection(
        subject='https://ok.example.com/',
        request_id='approval-1',
        policy_refs=[bundle['policy_decision']['policy_id']],
    )

    assert bundle['artifact_type'] == 'ravenclaw_govengine_admission_projection'
    assert validate_admission_decision(bundle['admission_decision']).allowed is True
    assert validate_policy_decision(bundle['policy_decision']).decision == 'allow'
    assert validate_audit_record(bundle['audit_record']).decision_ref == bundle['admission_decision']['decision_id']
    assert validate_approval_request(approval).policy_refs == (bundle['policy_decision']['policy_id'],)
    assert 'ok.example.com' not in str(bundle)
    assert 'https://ok.example.com/' not in str(approval)
