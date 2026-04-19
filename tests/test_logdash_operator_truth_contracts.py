from pathlib import Path


def test_operator_truth_contract_doc_mentions_hardened_control_and_recovery_semantics() -> None:
    text = Path('references/logdash-operator-truth-contracts.md').read_text(encoding='utf-8')

    required_phrases = [
        '/api/campaign/control',
        'start',
        'resume',
        'pause',
        'stop',
        'activate-from-blueprint',
        'stale PID files must be cleared',
        'paused persisted state must remain visible',
        'explicit stopped state takes precedence',
        'runtime_snapshot_source',
        'empty_selected_campaign_queue',
        'normalized_host_state_file',
        'normalized_runtime_plan_meta',
    ]

    for phrase in required_phrases:
        assert phrase in text



def test_logdash_readmes_link_operator_truth_contract_reference() -> None:
    root = Path('README.md').read_text(encoding='utf-8')
    logdash = Path('logdash/README.md').read_text(encoding='utf-8')

    assert 'references/logdash-operator-truth-contracts.md' in root
    assert '../references/logdash-operator-truth-contracts.md' in logdash
