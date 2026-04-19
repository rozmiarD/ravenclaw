from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_reporting import finalize_outputs, render_host_summary, write_run_details  # type: ignore


def _run() -> dict:
    return {
        'index': 1,
        'objective': 'Probe authz boundary',
        'target': 'https://api.example.com/v1/users',
        'mode': 'fast',
        'aggression': 5,
        'plan_name': 'AUTHZ-BOUNDARY',
        'owner_override': False,
        'owner_approved_auth': False,
        'auditor_decision': 'approve',
        'engine_status': 'ok',
        'classification': 'mid',
        'promising': True,
        'signal_assessment': {'workflow_promotable': True},
        'signal_contract': {
            'workflow_promotion': {'status': 'confirmable'},
            'finding_signal': {'status': 'strong'},
            'success_outcome': {'status': 'partial'},
            'adaptation_feedback': {'status': 'positive'},
        },
        'decision_intent_flags': {'confirm': True},
        'decision_flags': {'confirm': True},
        'decision_effective_status': 'applied',
        'decision_effective_summary': 'selected=confirm',
        'decision_explain': {'why': ['confirm_selected_for_confirmable_workflow'], 'blockers': []},
        'decision_economics': {'priority_score': 0.9},
        'brain_reasoning_summary': {'action_type': 'differential_probe'},
        'analysis_contract': {
            'hypothesis_support': 'strengthened',
            'expected_signal_observed': 'partial',
            'evidence_goal_met': 'partial',
            'semantic_execution_fit': 'exact',
            'semantic_loss_class': 'bounded_lowering',
            'semantic_loss_policy_response': 'proceed_mark_degraded',
            'approved_under_degradation': True,
        },
        'success_semantics': {'typed_family_eval': 'authz_boundary', 'success_gap': 'need_clear_allow_deny_or_boundary_evidence', 'success_evidence': ['engine_ok']},
        'engine_compiler': {'semantic_loss_policy': {'loss_class': 'bounded_lowering', 'policy_response': 'proceed_mark_degraded', 'approved_under_degradation': True}},
        'semantic_loss_rereview_required': False,
        'semantic_loss_rereview_completed': False,
        'semantic_loss_rereview_decision': '',
        'execution_gate': {'status': 'passed'},
        'host_state_band': 'promising',
        'host_transition': {'to_band': 'promising'},
        'host_regeneration_reason': 'promising_host_shift',
        'engine_stdout_preview': '403 forbidden on control; bypass candidate on variant',
        'runtime_decision': {'explain': {'why': ['confirm_selected_for_confirmable_workflow'], 'blockers': []}},
    }


def test_render_host_summary_exposes_signal_contract_statuses() -> None:
    text = render_host_summary([_run()], lineage_audit={'status': 'passed', 'gate_ready': True, 'stats': {'total_items': 1, 'unique_lineages': 1, 'duplicate_lineages': 0, 'missing_lineages': 0}})
    assert 'Lineage audit: status=passed gate_ready=True items=1 unique=1 duplicates=0 missing=0' in text
    assert 'Workflow promotion: confirmable' in text
    assert 'Success outcome: partial' in text
    assert 'Adaptation: positive' in text
    assert 'Semantic loss: bounded_lowering | Response: proceed_mark_degraded' in text


def test_finalize_outputs_includes_signal_contract_statuses_in_vectors() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        summary = finalize_outputs(
            runs=[_run()],
            campaign_validation={'ok': True},
            run_started=datetime.now(timezone.utc),
            max_runs=10,
            time_budget_min=15,
            retry_policy='balanced',
            out_path=str(root / 'summary.json'),
            reports_dir=root / 'reports',
            archive_root=root / 'archive',
        )
        vec = summary['vectors'][0]
        assert vec['signal_contract']['workflow_promotion']['status'] == 'confirmable'
        assert vec['workflow_promotion_status'] == 'confirmable'
        assert vec['success_outcome_status'] == 'partial'
        assert vec['adaptation_feedback_status'] == 'positive'
        assert vec['semantic_loss_class'] == 'bounded_lowering'
        assert vec['approved_under_degradation'] is True
        assert vec['semantic_lineage']['artifact_boundaries']['lineage_sha256']
        assert vec['semantic_lineage_summary']['lineage_sha256'] == vec['semantic_lineage']['artifact_boundaries']['lineage_sha256']
        saved = json.loads((root / 'summary.json').read_text(encoding='utf-8'))
        assert saved['vectors'][0]['finding_signal_status'] == 'strong'
        assert saved['lineage_audit']['status'] == 'passed'
        assert saved['lineage_audit']['gate_ready'] is True
        assert saved['lineage_audit']['stats']['total_items'] == 1
        assert saved['evaluation']['bundle_count'] == 1
        assert saved['evaluation']['status_counts']['ok'] == 1
        assert saved['evaluation']['metrics']['governance_metrics']['lineage_completeness_rate']['count'] == 1
        assert saved['branch_campaignlets']['count'] == 1
        assert saved['branch_campaignlets']['items'][0]['persistence_score'] >= 0.6
        assert saved['exploit_motif_memory']['count'] >= 1
        archived = json.loads((root / 'archive' / saved['run_id'] / 'semantic-lineage-index.json').read_text(encoding='utf-8'))
        assert archived['items'][0]['lineage_sha256'] == saved['vectors'][0]['semantic_lineage_summary']['lineage_sha256']
        assert archived['stats']['total_items'] == len(archived['items'])
        assert archived['stats']['missing_lineages'] == 0
        replay_output = json.loads((root / 'archive' / saved['run_id'] / 'evaluation-replay.json').read_text(encoding='utf-8'))
        metrics_output = json.loads((root / 'archive' / saved['run_id'] / 'evaluation-metrics.json').read_text(encoding='utf-8'))
        campaignlets_output = json.loads((root / 'archive' / saved['run_id'] / 'branch-campaignlets.json').read_text(encoding='utf-8'))
        motif_output = json.loads((root / 'archive' / saved['run_id'] / 'exploit-motif-memory.json').read_text(encoding='utf-8'))
        current_campaignlets = json.loads((root / 'state' / 'branch-campaignlets.json').read_text(encoding='utf-8'))
        current_motifs = json.loads((root / 'state' / 'exploit-motif-memory.json').read_text(encoding='utf-8'))
        assert replay_output['bundle_count'] == 1
        assert metrics_output['schema_version'] == 'phase5-metrics-v2'
        assert metrics_output['intelligence_quality_metrics']['branch_quality_rate']['count'] >= 0
        assert campaignlets_output['count'] == 1
        assert motif_output['count'] >= 1
        assert current_campaignlets['count'] == 1
        assert current_motifs['count'] >= 1


def test_write_run_details_writes_signal_contract_lines() -> None:
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td)
        write_run_details([_run()], dest)
        files = list(dest.glob('*.md'))
        assert len(files) == 1
        text = files[0].read_text(encoding='utf-8')
        assert '- Workflow promotion: confirmable' in text
        assert '- Success outcome: partial' in text
        assert '- Adaptation feedback: positive' in text
        assert '- Semantic loss class: bounded_lowering' in text
        assert '- Approved under degradation: True' in text
        assert '- Signal contract: {' in text
