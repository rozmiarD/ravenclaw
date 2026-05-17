from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from auto_campaign_targets import host_from_target  # type: ignore
from evaluation_bundle import build_replay_dataset_from_summary  # type: ignore
from evaluation_metrics import aggregate_replay_metrics  # type: ignore
from evaluation_replay import replay_dataset  # type: ignore
from offensive_reporting_artifacts import build_branch_campaignlets, build_exploit_motif_memory, build_proof_bundles, persist_runtime_state_artifacts  # type: ignore
from runtime_economics_aggregate import aggregate_runtime_economics  # type: ignore
from govengine.contracts.signal import adaptation_feedback_status, finding_signal_status, success_outcome_status, workflow_promotion_status  # type: ignore
from semantic_lineage import ensure_semantic_lineage, ensure_semantic_lineage_summary  # type: ignore


def render_host_summary(runs: list[dict], lineage_audit: dict | None = None) -> str:
    groups: dict[str, list[dict]] = {}
    for run in runs:
        host = host_from_target(run.get("target", "unknown"))
        groups.setdefault(host, []).append(run)

    def classify_note(cls: str) -> str:
        mapping = {
            "not_found_enforced": "Endpoint returned 404 (likely locked down).",
            "authz_enforced": "Authorization guard blocked unauthenticated probe.",
            "method_enforced": "HTTP verb restricted; try alternate method.",
            "input_validated": "Input sanitization in place.",
            "empty_response": "No meaningful data in body.",
            "healthy_endpoint": "Health endpoint responded OK.",
            "unknown": "Requires manual log review.",
        }
        return mapping.get(cls, cls)

    audit = dict(lineage_audit or {}) if isinstance(lineage_audit, dict) else {}
    audit_stats = dict(audit.get('stats') or {}) if isinstance(audit.get('stats'), dict) else {}
    lines = ["# Auto Campaign Host Summary", f"Generated: {datetime.now(timezone.utc).isoformat()}", ""]
    if audit_stats:
        lines.append(f"- Lineage audit: status={audit.get('status', 'unknown')} gate_ready={audit.get('gate_ready', False)} items={audit_stats.get('total_items', 0)} unique={audit_stats.get('unique_lineages', 0)} duplicates={audit_stats.get('duplicate_lineages', 0)} missing={audit_stats.get('missing_lineages', 0)}")
        lines.append("")
    for host, host_runs in groups.items():
        lines.append(f"## {host}")
        lines.append(f"- Runs: {len(host_runs)}")
        latest = host_runs[-1]
        cls = latest.get("classification")
        latest_signal = latest.get('signal_contract') if isinstance(latest.get('signal_contract'), dict) else {}
        latest_compiler = latest.get('engine_compiler') if isinstance(latest.get('engine_compiler'), dict) else {}
        latest_semantic = latest_compiler.get('semantic_loss_policy') if isinstance(latest_compiler.get('semantic_loss_policy'), dict) else {}
        latest_runtime_task = latest.get('runtime_task') if isinstance(latest.get('runtime_task'), dict) else {}
        latest_lineage = ensure_semantic_lineage(
            lineage=(latest.get('semantic_lineage') if isinstance(latest.get('semantic_lineage'), dict) else (latest_runtime_task.get('semantic_lineage') if isinstance(latest_runtime_task.get('semantic_lineage'), dict) else {})),
            task=latest,
            runtime_task=latest_runtime_task,
            source='report_host_summary',
        )
        latest_lineage_summary = ensure_semantic_lineage_summary(
            summary=(latest.get('semantic_lineage_summary') if isinstance(latest.get('semantic_lineage_summary'), dict) else {}),
            lineage=latest_lineage,
        )
        lines.append(f"- Latest classification: {cls} ({classify_note(cls)})")
        lines.append(f"- Engine status: {latest.get('engine_status')} | Mode: {latest.get('mode', 'fast')}")
        lines.append(f"- Workflow promotion: {workflow_promotion_status(latest_signal) or '-'} | Success outcome: {success_outcome_status(latest_signal) or '-'} | Adaptation: {adaptation_feedback_status(latest_signal) or '-'}")
        lines.append(f"- Semantic loss: {latest_semantic.get('loss_class', 'none')} | Response: {latest_semantic.get('policy_response', 'proceed')} | Approved under degradation: {latest_semantic.get('approved_under_degradation', False)}")
        lines.append(f"- Semantic lineage: {str(latest_lineage_summary.get('lineage_sha256') or '')[:12] or '-'} | Stage: {latest_lineage_summary.get('current_stage', '-')} → {latest_lineage_summary.get('next_stage', '-')}")
        lines.append("- Objectives:")
        for run in host_runs:
            lines.append(f"  - [{run.get('mode', 'fast')}] {run.get('objective', 'n/a')} → {run.get('engine_status')} ({run.get('classification')})")
        lines.append("")
    return "\n".join(lines)


