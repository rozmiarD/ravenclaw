from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from runtime_admission_reporting import (  # type: ignore
    admission_skip_bucket,
    execution_gate_log_parts,
    execution_gate_summary_payload,
    record_execution_gate_skip,
    synthesis_skip_summary,
)


def test_admission_skip_bucket_classifies_non_gate_reasons_explicitly() -> None:
    assert admission_skip_bucket('dns_unresolved') == 'dns'
    assert admission_skip_bucket('host_cooldown') == 'cooldown'
    assert admission_skip_bucket('allowed') == 'allowed'
    assert admission_skip_bucket('planner_activation_phase_skip') == 'execution_gate'


def test_record_execution_gate_skip_tracks_reason_and_sample_once() -> None:
    counts = {}
    examples = {}

    record_execution_gate_skip(
        'planner_activation_phase_skip',
        'https://a.example.com/',
        {'family': 'authz', 'state_band': 'warmup'},
        counts,
        examples,
    )
    record_execution_gate_skip(
        'planner_activation_phase_skip',
        'https://a.example.com/',
        {'family': 'authz', 'state_band': 'warmup'},
        counts,
        examples,
    )

    assert counts['planner_activation_phase_skip'] == 2
    assert examples['planner_activation_phase_skip'] == ['https://a.example.com/;family=authz;state=warmup']


def test_execution_gate_skip_example_includes_synthesis_explainability_when_present() -> None:
    counts = {}
    examples = {}

    record_execution_gate_skip(
        'planner_synthesis_skip',
        'https://a.example.com/',
        {
            'family': 'authz',
            'state_band': 'warmup',
            'synthesis_recommended_action': 'pivot',
            'synthesis_reason': 'dead_end_pressure_redirect',
            'synthesis_next_stage': 'bounded_exploit_proof',
            'synthesis_gate_family': 'recon',
        },
        counts,
        examples,
    )

    assert counts['planner_synthesis_skip'] == 1
    sample = examples['planner_synthesis_skip'][0]
    assert 'synthesis_action=pivot' in sample
    assert 'synthesis_reason=dead_end_pressure_redirect' in sample
    assert 'synthesis_stage=bounded_exploit_proof' in sample
    assert 'synthesis_family=recon' in sample


def test_execution_gate_log_parts_and_summary_payload_share_reason_shaping() -> None:
    reason, host, detail = execution_gate_log_parts(
        {
            'reason_code': 'planner_conditional_gate_skip',
            'host': 'a.example.com',
            'family': 'authz',
            'state_band': 'warmup',
            'blockers': ['planner_conditional_gate'],
            'detail': 'host=a.example.com;family=authz;conditional_gate=authenticated_or_boundary_mapping',
        },
        'followup',
    )
    summary = execution_gate_summary_payload(
        {'planner_conditional_gate_skip': 2, 'warmup_gate_skip': 1},
        {'planner_conditional_gate_skip': ['https://a.example.com/;family=authz;state=warmup']},
    )

    assert reason == 'planner_conditional_gate_skip'
    assert host == 'a.example.com'
    assert 'mode=followup' in detail
    assert 'planner_conditional_gate' in detail
    assert summary['total'] == 3
    assert summary['top_text'].startswith('planner_conditional_gate_skip:2')
    assert 'planner_conditional_gate_skip=>https://a.example.com/;family=authz;state=warmup' in summary['example_text']


def test_synthesis_skip_summary_aggregates_action_and_stage_breakdown() -> None:
    summary = synthesis_skip_summary(
        {'planner_synthesis_skip': 4},
        {
            'planner_synthesis_skip': [
                'https://a.example.com/;family=authz;state=warmup;synthesis_action=pivot;synthesis_reason=dead_end_pressure_redirect;synthesis_stage=bounded_exploit_proof;synthesis_family=recon',
                'https://b.example.com/;family=authz;state=warmup;synthesis_action=abandon;synthesis_reason=weak_validation_signal;synthesis_stage=validation;synthesis_family=recon',
                'https://c.example.com/;family=workflow;state=promising;synthesis_action=abandon;synthesis_reason=weak_validation_signal;synthesis_stage=validation;synthesis_family=content_discovery',
            ]
        },
    )

    assert summary['total'] == 4
    assert ('abandon', 2) in summary['actions']
    assert ('pivot', 1) in summary['actions']
    assert ('validation', 2) in summary['stages']
    assert ('bounded_exploit_proof', 1) in summary['stages']
    assert 'weak_validation_signal:2' in summary['reason_text']
    assert 'recon:2' in summary['family_text']


def test_execution_gate_log_parts_include_synthesis_explainability_when_present() -> None:
    reason, host, detail = execution_gate_log_parts(
        {
            'reason_code': 'planner_synthesis_skip',
            'host': 'a.example.com',
            'family': 'authz',
            'state_band': 'warmup',
            'blockers': ['planner_synthesis_gate'],
            'synthesis_recommended_action': 'abandon',
            'synthesis_reason': 'weak_validation_signal',
            'synthesis_next_stage': 'validation',
            'synthesis_gate_family': 'recon',
            'detail': 'host=a.example.com;family=authz;synthesis=weak_validation_signal;mode=followup',
        },
        'followup',
    )

    assert reason == 'planner_synthesis_skip'
    assert host == 'a.example.com'
    assert 'synthesis_action=abandon' in detail
    assert 'synthesis_reason=weak_validation_signal' in detail
    assert 'synthesis_stage=validation' in detail
    assert 'synthesis_family=recon' in detail


def test_execution_gate_summary_payload_includes_synthesis_skip_breakdown() -> None:
    summary = execution_gate_summary_payload(
        {'planner_synthesis_skip': 3, 'warmup_gate_skip': 1},
        {
            'planner_synthesis_skip': [
                'https://a.example.com/;family=authz;state=warmup;synthesis_action=pivot;synthesis_reason=dead_end_pressure_redirect;synthesis_stage=bounded_exploit_proof;synthesis_family=recon',
                'https://b.example.com/;family=authz;state=warmup;synthesis_action=abandon;synthesis_reason=weak_validation_signal;synthesis_stage=validation;synthesis_family=recon',
            ]
        },
    )

    assert summary['synthesis_skip']['total'] == 3
    assert 'pivot:1' in summary['synthesis_skip']['action_text']
    assert 'abandon:1' in summary['synthesis_skip']['action_text']
    assert 'validation:1' in summary['synthesis_skip']['stage_text']
    assert 'bounded_exploit_proof:1' in summary['synthesis_skip']['stage_text']
