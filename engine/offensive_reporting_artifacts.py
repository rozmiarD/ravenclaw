from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from auto_campaign_targets import host_from_target  # type: ignore
from paths import rsp  # type: ignore
from semantic_lineage import ensure_semantic_lineage, ensure_semantic_lineage_summary  # type: ignore
from govengine.contracts.signal import adaptation_feedback_status, finding_signal_status, success_outcome_status, workflow_promotion_status  # type: ignore


ProofArtifact = dict[str, object]
RuntimeVector = dict[str, Any]


def _planner_contract_for_vector(vector: RuntimeVector) -> dict[str, Any]:
    runtime_task = vector.get('runtime_task') if isinstance(vector.get('runtime_task'), dict) else {}
    semantic_lineage = runtime_task.get('semantic_lineage') if isinstance(runtime_task.get('semantic_lineage'), dict) else {}
    return semantic_lineage.get('planner_contract') if isinstance(semantic_lineage.get('planner_contract'), dict) else {}


def _planner_task_family_for_vector(vector: RuntimeVector) -> str:
    planner_contract = _planner_contract_for_vector(vector)
    return str(planner_contract.get('task_family') or '').strip()


def _planner_ladder_for_vector(vector: RuntimeVector) -> dict[str, Any]:
    planner_contract = _planner_contract_for_vector(vector)
    return planner_contract.get('planning_ladder') if isinstance(planner_contract.get('planning_ladder'), dict) else {}


def _lineage_summary_for_vector(vector: RuntimeVector, *, source: str) -> dict[str, Any]:
    runtime_task = vector.get('runtime_task') if isinstance(vector.get('runtime_task'), dict) else {}
    semantic_lineage = ensure_semantic_lineage(
        lineage=(vector.get('semantic_lineage') if isinstance(vector.get('semantic_lineage'), dict) else (runtime_task.get('semantic_lineage') if isinstance(runtime_task.get('semantic_lineage'), dict) else {})),
        task=vector,
        runtime_task=runtime_task,
        source=source,
    )
    return ensure_semantic_lineage_summary(
        summary=(vector.get('semantic_lineage_summary') if isinstance(vector.get('semantic_lineage_summary'), dict) else {}),
        lineage=semantic_lineage,
    )


def _branch_stage_score(current_stage: str, next_stage: str) -> float:
    proof_adjacent = {
        'bounded_exploit_proof': 1.0,
        'exploit_confirmation': 1.0,
        'reportable_proof': 1.0,
        'state_transition_confirmation': 0.85,
        'workflow_confirmation': 0.85,
        'authz_confirmation': 0.85,
        'confirm': 0.8,
        'followup': 0.7,
        'precision': 0.6,
        'recon': 0.4,
        'enumeration': 0.4,
    }
    for candidate in (str(next_stage or '').strip(), str(current_stage or '').strip()):
        if candidate in proof_adjacent:
            return proof_adjacent[candidate]
    return 0.5


def _signal_score(signal_contract: dict[str, Any]) -> float:
    workflow_status = workflow_promotion_status(signal_contract) or ''
    finding_status = finding_signal_status(signal_contract) or ''
    success_status = success_outcome_status(signal_contract) or ''
    adaptation_status = adaptation_feedback_status(signal_contract) or ''
    score = 0.0
    if workflow_status in {'confirmable', 'promotable', 'candidate'}:
        score += 0.3 if workflow_status == 'confirmable' else 0.2
    if finding_status in {'strong', 'high', 'confirmed'}:
        score += 0.3
    elif finding_status in {'medium', 'partial'}:
        score += 0.2
    if success_status in {'partial', 'confirmed', 'reportable'}:
        score += 0.2
    if adaptation_status in {'positive', 'promote', 'continue'}:
        score += 0.1
    return min(score, 1.0)


def _governance_score(vector: RuntimeVector) -> float:
    execution_gate = vector.get('execution_gate') if isinstance(vector.get('execution_gate'), dict) else {}
    gate_status = str(execution_gate.get('status') or '').strip().lower()
    compiler = vector.get('engine_compiler') if isinstance(vector.get('engine_compiler'), dict) else {}
    semantic_policy = compiler.get('semantic_loss_policy') if isinstance(compiler.get('semantic_loss_policy'), dict) else {}
    loss_class = str(semantic_policy.get('loss_class') or vector.get('semantic_loss_class') or 'none').strip().lower()
    if gate_status and gate_status not in {'passed', 'pass', 'ok'}:
        return 0.2
    if loss_class in {'none', ''}:
        return 1.0
    if loss_class in {'bounded_lowering', 'bounded'}:
        return 0.8
    return 0.5