def write_host_summary(runs: list[dict], path: str, lineage_audit: dict | None = None) -> str:
    text = render_host_summary(runs, lineage_audit=lineage_audit)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return text


def write_run_details(runs: list[dict], dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for run in runs:
        idx = run.get("index", 0)
        name = run.get("plan_name") or run.get("objective") or f"run-{idx}"
        safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in (name or "").lower()).strip("-")
        safe = (safe[:80] or f"run-{idx}").strip("-")
        filename = dest_dir / f"{idx:02d}-{safe}.md"
        decision = run.get('runtime_decision') if isinstance(run.get('runtime_decision'), dict) else {}
        explain = decision.get('explain') if isinstance(decision.get('explain'), dict) else {}
        signal_contract = run.get('signal_contract') if isinstance(run.get('signal_contract'), dict) else {}
        runtime_task = run.get('runtime_task') if isinstance(run.get('runtime_task'), dict) else {}
        semantic_lineage = ensure_semantic_lineage(
            lineage=(run.get('semantic_lineage') if isinstance(run.get('semantic_lineage'), dict) else (runtime_task.get('semantic_lineage') if isinstance(runtime_task.get('semantic_lineage'), dict) else {})),
            task=run,
            runtime_task=runtime_task,
            source='report_run_detail',
        )
        lineage_summary = ensure_semantic_lineage_summary(
            summary=(run.get('semantic_lineage_summary') if isinstance(run.get('semantic_lineage_summary'), dict) else {}),
            lineage=semantic_lineage,
        )
        planner_contract = semantic_lineage.get('planner_contract') if isinstance(semantic_lineage.get('planner_contract'), dict) else {}
        artifact_boundaries = semantic_lineage.get('artifact_boundaries') if isinstance(semantic_lineage.get('artifact_boundaries'), dict) else {}
        planning_ladder = planner_contract.get('planning_ladder') if isinstance(planner_contract.get('planning_ladder'), dict) else {}
        lines = [
            f"# Run {idx}: {name}", "",
            f"- Objective: {run.get('objective')}",
            f"- Target: {run.get('target')}",
            f"- Mode: {run.get('mode')}",
            f"- Aggression: {run.get('aggression')}",
            f"- Owner override: {run.get('owner_override')}",
            f"- Auditor decision: {run.get('auditor_decision')}",
            f"- Engine status: {run.get('engine_status')} | Classification: {run.get('classification')}",
            f"- Signal assessment: {run.get('signal_assessment')}",
            f"- Workflow promotion: {workflow_promotion_status(signal_contract) or '-'}",
            f"- Finding signal: {finding_signal_status(signal_contract) or '-'}",
            f"- Success outcome: {success_outcome_status(signal_contract) or '-'}",
            f"- Adaptation feedback: {adaptation_feedback_status(signal_contract) or '-'}",
            f"- Signal contract: {signal_contract}",
            f"- Decision intent flags: {run.get('decision_intent_flags')}",
            f"- Decision effective flags: {run.get('decision_flags')}",
            f"- Decision effective status: {run.get('decision_effective_status')}",
            f"- Decision effective summary: {run.get('decision_effective_summary')}",
            f"- Action type: {(run.get('brain_reasoning_summary') or {}).get('action_type') if isinstance(run.get('brain_reasoning_summary'), dict) else '-'}",
            f"- Hypothesis support: {(run.get('analysis_contract') or {}).get('hypothesis_support') if isinstance(run.get('analysis_contract'), dict) else '-'}",
            f"- Expected signal observed: {(run.get('analysis_contract') or {}).get('expected_signal_observed') if isinstance(run.get('analysis_contract'), dict) else '-'}",
            f"- Evidence goal met: {(run.get('analysis_contract') or {}).get('evidence_goal_met') if isinstance(run.get('analysis_contract'), dict) else '-'}",
            f"- Semantic execution fit: {(run.get('analysis_contract') or {}).get('semantic_execution_fit') if isinstance(run.get('analysis_contract'), dict) else '-'}",
            f"- Semantic loss class: {(run.get('analysis_contract') or {}).get('semantic_loss_class') if isinstance(run.get('analysis_contract'), dict) else ((run.get('engine_compiler') or {}).get('semantic_loss_policy') or {}).get('loss_class', '-')}",
            f"- Semantic loss response: {(run.get('analysis_contract') or {}).get('semantic_loss_policy_response') if isinstance(run.get('analysis_contract'), dict) else ((run.get('engine_compiler') or {}).get('semantic_loss_policy') or {}).get('policy_response', '-')}",
            f"- Approved under degradation: {(run.get('analysis_contract') or {}).get('approved_under_degradation') if isinstance(run.get('analysis_contract'), dict) else ((run.get('engine_compiler') or {}).get('semantic_loss_policy') or {}).get('approved_under_degradation', False)}",
            f"- Semantic rereview required: {run.get('semantic_loss_rereview_required', False)} | completed: {run.get('semantic_loss_rereview_completed', False)} | decision: {run.get('semantic_loss_rereview_decision', '')}",
            f"- Decision why: {', '.join(explain.get('why', [])) if isinstance(explain.get('why'), list) else '-'}",
            f"- Decision blockers: {', '.join(explain.get('blockers', [])) if isinstance(explain.get('blockers'), list) else '-'}",
            f"- Decision effective blockers: {run.get('decision_effective_blockers')}",
            f"- Decision economics: {run.get('decision_economics')}",
            f"- Semantic lineage hash: {lineage_summary.get('lineage_sha256', '')}",
            f"- Planner/runtime boundary hashes: planner={artifact_boundaries.get('planner_contract_sha256', '')} runtime={artifact_boundaries.get('runtime_contract_sha256', '')}",
            f"- Lineage stage: {lineage_summary.get('current_stage', '-')} -> {lineage_summary.get('next_stage', '-')}",
            f"- Target surface rationale: {lineage_summary.get('target_surface_rationale', [])}",
            f"- Execution gate: {run.get('execution_gate')}",
            f"- Host state band: {run.get('host_state_band')}",
            f"- Host transition: {run.get('host_transition')}",
            f"- Host regeneration reason: {run.get('host_regeneration_reason')}",
            "", "## Stdout preview", "```", run.get("engine_stdout_preview") or "", "```",
        ]
        filename.write_text("\n".join(lines), encoding="utf-8")


