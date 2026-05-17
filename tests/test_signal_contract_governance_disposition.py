from govengine.contracts.signal import build_signal_contract


def test_signal_contract_carries_governance_blocked_qualification_disposition() -> None:
    contract = build_signal_contract(
        engine_status='blocked',
        auditor_decision='owner_approval_required',
        success_eval_status='not_met',
        qual={
            'verdict': 'weak_signal',
            'confidence': 0.29,
            'disposition': 'governance_blocked',
        },
        signal_assessment={
            'qualification_threshold': 'probable',
            'workflow_promotable': False,
            'signal_positive': True,
        },
        runtime_decision={},
        summary_text='Blocked by policy before confirmatory execution',
        reason_code='auditor_owner_approval_required',
        control_cmp={},
        metrics_obj={'code': 403},
        success_semantics={},
    )
    assert contract['workflow_promotion']['qualification_disposition'] == 'governance_blocked'
    assert contract['finding_signal']['evidence_class'] == 'blocked_evidence'
    assert 'qualification_disposition:governance_blocked' in contract['finding_signal']['evidence']