def _fanout_score(vector: RuntimeVector) -> float:
    reasoning = vector.get('brain_reasoning_summary') if isinstance(vector.get('brain_reasoning_summary'), dict) else {}
    siblings = reasoning.get('sibling_hypotheses') if isinstance(reasoning.get('sibling_hypotheses'), list) else []
    analysis_contract = vector.get('analysis_contract') if isinstance(vector.get('analysis_contract'), dict) else {}
    open_questions = analysis_contract.get('open_questions') if isinstance(analysis_contract.get('open_questions'), list) else []
    richness = min(len(siblings), 2) + min(len(open_questions), 2)
    return min(0.4 + (0.15 * richness), 1.0)


def _pending_proof_direction(vector: RuntimeVector, lineage_summary: dict[str, Any], signal_contract: dict[str, Any]) -> str:
    next_stage = str(lineage_summary.get('next_stage') or '').strip()
    workflow_status = workflow_promotion_status(signal_contract) or ''
    finding_status = finding_signal_status(signal_contract) or ''
    if next_stage:
        return next_stage
    if workflow_status == 'confirmable' and finding_status in {'strong', 'high', 'confirmed'}:
        return 'bounded_exploit_proof'
    if workflow_status in {'candidate', 'promotable', 'confirmable'}:
        return 'state_transition_confirmation'
    return 'collect_more_evidence'


def build_branch_campaignlets(vectors: list[RuntimeVector]) -> ProofArtifact:
    items: list[dict[str, object]] = []
    for vector in vectors:
        lineage_summary = _lineage_summary_for_vector(vector, source='report_branch_campaignlet')
        signal_contract = vector.get('signal_contract') if isinstance(vector.get('signal_contract'), dict) else {}
        planner_ladder = _planner_ladder_for_vector(vector)
        current_stage = str(planner_ladder.get('current_stage') or lineage_summary.get('current_stage') or '').strip()
        next_stage = str(planner_ladder.get('next_stage') or lineage_summary.get('next_stage') or '').strip()
        stage_score = _branch_stage_score(
            current_stage,
            next_stage,
        )
        signal_score = _signal_score(signal_contract)
        governance_score = _governance_score(vector)
        fanout_score = _fanout_score(vector)
        persistence_score = round((0.35 * stage_score) + (0.35 * signal_score) + (0.2 * governance_score) + (0.1 * fanout_score), 3)
        if persistence_score < 0.45 and not bool(vector.get('promising')):
            continue
        analysis_contract = vector.get('analysis_contract') if isinstance(vector.get('analysis_contract'), dict) else {}
        brain_reasoning = vector.get('brain_reasoning_summary') if isinstance(vector.get('brain_reasoning_summary'), dict) else {}
        success_semantics = vector.get('success_semantics') if isinstance(vector.get('success_semantics'), dict) else {}
        execution_gate = vector.get('execution_gate') if isinstance(vector.get('execution_gate'), dict) else {}
        items.append({
            'lineage_sha256': lineage_summary.get('lineage_sha256'),
            'target': vector.get('target'),
            'target_host': host_from_target(vector.get('target', 'unknown')),
            'objective': vector.get('objective'),
            'task_family': _planner_task_family_for_vector(vector) or lineage_summary.get('task_family') or vector.get('task_family') or success_semantics.get('typed_family_eval') or '',
            'current_stage': current_stage,
            'next_stage': next_stage,
            'primary_hypothesis': analysis_contract.get('primary_hypothesis') or analysis_contract.get('hypothesis') or vector.get('objective'),
            'action_type': brain_reasoning.get('action_type'),
            'workflow_status': workflow_promotion_status(signal_contract),
            'finding_signal_status': finding_signal_status(signal_contract),
            'success_outcome_status': success_outcome_status(signal_contract),
            'governance_status': execution_gate.get('status'),
            'persistence_score': persistence_score,
            'pending_proof_direction': _pending_proof_direction(vector, lineage_summary, signal_contract),
        })
    items.sort(key=lambda item: (-float(item.get('persistence_score') or 0.0), str(item.get('lineage_sha256') or '')))
    return {
        'schema_version': 'branch-campaignlets-v1',
        'count': len(items),
        'items': items,
    }