def record_run(runs: list[dict], info: dict, findings_history_path: Path, campaign_key: str) -> None:
    runs.append(info)
    try:
        rec = dict(info or {})
        rec["campaign_key"] = campaign_key
        rec["recorded_at"] = datetime.now(timezone.utc).isoformat()
        findings_history_path.parent.mkdir(parents=True, exist_ok=True)
        with findings_history_path.open("a", encoding="utf-8") as h:
            h.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _build_semantic_lineage_index(runs: list[dict]) -> dict[str, object]:
    items: list[dict[str, object]] = []
    seen_hashes: dict[str, int] = {}
    missing = 0
    for r in runs:
        semantic_lineage = ensure_semantic_lineage(
            lineage=(r.get('semantic_lineage') if isinstance(r.get('semantic_lineage'), dict) else {}),
            task=r,
            runtime_task=(r.get('runtime_task') if isinstance(r.get('runtime_task'), dict) else {}),
            source='report_summary_vector',
        )
        summary = ensure_semantic_lineage_summary(
            summary=(r.get('semantic_lineage_summary') if isinstance(r.get('semantic_lineage_summary'), dict) else {}),
            lineage=semantic_lineage,
        )
        lineage_hash = str(summary.get('lineage_sha256') or '').strip()
        if not lineage_hash:
            missing += 1
            continue
        idx = int(r.get('index') or 0)
        name = r.get('plan_name') or r.get('objective') or f'run-{idx}'
        safe = ''.join(c if c.isalnum() or c in '-_' else '-' for c in str(name or '').lower()).strip('-')
        safe = (safe[:80] or f'run-{idx}').strip('-')
        seen_hashes[lineage_hash] = int(seen_hashes.get(lineage_hash, 0)) + 1
        items.append({
            'lineage_sha256': lineage_hash,
            'index': idx,
            'objective': r.get('objective'),
            'target': r.get('target'),
            'task_family': summary.get('task_family'),
            'current_stage': summary.get('current_stage'),
            'next_stage': summary.get('next_stage'),
            'run_detail_path': f'run-details/{idx:02d}-{safe}.md',
        })
    items.sort(key=lambda item: (int(item.get('index') or 0), str(item.get('lineage_sha256') or '')))
    duplicate_hashes = sorted([h for h, c in seen_hashes.items() if c > 1])
    return {
        'version': 2,
        'items': items,
        'stats': {
            'total_items': len(items),
            'unique_lineages': len(seen_hashes),
            'duplicate_lineages': len(duplicate_hashes),
            'missing_lineages': missing,
        },
        'duplicate_hashes': duplicate_hashes,
    }



