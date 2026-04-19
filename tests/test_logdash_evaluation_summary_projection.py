from logdash.services import build_evaluation_summary_payload


def test_build_evaluation_summary_payload_exposes_semantic_class_metrics() -> None:
    payload = build_evaluation_summary_payload(
        payload={'run_id': 'run-1'},
        archive_summary={},
        metrics={
            'totals': {'excluded_by_reason': {'policy_blocked': 2}},
            'yield_metrics': {},
            'governance_metrics': {'blocked_evidence_rate': {'count': 2, 'denominator': 4, 'rate': 0.5}},
            'auth_state_metrics': {},
            'semantic_class_metrics': {'weak_evidence_rate': {'count': 1, 'denominator': 4, 'rate': 0.25}},
            'queue_metrics': {},
        },
        replay={
            'dataset_id': 'd1',
            'bundle_count': 4,
            'status_counts': {'ok': 4},
            'variant': {'variant_id': 'baseline'},
            'results': [],
        },
    )
    assert payload['ok'] is True
    assert payload['semantic_class_metrics']['weak_evidence_rate']['count'] == 1
    assert payload['governance_metrics']['blocked_evidence_rate']['count'] == 2
    assert payload['top_exclusions'][0]['reason'] == 'policy_blocked'