def build_exploit_motif_memory(vectors: list[RuntimeVector], branch_campaignlets: ProofArtifact) -> ProofArtifact:
    grouped: dict[tuple[str, str, str, str], dict[str, object]] = {}
    vector_by_lineage: dict[str, RuntimeVector] = {}
    for vector in vectors:
        lineage_summary = _lineage_summary_for_vector(vector, source='report_exploit_motif_memory')
        lineage_hash = str(lineage_summary.get('lineage_sha256') or '').strip()
        if lineage_hash:
            vector_by_lineage[lineage_hash] = vector
    for item in list(branch_campaignlets.get('items') or []):
        if not isinstance(item, dict):
            continue
        lineage_hash = str(item.get('lineage_sha256') or '').strip()
        vector = vector_by_lineage.get(lineage_hash, {})
        task_family = str(item.get('task_family') or '').strip() or 'generic'
        current_stage = str(item.get('current_stage') or '').strip() or 'unknown'
        workflow_status = str(item.get('workflow_status') or '').strip() or 'unknown'
        brain_reasoning = vector.get('brain_reasoning_summary') if isinstance(vector.get('brain_reasoning_summary'), dict) else {}
        capability = str(brain_reasoning.get('capability') or '').strip() or 'http_probe'
        key = (task_family, current_stage, capability, workflow_status)
        entry = grouped.setdefault(key, {
            'task_family': task_family,
            'current_stage': current_stage,
            'capability': capability,
            'workflow_status': workflow_status,
            'occurrences': 0,
            'max_persistence_score': 0.0,
            'example_hypotheses': [],
        })
        entry['occurrences'] = int(entry.get('occurrences', 0) or 0) + 1
        entry['max_persistence_score'] = max(float(entry.get('max_persistence_score', 0.0) or 0.0), float(item.get('persistence_score') or 0.0))
        hypothesis = str(item.get('primary_hypothesis') or '').strip()
        examples = list(entry.get('example_hypotheses') or [])
        if hypothesis and hypothesis not in examples and len(examples) < 3:
            examples.append(hypothesis)
            entry['example_hypotheses'] = examples
    items = sorted(
        grouped.values(),
        key=lambda item: (-float(item.get('max_persistence_score') or 0.0), -int(item.get('occurrences') or 0), str(item.get('task_family') or '')),
    )
    return {
        'schema_version': 'exploit-motif-memory-v1',
        'count': len(items),
        'items': items,
    }


def build_proof_bundles(vectors: list[RuntimeVector], branch_campaignlets: ProofArtifact) -> ProofArtifact:
    vector_by_lineage: dict[str, RuntimeVector] = {}
    for vector in vectors:
        lineage_summary = _lineage_summary_for_vector(vector, source='report_proof_bundle')
        lineage_hash = str(lineage_summary.get('lineage_sha256') or '').strip()
        if lineage_hash:
            vector_by_lineage[lineage_hash] = vector
    items: list[dict[str, object]] = []
    for item in list(branch_campaignlets.get('items') or []):
        if not isinstance(item, dict):
            continue
        persistence_score = float(item.get('persistence_score') or 0.0)
        if persistence_score < 0.7:
            continue
        lineage_hash = str(item.get('lineage_sha256') or '').strip()
        vector = vector_by_lineage.get(lineage_hash, {})
        analysis_contract = vector.get('analysis_contract') if isinstance(vector.get('analysis_contract'), dict) else {}
        runtime_task = vector.get('runtime_task') if isinstance(vector.get('runtime_task'), dict) else {}
        actor_or_session_prerequisites = analysis_contract.get('actor_or_session_prerequisites') if isinstance(analysis_contract.get('actor_or_session_prerequisites'), list) else []
        acceptance_checks = runtime_task.get('acceptance_checks') if isinstance(runtime_task.get('acceptance_checks'), list) else []
        items.append({
            'lineage_sha256': lineage_hash,
            'target': item.get('target'),
            'task_family': item.get('task_family'),
            'current_stage': item.get('current_stage'),
            'next_stage': item.get('next_stage'),
            'primary_hypothesis': item.get('primary_hypothesis'),
            'signal_status': {
                'workflow': item.get('workflow_status'),
                'finding': item.get('finding_signal_status'),
                'success_outcome': item.get('success_outcome_status'),
            },
            'actor_or_session_prerequisites': list(actor_or_session_prerequisites),
            'acceptance_checks': list(acceptance_checks),
            'pending_proof_direction': item.get('pending_proof_direction'),
            'persistence_score': persistence_score,
        })
    items.sort(key=lambda entry: (-float(entry.get('persistence_score') or 0.0), str(entry.get('lineage_sha256') or '')))
    return {
        'schema_version': 'proof-bundles-v1',
        'count': len(items),
        'items': items,
    }


def persist_runtime_state_artifacts(*, reports_dir: Path, artifacts: dict[str, ProofArtifact]) -> None:
    runtime_state_dir = reports_dir.parent / 'state'
    for name, payload in artifacts.items():
        for path in {rsp(name), runtime_state_dir / name}:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