def _lineage_audit_summary(index: dict[str, object]) -> dict[str, object]:
    stats = dict(index.get('stats') or {}) if isinstance(index.get('stats'), dict) else {}
    missing = int(stats.get('missing_lineages', 0) or 0)
    duplicates = int(stats.get('duplicate_lineages', 0) or 0)
    status = 'passed'
    if missing > 0:
        status = 'failed'
    elif duplicates > 0:
        status = 'warn'
    return {
        'version': index.get('version', 0),
        'status': status,
        'gate_ready': bool(missing == 0),
        'stats': stats,
        'duplicate_hashes': list(index.get('duplicate_hashes') or []),
    }



def _build_summary_vector(run: dict) -> dict[str, object]:
    runtime_task = run.get('runtime_task') if isinstance(run.get('runtime_task'), dict) else {}
    semantic_lineage = ensure_semantic_lineage(
        lineage=(run.get('semantic_lineage') if isinstance(run.get('semantic_lineage'), dict) else {}),
        task=run,
        runtime_task=runtime_task,
        source='report_summary_vector',
    )
    semantic_lineage_summary = ensure_semantic_lineage_summary(
        summary=(run.get('semantic_lineage_summary') if isinstance(run.get('semantic_lineage_summary'), dict) else {}),
        lineage=semantic_lineage,
        task=run,
        runtime_task=runtime_task,
        source='report_summary_vector',
    )
    signal_contract = run.get('signal_contract') if isinstance(run.get('signal_contract'), dict) else {}
    compiler = run.get('engine_compiler') if isinstance(run.get('engine_compiler'), dict) else {}
    semantic_loss_policy = compiler.get('semantic_loss_policy') if isinstance(compiler.get('semantic_loss_policy'), dict) else {}
    return {
        "index": run.get("index"),
        "objective": run.get("objective"),
        "target": run.get("target"),
        "mode": run.get("mode"),
        "aggression": run.get("aggression"),
        "plan_name": run.get("plan_name"),
        "owner_override": run.get("owner_override"),
        "owner_approved_auth": run.get("owner_approved_auth"),
        "auditor_decision": run.get("auditor_decision"),
        "engine_status": run.get("engine_status"),
        "classification": run.get("classification"),
        "promising": run.get("promising"),
        "signal_assessment": run.get("signal_assessment"),
        "signal_contract": signal_contract,
        "workflow_promotion_status": workflow_promotion_status(signal_contract),
        "finding_signal_status": finding_signal_status(signal_contract),
        "success_outcome_status": success_outcome_status(signal_contract),
        "adaptation_feedback_status": adaptation_feedback_status(signal_contract),
        "semantic_loss_policy": semantic_loss_policy,
        "semantic_loss_class": semantic_loss_policy.get("loss_class", 'none'),
        "semantic_loss_policy_response": semantic_loss_policy.get("policy_response", 'proceed'),
        "approved_under_degradation": semantic_loss_policy.get("approved_under_degradation", False),
        "semantic_loss_rereview_required": run.get("semantic_loss_rereview_required"),
        "semantic_loss_rereview_completed": run.get("semantic_loss_rereview_completed"),
        "semantic_loss_rereview_decision": run.get("semantic_loss_rereview_decision"),
        "stdout_preview": run.get("engine_stdout_preview"),
        "decision_intent_flags": run.get("decision_intent_flags"),
        "decision_flags": run.get("decision_flags"),
        "decision_effective_status": run.get("decision_effective_status"),
        "decision_effective_summary": run.get("decision_effective_summary"),
        "decision_explain": run.get("decision_explain"),
        "decision_economics": run.get("decision_economics"),
        "brain_reasoning_summary": run.get("brain_reasoning_summary"),
        "engine_compiler": run.get("engine_compiler"),
        "analysis_contract": run.get("analysis_contract"),
        "success_semantics": run.get("success_semantics"),
        "execution_gate": run.get("execution_gate"),
        "semantic_lineage": semantic_lineage,
        "semantic_lineage_summary": semantic_lineage_summary,
        "host_state_band": run.get("host_state_band"),
        "host_transition": run.get("host_transition"),
        "host_regeneration_reason": run.get("host_regeneration_reason"),
    }



def finalize_outputs(
    *,
    runs: list[dict],
    campaign_validation: dict,
    run_started,
    max_runs: int,
    time_budget_min: int,
    retry_policy: str,
    out_path: str,
    reports_dir: Path,
    archive_root: Path,
) -> dict:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    economics_summary = aggregate_runtime_economics(runs)
    summary = {
        "run_id": run_id,
        "campaign_validation": campaign_validation,
        "started_at": run_started.isoformat(),
        "max_runs": max_runs,
        "time_budget_min": time_budget_min,
        "retry_policy": retry_policy,
        "executed": len(runs),
        "economics": economics_summary,
        "runs": runs,
        "vectors": [_build_summary_vector(r) for r in runs],
    }
    lineage_index = _build_semantic_lineage_index(summary.get('vectors') or [])
    summary['lineage_audit'] = _lineage_audit_summary(lineage_index)
    evaluation_dataset = build_replay_dataset_from_summary(summary)
    evaluation_replay = replay_dataset(evaluation_dataset)
    evaluation_metrics = aggregate_replay_metrics(evaluation_replay.get('results') or [])
    branch_campaignlets = build_branch_campaignlets(summary.get('vectors') or [])
    exploit_motif_memory = build_exploit_motif_memory(summary.get('vectors') or [], branch_campaignlets)
    proof_bundles = build_proof_bundles(summary.get('vectors') or [], branch_campaignlets)
    summary['evaluation'] = {
        'dataset_id': evaluation_dataset.get('dataset_id'),
        'bundle_count': evaluation_replay.get('bundle_count', 0),
        'status_counts': evaluation_replay.get('status_counts', {}),
        'metrics': evaluation_metrics,
    }
    summary['branch_campaignlets'] = branch_campaignlets
    summary['exploit_motif_memory'] = exploit_motif_memory
    summary['proof_bundles'] = proof_bundles
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    host_summary = write_host_summary(runs, str(reports_dir / "auto-campaign-summary.md"), lineage_audit=summary['lineage_audit'])
    archive_dir = archive_root / run_id
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (archive_dir / "summary.md").write_text(host_summary, encoding="utf-8")
    write_run_details(runs, archive_dir / "run-details")
    (archive_dir / 'semantic-lineage-index.json').write_text(json.dumps(lineage_index, ensure_ascii=False, indent=2), encoding='utf-8')
    (archive_dir / 'evaluation-replay.json').write_text(json.dumps(evaluation_replay, ensure_ascii=False, indent=2), encoding='utf-8')
    (archive_dir / 'evaluation-metrics.json').write_text(json.dumps(evaluation_metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    (archive_dir / 'branch-campaignlets.json').write_text(json.dumps(branch_campaignlets, ensure_ascii=False, indent=2), encoding='utf-8')
    (archive_dir / 'exploit-motif-memory.json').write_text(json.dumps(exploit_motif_memory, ensure_ascii=False, indent=2), encoding='utf-8')
    (archive_dir / 'proof-bundles.json').write_text(json.dumps(proof_bundles, ensure_ascii=False, indent=2), encoding='utf-8')
    persist_runtime_state_artifacts(
        reports_dir=reports_dir,
        artifacts={
            'branch-campaignlets.json': branch_campaignlets,
            'exploit-motif-memory.json': exploit_motif_memory,
            'proof-bundles.json': proof_bundles,
        },
    )
    latest_link = reports_dir / "latest"
    try:
        if latest_link.is_symlink() or latest_link.exists():
            latest_link.unlink()
    except FileNotFoundError:
        pass
    latest_link.symlink_to(archive_dir)
    return summary
