#!/usr/bin/env python3
"""Curated auto-campaign runner for RAVEN-CLAW."""
from __future__ import annotations
import json
import re
import os
import socket
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qsl
import hashlib

SIGNAL_REGEX = {
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "akia": re.compile(r"AKIA[0-9A-Z]{16}"),
    "metrics": re.compile(r"__RC_METRICS__\s+([^\n]+)"),
}

from campaign_utils import load_scope_targets, summarize_scope, load_scope_domains
from campaign_validator import validate_campaign
from runtime_task_schema import normalize_runtime_task_v2  # type: ignore
from runtime_task_normalization import normalize_runtime_task as normalize_runtime_task_helper, merge_runtime_task_contract_metadata as merge_runtime_task_contract_metadata_helper, build_normalized_runtime_task_core as build_normalized_runtime_task_core_helper, ensure_runtime_task_view as ensure_runtime_task_view_helper  # type: ignore
from auto_campaign_downstream import post_run_decision  # type: ignore
from auto_campaign_queue import QueueCoordinator  # type: ignore
from auto_campaign_health import adaptive_aggression  # type: ignore
from auto_campaign_precheck import family_allowed_for_host_stage  # type: ignore
from auto_campaign_postprocess import post_result_common  # type: ignore
from auto_campaign_finalize import qualify_and_finalize_run  # type: ignore
from auto_campaign_persistence import record_and_persist_run as persist_recorded_run  # type: ignore
from auto_campaign_qualification import compute_promising, finding_lifecycle  # type: ignore
from status_utils import normalize_auditor_decision, normalize_engine_status, normalize_pipeline_status
from aggression_policy import clamp_aggression
from learning_store import top_progression_hints, update_learning, summarize_learning
from paths import OPENCLAW_ENV_PATH, RUNTIME_PLAN_PATH, wp, ep, REPORTS_DIR, LOGDASH_DIR  # type: ignore
from runtime_plan_service import regenerate_runtime_plan, load_runtime_plan_meta, load_active_campaign_blueprint, load_planner_ui_state  # type: ignore
from runtime_campaign_state import load_runtime_campaign_state, runtime_owner_override, runtime_aggression_override, resolve_campaign_key, campaign_settings_for_key  # type: ignore
from runtime_orchestrator import build_deduped_target_plan, build_execute_runtime_request, maybe_preempt_curated_entry, prepare_curated_task, prepare_runtime_task, resolve_main_loop_candidate, unpack_queued_task  # type: ignore
from json_state_io import atomic_write_json, safe_load_json_object  # type: ignore
from runtime_state_schemas import normalize_host_state  # type: ignore
from runtime_plan_control import refresh_planner_hints_and_reprioritize as apply_planner_hints_refresh, maybe_trigger_plan_regeneration as apply_plan_regeneration, reconcile_active_plan_if_needed as apply_plan_reconciliation, summarize_planner_feedback, adaptive_quality_context  # type: ignore
from runtime_runner_bootstrap import current_scope_summary, current_scope_targets, load_openclaw_env, load_runtime_toggles, maybe_reconsult_planner, selected_scope_path  # type: ignore
from runtime_override_control import refresh_runtime_overrides as apply_runtime_overrides  # type: ignore
from runtime_queue_strategy import reprioritize_queues as apply_queue_reprioritization  # type: ignore
from runtime_archetype_inference import adaptive_followup_explainability  # type: ignore
from runtime_runner_post_run_admission import quality_aware_followup_admission_hint as resolve_quality_aware_followup_admission_hint, apply_post_run_admission_hint as resolve_apply_post_run_admission_hint  # type: ignore
from runtime_runner_post_run_flow import run_post_run_actions as resolve_run_post_run_actions  # type: ignore
from runtime_followup_policy import next_followup_family as resolve_next_followup_family  # type: ignore
from runtime_runner_controls import MainRuntimeControls, build_main_runtime_controls  # type: ignore
from runtime_runner_session_setup import MainSessionBaseFields, MainSessionAliasFields, MainSessionSetup, build_main_session_base_fields, build_main_session_alias_fields, build_main_session_setup  # type: ignore
from runtime_runner_runtime_callbacks import persist_main_runtime_snapshot, refresh_main_runtime_overrides, build_main_runtime_callbacks, build_main_precheck_hooks  # type: ignore
from runtime_runner_persist_callbacks import RuntimePersistServices, RecordAndPersistRunInputs, build_runtime_persist_services, build_record_and_persist_run_inputs, build_main_persist_callbacks  # type: ignore
from runtime_runner_persist_callbacks_passthrough_wrapper import build_main_persist_callbacks as resolve_persist_callbacks_passthrough_wrapper  # type: ignore
from runtime_runner_execution_stage import ExecuteRunnerSessionInputs, FinalizeRunnerExceptionInputs, build_execute_runner_session_inputs, build_finalize_runner_exception_inputs  # type: ignore
from runtime_runner_bundle_builders import build_queue_coordinator, build_runtime_precheck_context_inputs, build_runtime_execution_deps, build_runtime_runner_deps, build_runtime_session_bundle_inputs  # type: ignore
from runtime_runner_task_execution_builders import build_post_run_action_inputs, build_execute_runtime_task_inputs, run_record_and_persist_stage  # type: ignore
from runtime_runner_state_aliases import MainStateAliases, build_main_state_aliases, make_skip_summary_flusher, build_main_skip_summary_flushers  # type: ignore
from runtime_runner_post_run_callback import build_main_post_run_actions_callback  # type: ignore
from runtime_runner_session_state_builders import build_runtime_session_state_from_bootstrap as resolve_runtime_session_state_from_bootstrap, build_runtime_session_state as resolve_runtime_session_state  # type: ignore
from runtime_runner_session_bundle_inputs_wrapper import build_runtime_session_bundle_inputs as resolve_session_bundle_inputs_wrapper  # type: ignore
from runtime_runner_planner_callback_wrapper import build_main_planner_callbacks as resolve_main_planner_callback_wrapper  # type: ignore
from runtime_runner_planner_callbacks_passthrough_wrapper import build_main_planner_callbacks as resolve_planner_callbacks_passthrough_wrapper  # type: ignore
from runtime_runner_bootstrap_loader import load_runtime_session_bootstrap as resolve_runtime_session_bootstrap  # type: ignore
from runtime_runner_execution_stage_runner import run_main_execution_stage as resolve_run_main_execution_stage  # type: ignore
from runtime_runner_execution_stage_passthrough_wrapper import run_main_execution_stage as resolve_execution_stage_passthrough_wrapper  # type: ignore
from runtime_runner_main_entry import run_main_entry as resolve_run_main_entry  # type: ignore
from runtime_runner_execute_completion_wrapper import complete_execute_runtime_pipeline_result as resolve_execute_completion_wrapper  # type: ignore
from runtime_runner_execute_task_callback_wrapper import build_main_execute_runtime_task_callback as resolve_execute_task_callback_wrapper  # type: ignore
from runtime_runner_complete_run_inputs_wrapper import build_complete_runtime_run_inputs as resolve_complete_run_inputs_wrapper  # type: ignore
from runtime_runner_execute_task_inputs_wrapper import build_execute_runtime_task_inputs as resolve_execute_task_inputs_wrapper  # type: ignore
from runtime_runner_prepare_callbacks import build_main_prepare_callbacks, prepare_task_precheck_from_context, reprioritize_main_prepare_queues  # type: ignore
from runtime_runner_queue_coordinator_wrapper import build_queue_coordinator as resolve_queue_coordinator_wrapper  # type: ignore
from runtime_runner_overrides_wrapper import refresh_main_runtime_overrides as resolve_overrides_wrapper  # type: ignore
from runtime_runner_post_run_actions_wrapper import build_main_post_run_actions_callback as resolve_post_run_actions_wrapper  # type: ignore
from runtime_runner_precheck_context_wrapper import build_runtime_precheck_context_inputs as resolve_precheck_context_wrapper  # type: ignore
from runtime_runner_record_persist_stage_wrapper import run_record_and_persist_stage as resolve_record_persist_stage_wrapper  # type: ignore
from runtime_runner_skip_flusher_wrapper import make_skip_summary_flusher as resolve_skip_flusher_wrapper  # type: ignore
from runtime_runner_skip_summary_wrapper import build_main_skip_summary_flushers as resolve_skip_summary_wrapper  # type: ignore
from runtime_runner_precheck_hooks_wrapper import build_main_precheck_hooks as resolve_precheck_hooks_wrapper  # type: ignore
from runtime_runner_prepare_callbacks_wrapper import build_main_prepare_callbacks as resolve_prepare_callbacks_wrapper  # type: ignore
from runtime_runner_runtime_callbacks_wrapper import build_main_runtime_callbacks as resolve_runtime_callbacks_wrapper  # type: ignore
from runtime_runner_snapshot_wrapper import persist_main_runtime_snapshot as resolve_snapshot_wrapper  # type: ignore
from runtime_runner_session_setup_wrapper import build_main_session_alias_fields as resolve_session_alias_fields_wrapper, build_main_session_base_fields as resolve_session_base_fields_wrapper, build_main_session_setup as resolve_session_setup_wrapper  # type: ignore
from runtime_runner_state_aliases_wrapper import build_main_state_aliases as resolve_state_aliases_wrapper  # type: ignore
from runtime_runner_planner_callbacks import build_main_planner_callbacks as resolve_main_planner_callbacks  # type: ignore
from runtime_runner_completion_callbacks import CompleteRuntimeRunInputs, build_complete_runtime_run_inputs, complete_execute_runtime_pipeline_result, build_main_execute_runtime_task_callback  # type: ignore
from runtime_runner_result_summary import summarize_result as resolve_runner_result_summary  # type: ignore
from runtime_effective_decision import apply_effective_decision  # type: ignore
from runtime_decision_projection import project_runtime_decision_to_run_info  # type: ignore
from runtime_run_completion import complete_runtime_run  # type: ignore
from runtime_task_execution import execute_runtime_task_pipeline  # type: ignore
from runtime_loop_control import run_curated_loop, run_main_loop  # type: ignore
from runtime_execution_deps import RuntimeExecutionDeps  # type: ignore
from runtime_runner_deps import RuntimeRunnerDeps  # type: ignore
from runtime_prepare_deps import RuntimePrepareDeps  # type: ignore
from runtime_precheck_context import RuntimePrecheckContext  # type: ignore
from runtime_session_bootstrap import build_runtime_session_bundles  # type: ignore
from feature_flags import normalize_pipeline_flags  # type: ignore
from runtime_persist_services import RuntimePersistServices, record_and_persist_runtime_run, apply_runtime_adaptation  # type: ignore
from runtime_session_state import RuntimeSessionState  # type: ignore
from runtime_runner_main import execute_runner_session, finalize_runner_exception  # type: ignore
import auto_campaign_reporting as acr  # type: ignore
import auto_campaign_state as acst  # type: ignore
import vuln_qualification as vq  # type: ignore
import auto_campaign_controls as acc  # type: ignore
import evidence_policy as evp  # type: ignore
OPENCLAW = "openclaw"
RUN_PIPE = str(ep("run_pipeline.py"))
OUT_PATH = str(REPORTS_DIR / "auto-campaign-latest.json")
FINDINGS_HISTORY_PATH = REPORTS_DIR / "findings-history.jsonl"
CAMPAIGN_KEY = os.getenv("AUTO_CAMPAIGN_KEY", "").strip()
QUEUE_STATE_PATH = REPORTS_DIR / ".auto_campaign.queues.json"
PLAN_PATH = str(RUNTIME_PLAN_PATH)
RUNTIME_SNAPSHOT_PATH = REPORTS_DIR / ".runtime_snapshot.json"
ARCHIVE_ROOT = REPORTS_DIR / "archive" / "auto"
LOGDASH_VENV_PY = LOGDASH_DIR / ".venv" / "bin" / "python"
LOG_EVENT_SCRIPT = LOGDASH_DIR / "log_event.py"
HOST_STATE_PATH = REPORTS_DIR / ".host_state.json"


def _warn_runner(message: str) -> None:
    print(f"[auto_campaign_runner] {message}", file=sys.stderr)



def _current_campaign_key() -> str:
    return resolve_campaign_key(CAMPAIGN_KEY)



def _selected_scope_path() -> Path:
    return selected_scope_path(load_planner_ui_state_fn=load_planner_ui_state, wp_fn=wp)



def _current_scope_targets() -> list[str]:
    return current_scope_targets(load_scope_domains_fn=load_scope_domains, load_scope_targets_fn=load_scope_targets)



def _current_scope_summary() -> str:
    return current_scope_summary(current_scope_targets_fn=_current_scope_targets, summarize_scope_fn=summarize_scope)



def _load_openclaw_env() -> dict:
    return load_openclaw_env(environ=os.environ, env_path=OPENCLAW_ENV_PATH, warn_fn=_warn_runner)
LOW_SIGNAL_CLASSES = {
    "method_enforced",
    "authz_enforced",
    "not_found_enforced",
    "input_validated",
    "empty_response",
    "healthy_endpoint",
    "failed",
}


PIPELINE_CONFIG_PATH = ep("pipeline_config.json")


def regenerate_runtime_plan_from_blueprint(reason: str = 'auto_runner') -> dict:
    try:
        key = resolve_campaign_key(CAMPAIGN_KEY)
        if not key:
            return {'ok': False, 'error': 'missing_campaign_key'}
        return regenerate_runtime_plan(key, reason=reason)
    except Exception as exc:
        return {'ok': False, 'error': f'regenerate_runtime_plan_failed:{exc}'}


def load_planner_hints() -> dict:
    try:
        resolved_key = resolve_campaign_key(CAMPAIGN_KEY)
        _campaign_key, _version_dir, bp_path, bp = load_active_campaign_blueprint(resolved_key)
        if not bp_path or not isinstance(bp, dict):
            return {}
        hints = bp.get("planner_hints") if isinstance(bp, dict) else {}
        vectors = (hints or {}).get("global_vectors", (hints or {}).get("suggested_attack_vectors", []))
        return {
            "resolved_campaign_key": resolved_key,
            "suggested_attack_vectors": [str(v).strip().lower() for v in vectors if str(v).strip()],
            "recommended_task_families": [str(v).strip().lower() for v in ((hints or {}).get('recommended_task_families', []) or []) if str(v).strip()],
            "llm_confidence": (hints or {}).get("llm_confidence"),
        }
    except (OSError, TypeError, ValueError, AttributeError):
        return {}


def load_host_state() -> dict:
    data, _meta = safe_load_json_object(
        HOST_STATE_PATH,
        {'hosts': {}},
        normalizer=normalize_host_state,
        description='host_state',
    )
    return data


def save_host_state(state: dict) -> None:
    try:
        atomic_write_json(HOST_STATE_PATH, normalize_host_state(state), ensure_ascii=False, indent=2)
    except OSError as exc:
        _warn_runner(f"failed to save host state to {HOST_STATE_PATH}: {exc}")


def planner_vector_weight(task: dict, planner_hints: dict) -> float:
    try:
        vectors = planner_hints.get("suggested_attack_vectors") if isinstance(planner_hints, dict) else []
        families = planner_hints.get("recommended_task_families") if isinstance(planner_hints, dict) else []
        if (not isinstance(vectors, list) or not vectors) and (not isinstance(families, list) or not families):
            return 1.0
        text = f"{str(task.get('objective') or '')} {str(task.get('target') or '')} {str(task.get('task_family') or '')}".lower()
        hits = 0
        for raw in (vectors or [])[:10]:
            token = str(raw or "").strip().lower()
            if not token:
                continue
            parts = [p for p in re.split(r"[^a-z0-9]+", token) if p]
            if token in text or (parts and all(p in text for p in parts[:3])):
                hits += 1
        fam_hits = 0
        for raw in (families or [])[:8]:
            token = str(raw or '').strip().lower()
            if token and token in text:
                fam_hits += 1
        boost = 1.0 + (0.12 * hits) + (0.18 * fam_hits)
        return min(1.65, boost)
    except (AttributeError, TypeError, ValueError):
        return 1.0

def repeated_consistency_ok(runs: list[dict], target: str, objective: str) -> bool:
    t = str(target or "").strip().lower()
    o = str(objective or "").strip().lower()
    seen = 0
    for r in reversed(runs[-10:]):
        if not isinstance(r, dict):
            continue
        if str(r.get("target") or "").strip().lower() != t:
            continue
        if str(r.get("objective") or "").strip().lower() != o:
            continue
        cls = str(r.get("classification") or "").lower()
        if cls not in {"failed", "blocked", "unknown", "none"}:
            seen += 1
        if seen >= 2:
            return True
    return False


PROMISING_KEYWORDS = (
    "xss",
    "idor",
    "sqli",
    "sql injection",
    "csrf",
    "ssrf",
    "rce",
    "lfi",
    "shell",
    "credential",
    "token",
    "leak",
    "expos",
    "vuln",
    "finding",
    "override",
    "bypass",
    "interesting",
    "potential",
)


def is_strong_security_signal(classification: str | None, reason_code: str | None, summary: str | None = None) -> bool:
    cls = (classification or '').lower()
    rc = (reason_code or '').lower()
    s = (summary or '').lower()
    if cls in {'high', 'critical'}:
        return True
    security_reason_tokens = (
        'idor', 'bola', 'xss', 'sqli', 'ssrf', 'rce', 'csrf', 'bypass', 'authz', 'auth', 'token_leak', 'exposure',
    )
    if any(tok in rc for tok in security_reason_tokens):
        return True
    return any(tok in s for tok in security_reason_tokens)


def log_event(
    tor: str,
    decision: str,
    status: str,
    result: str,
    actor: str | None = None,
    row_type: str = "entry",
    highlight: bool = False,
) -> None:
    if not (LOG_EVENT_SCRIPT.exists() and LOGDASH_VENV_PY.exists()):
        return
    try:
        cmd = [
            str(LOGDASH_VENV_PY),
            str(LOG_EVENT_SCRIPT),
            "--tor",
            tor,
            "--decision",
            decision,
            "--status",
            status,
            "--result",
            result,
            "--row-type",
            row_type,
        ]
        if actor:
            cmd.extend(["--agent", actor])
        if highlight:
            cmd.append("--highlight")
        subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[logdash] failed to record event: {exc}")
def is_promising(summary: str | None, classification: str | None = None) -> bool:
    summary_text = (summary or "").lower()
    cls = (classification or "").lower()
    if cls and cls not in LOW_SIGNAL_CLASSES:
        return True

    # Suppress generic transport/operational noise from triggering follow-ups.
    low_signal_phrases = (
        'request completed and response was saved',
        'could not resolve host',
        'tls/ssl connect error',
        'engine ended with status',
        '__rc_metrics__',
        'no output',
        'dns_unresolvable',
    )
    if any(p in summary_text for p in low_signal_phrases):
        return False

    return any(keyword in summary_text for keyword in PROMISING_KEYWORDS)
def log_operation(
    tor: str,
    name: str,
    phase: str,
    *,
    actor: str | None = None,
    note: str | None = None,
    success: bool | None = None,
) -> None:
    phase_clean = phase.upper()
    message = f"OPERATION: {name} {phase_clean}"
    if note:
        message += f" — {note}"
    status = "in_progress"
    if phase.lower() == "end":
        if success is None:
            success = True
        status = "success" if success else "failed"
    log_event(tor, f"operation::{name}", status, message, actor=actor, row_type="operation")
def run_agent(agent: str, message: str, timeout: int = 180) -> str:
    session_id = str(uuid.uuid4())
    proc = subprocess.run(
        [OPENCLAW, "agent", "--agent", agent, "--session-id", session_id, "--message", message, "--json"],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_load_openclaw_env(),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{agent} failed: {proc.stderr or proc.stdout}")
    data = json.loads(proc.stdout)
    payloads = data.get("result", {}).get("payloads", [])
    if not payloads:
        raise RuntimeError(f"{agent} returned no payload")
    return (payloads[0].get("text") or "").strip()
def parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise
def propose_next_vector(history: list[dict]) -> tuple[str, str]:
    learning = summarize_learning(limit=5)
    prompt = (
        "You are BRAIN. Choose the next best low-risk vector for the currently selected in-scope campaign. "
        "Stay policy compliant (no auth brute force, no privacy violations). "
        "Return JSON only: {{\"objective\":\"...\",\"target\":\"https://...\"}}. "
        f"Allowed scope summary: {_current_scope_summary()}. "
        f"Recent history: {json.dumps(history[-10:], ensure_ascii=False)}. "
        f"Learning summary: {json.dumps(learning, ensure_ascii=False)}"
    )
    raw = run_agent("brain", prompt)
    data = parse_json(raw)
    return data["objective"], data["target"]
def _extend_run_pipeline_contract_args(
    cmd: list[str],
    *,
    success_criteria: str = "",
    campaign_success_criteria: str = "",
    task_family: str = "",
    acceptance_checks: str = "",
    evidence_required: str = "",
    success_semantics_json: str = "",
    experiment_intent_id: str = "",
    capability_candidates_json: str = "",
    recommended_action_types_json: str = "",
    hypothesis_candidates_json: str = "",
    planner_constraints_json: str = "",
    planner_preferences_json: str = "",
    open_questions_json: str = "",
    planner_rationale_json: str = "",
    planning_ladder_json: str = "",
    target_surface_rationale_json: str = "",
    recommended_progression_json: str = "",
    semantic_lineage_json: str = "",
    semantic_lineage_summary_json: str = "",
) -> list[str]:
    option_pairs = [
        ("--task-success-criteria", success_criteria),
        ("--campaign-success-criteria", campaign_success_criteria),
        ("--task-family", task_family),
        ("--acceptance-checks", acceptance_checks),
        ("--evidence-required", evidence_required),
        ("--success-semantics-json", success_semantics_json),
        ("--experiment-intent-id", experiment_intent_id),
        ("--capability-candidates-json", capability_candidates_json),
        ("--recommended-action-types-json", recommended_action_types_json),
        ("--hypothesis-candidates-json", hypothesis_candidates_json),
        ("--planner-constraints-json", planner_constraints_json),
        ("--planner-preferences-json", planner_preferences_json),
        ("--open-questions-json", open_questions_json),
        ("--planner-rationale-json", planner_rationale_json),
        ("--planning-ladder-json", planning_ladder_json),
        ("--target-surface-rationale-json", target_surface_rationale_json),
        ("--recommended-progression-json", recommended_progression_json),
        ("--semantic-lineage-json", semantic_lineage_json),
        ("--semantic-lineage-summary-json", semantic_lineage_summary_json),
    ]
    for flag, value in option_pairs:
        if value:
            cmd.extend([flag, str(value)])
    return cmd


def _extend_run_pipeline_owner_flags(cmd: list[str], *, owner_auth: bool = False, owner_override: bool = False) -> list[str]:
    if owner_auth:
        cmd.append("--owner-approved-auth")
    if owner_override:
        cmd.append("--owner-override")
    return cmd


@dataclass
class RunPipelineRequest:
    objective: str
    target: str
    aggression: int
    owner_auth: bool
    owner_override: bool
    success_criteria: str
    campaign_success_criteria: str
    task_family: str
    acceptance_checks: str
    evidence_required: str
    success_semantics_json: str
    experiment_intent_id: str
    capability_candidates_json: str
    recommended_action_types_json: str
    hypothesis_candidates_json: str
    planner_constraints_json: str
    planner_preferences_json: str
    open_questions_json: str
    planner_rationale_json: str
    planning_ladder_json: str
    target_surface_rationale_json: str
    recommended_progression_json: str
    semantic_lineage_json: str
    semantic_lineage_summary_json: str



def _build_run_pipeline_request(
    objective: str,
    target: str,
    *,
    aggression: int = 6,
    owner_auth: bool = False,
    owner_override: bool = False,
    success_criteria: str = "",
    campaign_success_criteria: str = "",
    task_family: str = "",
    acceptance_checks: str = "",
    evidence_required: str = "",
    success_semantics_json: str = "",
    experiment_intent_id: str = "",
    capability_candidates_json: str = "",
    recommended_action_types_json: str = "",
    hypothesis_candidates_json: str = "",
    planner_constraints_json: str = "",
    planner_preferences_json: str = "",
    open_questions_json: str = "",
    planner_rationale_json: str = "",
    planning_ladder_json: str = "",
    target_surface_rationale_json: str = "",
    recommended_progression_json: str = "",
    semantic_lineage_json: str = "",
    semantic_lineage_summary_json: str = "",
) -> RunPipelineRequest:
    return RunPipelineRequest(
        objective=str(objective),
        target=str(target),
        aggression=int(aggression),
        owner_auth=bool(owner_auth),
        owner_override=bool(owner_override),
        success_criteria=str(success_criteria),
        campaign_success_criteria=str(campaign_success_criteria),
        task_family=str(task_family),
        acceptance_checks=str(acceptance_checks),
        evidence_required=str(evidence_required),
        success_semantics_json=str(success_semantics_json),
        experiment_intent_id=str(experiment_intent_id),
        capability_candidates_json=str(capability_candidates_json),
        recommended_action_types_json=str(recommended_action_types_json),
        hypothesis_candidates_json=str(hypothesis_candidates_json),
        planner_constraints_json=str(planner_constraints_json),
        planner_preferences_json=str(planner_preferences_json),
        open_questions_json=str(open_questions_json),
        planner_rationale_json=str(planner_rationale_json),
        planning_ladder_json=str(planning_ladder_json),
        target_surface_rationale_json=str(target_surface_rationale_json),
        recommended_progression_json=str(recommended_progression_json),
        semantic_lineage_json=str(semantic_lineage_json),
        semantic_lineage_summary_json=str(semantic_lineage_summary_json),
    )



def _build_run_pipeline_command(
    objective: str,
    target: str,
    *,
    aggression: int = 6,
    owner_auth: bool = False,
    owner_override: bool = False,
    success_criteria: str = "",
    campaign_success_criteria: str = "",
    task_family: str = "",
    acceptance_checks: str = "",
    evidence_required: str = "",
    success_semantics_json: str = "",
    experiment_intent_id: str = "",
    capability_candidates_json: str = "",
    recommended_action_types_json: str = "",
    hypothesis_candidates_json: str = "",
    planner_constraints_json: str = "",
    planner_preferences_json: str = "",
    open_questions_json: str = "",
    planner_rationale_json: str = "",
    planning_ladder_json: str = "",
    target_surface_rationale_json: str = "",
    recommended_progression_json: str = "",
    semantic_lineage_json: str = "",
    semantic_lineage_summary_json: str = "",
) -> list[str]:
    cmd = [
        "python3",
        RUN_PIPE,
        "--objective",
        objective,
        "--target",
        target,
        "--aggression",
        str(aggression),
    ]
    _extend_run_pipeline_contract_args(
        cmd,
        success_criteria=success_criteria,
        campaign_success_criteria=campaign_success_criteria,
        task_family=task_family,
        acceptance_checks=acceptance_checks,
        evidence_required=evidence_required,
        success_semantics_json=success_semantics_json,
        experiment_intent_id=experiment_intent_id,
        capability_candidates_json=capability_candidates_json,
        recommended_action_types_json=recommended_action_types_json,
        hypothesis_candidates_json=hypothesis_candidates_json,
        planner_constraints_json=planner_constraints_json,
        planner_preferences_json=planner_preferences_json,
        open_questions_json=open_questions_json,
        planner_rationale_json=planner_rationale_json,
        planning_ladder_json=planning_ladder_json,
        target_surface_rationale_json=target_surface_rationale_json,
        recommended_progression_json=recommended_progression_json,
        semantic_lineage_json=semantic_lineage_json,
        semantic_lineage_summary_json=semantic_lineage_summary_json,
    )
    return _extend_run_pipeline_owner_flags(cmd, owner_auth=owner_auth, owner_override=owner_override)


def _execute_run_pipeline_command(cmd: list[str], *, timeout: int = 420) -> dict:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return {"error": f"run_pipeline_timeout:{exc}"}
    except Exception as exc:
        return {"error": f"run_pipeline_exec_failed:{exc}"}
    return {"proc": proc}


def _decode_run_pipeline_result(exec_result: dict) -> dict:
    if not isinstance(exec_result, dict):
        return {"error": "run_pipeline_exec_result_invalid"}
    if exec_result.get("error"):
        return dict(exec_result)
    proc = exec_result.get("proc")
    if proc is None:
        return {"error": "run_pipeline_missing_proc"}
    if getattr(proc, 'returncode', 1) != 0:
        return {"error": getattr(proc, 'stderr', '') or getattr(proc, 'stdout', '')}
    try:
        return json.loads(getattr(proc, 'stdout', ''))
    except (json.JSONDecodeError, TypeError):
        return {"error": "invalid_pipeline_output", "raw": str(getattr(proc, 'stdout', '') or '')[:2000]}



def _run_pipeline_command_flow(cmd: list[str], *, timeout: int = 420) -> dict:
    exec_result = _execute_run_pipeline_command(cmd, timeout=timeout)
    return _decode_run_pipeline_result(exec_result)



def _run_pipeline_request(request: dict | RunPipelineRequest, *, timeout: int = 420) -> dict:
    req = vars(request) if isinstance(request, RunPipelineRequest) else dict(request)
    cmd = _build_run_pipeline_command(
        req['objective'],
        req['target'],
        aggression=int(req.get('aggression', 6) or 6),
        owner_auth=bool(req.get('owner_auth', False)),
        owner_override=bool(req.get('owner_override', False)),
        success_criteria=str(req.get('success_criteria') or ''),
        campaign_success_criteria=str(req.get('campaign_success_criteria') or ''),
        task_family=str(req.get('task_family') or ''),
        acceptance_checks=str(req.get('acceptance_checks') or ''),
        evidence_required=str(req.get('evidence_required') or ''),
        success_semantics_json=str(req.get('success_semantics_json') or ''),
        experiment_intent_id=str(req.get('experiment_intent_id') or ''),
        capability_candidates_json=str(req.get('capability_candidates_json') or ''),
        recommended_action_types_json=str(req.get('recommended_action_types_json') or ''),
        hypothesis_candidates_json=str(req.get('hypothesis_candidates_json') or ''),
        planner_constraints_json=str(req.get('planner_constraints_json') or ''),
        planner_preferences_json=str(req.get('planner_preferences_json') or ''),
        open_questions_json=str(req.get('open_questions_json') or ''),
        planner_rationale_json=str(req.get('planner_rationale_json') or ''),
        planning_ladder_json=str(req.get('planning_ladder_json') or ''),
        target_surface_rationale_json=str(req.get('target_surface_rationale_json') or ''),
        recommended_progression_json=str(req.get('recommended_progression_json') or ''),
        semantic_lineage_json=str(req.get('semantic_lineage_json') or ''),
        semantic_lineage_summary_json=str(req.get('semantic_lineage_summary_json') or ''),
    )
    return _run_pipeline_command_flow(cmd, timeout=timeout)



def run_pipeline(
    objective: str,
    target: str,
    *,
    aggression: int = 6,
    owner_auth: bool = False,
    owner_override: bool = False,
    success_criteria: str = "",
    campaign_success_criteria: str = "",
    task_family: str = "",
    acceptance_checks: str = "",
    evidence_required: str = "",
    success_semantics_json: str = "",
    experiment_intent_id: str = "",
    capability_candidates_json: str = "",
    recommended_action_types_json: str = "",
    hypothesis_candidates_json: str = "",
    planner_constraints_json: str = "",
    planner_preferences_json: str = "",
    open_questions_json: str = "",
    planner_rationale_json: str = "",
    planning_ladder_json: str = "",
    target_surface_rationale_json: str = "",
    recommended_progression_json: str = "",
    semantic_lineage_json: str = "",
    semantic_lineage_summary_json: str = "",
    **_ignored_runtime_metadata: Any,
) -> dict:
    request = _build_run_pipeline_request(
        objective,
        target,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        success_criteria=success_criteria,
        campaign_success_criteria=campaign_success_criteria,
        task_family=task_family,
        acceptance_checks=acceptance_checks,
        evidence_required=evidence_required,
        success_semantics_json=success_semantics_json,
        experiment_intent_id=experiment_intent_id,
        capability_candidates_json=capability_candidates_json,
        recommended_action_types_json=recommended_action_types_json,
        hypothesis_candidates_json=hypothesis_candidates_json,
        planner_constraints_json=planner_constraints_json,
        planner_preferences_json=planner_preferences_json,
        open_questions_json=open_questions_json,
        planner_rationale_json=planner_rationale_json,
        planning_ladder_json=planning_ladder_json,
        target_surface_rationale_json=target_surface_rationale_json,
        recommended_progression_json=recommended_progression_json,
        semantic_lineage_json=semantic_lineage_json,
        semantic_lineage_summary_json=semantic_lineage_summary_json,
    )
    return _run_pipeline_request(request, timeout=420)
def classify(result: dict) -> str:
    engine = result.get("engine") or {}
    stdout = (engine.get("stdout") or "").lower()
    if "method not allowed" in stdout:
        return "method_enforced"
    if "forbidden" in stdout or "unauthorized" in stdout:
        return "authz_enforced"
    if "not found" in stdout:
        return "not_found_enforced"
    if "invalid" in stdout and "parameter" in stdout:
        return "input_validated"
    if "results" in stdout and "[]" in stdout:
        return "empty_response"
    if "health" in stdout and "ok" in stdout:
        return "healthy_endpoint"
    return "unknown"
def read_runtime_owner_override(default: bool = False) -> bool:
    try:
        return runtime_owner_override(default=default)
    except (OSError, ValueError, TypeError):
        return default


def read_runtime_aggression_override() -> int | None:
    try:
        return runtime_aggression_override(resolve_campaign_key(CAMPAIGN_KEY))
    except (OSError, ValueError, TypeError):
        return None


def read_runtime_control_state() -> dict:
    try:
        state = load_runtime_campaign_state()
        return state if isinstance(state, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def load_queue_state() -> dict:
    if os.getenv("AUTO_RESUME", "0") == "0":
        return {}
    try:
        if QUEUE_STATE_PATH.exists():
            d = json.loads(QUEUE_STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, json.JSONDecodeError) as exc:
        _warn_runner(f"failed to load queue state from {QUEUE_STATE_PATH}: {exc}")
    return {}


def save_queue_state(state: dict) -> None:
    try:
        QUEUE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        QUEUE_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        _warn_runner(f"failed to save queue state to {QUEUE_STATE_PATH}: {exc}")


def load_existing_runs() -> list[dict]:
    if os.getenv("AUTO_RESUME", "0") == "0":
        return []
    if not os.path.exists(OUT_PATH):
        return []
    try:
        with open(OUT_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        runs = data.get("runs", [])
        if isinstance(runs, list):
            return runs
    except (OSError, json.JSONDecodeError) as exc:
        _warn_runner(f"failed to load existing runs from {OUT_PATH}: {exc}")
    return []


def load_curated_plan() -> list[dict]:
    if not os.path.exists(PLAN_PATH):
        return []
    try:
        with open(PLAN_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            return []
        filtered: list[dict] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            if not entry.get("objective") or not entry.get("target"):
                continue
            filtered.append(entry)
        return filtered
    except (OSError, json.JSONDecodeError) as exc:
        _warn_runner(f"failed to load curated plan from {PLAN_PATH}: {exc}")
        return []
def host_from_target(target: str) -> str:
    target_text = str(target or "")
    host = urlparse(target_text).netloc
    return host or target_text




def is_resolvable_host(host: str) -> bool:
    h = str(host or '').strip().lower()
    if not h:
        return False
    try:
        socket.getaddrinfo(h, None)
        return True
    except OSError:
        return False
def attack_family(objective: str, target: str, task_family: str = '') -> str:
    tf = str(task_family or '').strip().lower()
    if tf:
        return tf
    text = f"{objective} {target}".lower()
    families = [
        ('subdomain_expansion', ['subdomain','asset enumeration','dnsgen','assetfinder','subfinder']),
        ('historical_url_mining', ['historical','legacy endpoint','gau','wayback']),
        ('content_discovery', ['content discovery','path surface','ferox','ffuf','gobuster']),
        ('tls_assessment', ['tls','certificate','https posture','testssl']),
        ('secret_hunt', ['secret exposure','secret hunt']),
        ('xss', ['xss','script','onerror','onload']),
        ('idor', ['idor','authorization','object id','insecure direct object']),
        ('sqli', ['sqli','sql injection','sqlmap']),
        ('csrf', ['csrf']),
        ('ssrf', ['ssrf']),
        ('recon', ['recon','robots','sitemap','fingerprint']),
    ]
    for fam, keys in families:
        if any(k in text for k in keys):
            return fam
    return 'generic'


def _merge_runtime_task_contract_metadata(out: dict, runtime_task: dict) -> dict:
    return merge_runtime_task_contract_metadata_helper(out, runtime_task)



def _build_normalized_runtime_task_core(task: dict, runtime_task: dict) -> dict:
    return build_normalized_runtime_task_core_helper(task, runtime_task)



def _ensure_runtime_task_view(out: dict, runtime_task: dict) -> dict:
    return ensure_runtime_task_view_helper(out, runtime_task)



def normalize_runtime_task(task: dict) -> dict:
    return normalize_runtime_task_helper(task)


def next_followup_family(current_family: str, result: dict | None = None) -> str:
    return resolve_next_followup_family(current_family, result, host_from_target_fn=host_from_target)



def _build_main_runtime_controls(toggles: dict) -> MainRuntimeControls:
    return build_main_runtime_controls(toggles)



def is_sensitive_host(target: str) -> bool:
    h = host_from_target(str(target or '')).lower()
    return any(k in h for k in ['auth.', 'login', 'signin', 'oauth', 'sso', 'webhook', 'hook', 'callback', 'partner'])


def host_warmup_complete(host_state: dict, target: str) -> bool:
    h = host_from_target(str(target or ''))
    hs = ((host_state or {}).get('hosts') or {}).get(h, {}) if isinstance((host_state or {}).get('hosts'), dict) else {}
    if not isinstance(hs, dict):
        return False
    last_success = str(hs.get('last_success_family') or '')
    if last_success in {'tls_assessment', 'recon', 'historical_url_mining'}:
        return True
    return float(hs.get('promise_score', 1.0) or 1.0) >= 1.12 and float(hs.get('evidence_density', 0.5) or 0.5) >= 0.55


def capped_aggression(task_family: str, target: str, requested: int) -> int:
    fam = str(task_family or '').strip().lower()
    host = host_from_target(str(target or ''))
    family_cap = {
        'recon': 3,
        'subdomain_expansion': 3,
        'historical_url_mining': 3,
        'tls_assessment': 3,
        'content_discovery': 4,
        'client_input': 4,
        'input_tamper': 4,
        'redirect_trust': 4,
        'secret_hunt': 3,
        'auth_flow': 5,
        'authz': 5,
        'logic': 5,
    }.get(fam, 5)
    host_cap = 6
    h = str(host or '').lower()
    if any(k in h for k in ['auth.', 'login', 'signin', 'oauth', 'sso']):
        host_cap = 5
    if any(k in h for k in ['webhook', 'hook', 'callback', 'partner']):
        host_cap = 4
    if any(k in h for k in ['sandbox', '.dev.', '.int.']):
        host_cap = min(6, host_cap + 1)
    return max(1, min(int(requested or 1), int(family_cap), int(host_cap)))


@dataclass
class PostRunActionInputs:
    task: dict
    result: dict
    qual: dict
    classification: str
    auditor: str
    engine_status: str
    success_eval_status: str
    summary_text: str
    reason_code: str
    target: str
    objective: str
    aggression: int
    owner_auth: bool
    owner_override: bool
    retry_counts: dict
    retry_limit: int
    followup_queue: list
    followup_counts: dict
    followup_recent: dict
    max_followups_per_target: int
    scheduled_keys: set
    host_weak_count: dict
    host_family_owner_gate: dict
    confirm_counts: dict
    confirm_recent: dict
    confirm_total: int
    confirm_class_counts: dict
    max_confirm_jobs_per_target: int
    max_confirm_jobs_total: int
    max_confirm_jobs_per_class: int
    confirm_job_cooldown_sec: int
    quality_telemetry: dict
    toggles: dict
    promising: bool
    signal_contract: dict
    runtime_decision: dict | None
    dedup_key_fn: Callable[[str, str], tuple[str, str, str]]
    attack_family_fn: Callable[[str, str, str], str]
    host_from_target_fn: Callable[[str], str]
    next_followup_family_fn: Callable[[str, dict | None], str]
    clamp_aggression_fn: Callable[[int], int]
    capped_aggression_fn: Callable[[str, str, int], int]
    adaptive_aggression_fn: Callable[..., int]
    enqueue_followup_task_fn: Callable[[dict, bool], None]
    post_run_decision_fn: Callable[..., dict[str, bool]]
    log_event_fn: Callable[..., None]



def _build_post_run_action_inputs(*, task: dict, result: dict, qual: dict, classification: str, auditor: str, engine_status: str, success_eval_status: str, summary_text: str, reason_code: str, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, retry_counts: dict, retry_limit: int, followup_queue: list, followup_counts: dict, followup_recent: dict, max_followups_per_target: int, scheduled_keys: set, host_weak_count: dict, host_family_owner_gate: dict, confirm_counts: dict, confirm_recent: dict, confirm_total: int, confirm_class_counts: dict, max_confirm_jobs_per_target: int, max_confirm_jobs_total: int, max_confirm_jobs_per_class: int, confirm_job_cooldown_sec: int, quality_telemetry: dict, toggles: dict, promising: bool, signal_contract: dict | None = None, runtime_decision: dict | None = None, enqueue_followup_task_fn: Callable[[dict, bool], None] | None = None) -> PostRunActionInputs:
    return build_post_run_action_inputs(
        post_run_action_inputs_cls=PostRunActionInputs,
        task=task,
        result=result,
        qual=qual,
        classification=classification,
        auditor=auditor,
        engine_status=engine_status,
        success_eval_status=success_eval_status,
        summary_text=summary_text,
        reason_code=reason_code,
        target=target,
        objective=objective,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        mode=mode,
        retry_counts=retry_counts,
        retry_limit=retry_limit,
        followup_queue=followup_queue,
        followup_counts=followup_counts,
        followup_recent=followup_recent,
        max_followups_per_target=max_followups_per_target,
        scheduled_keys=scheduled_keys,
        host_weak_count=host_weak_count,
        host_family_owner_gate=host_family_owner_gate,
        confirm_counts=confirm_counts,
        confirm_recent=confirm_recent,
        confirm_total=confirm_total,
        confirm_class_counts=confirm_class_counts,
        max_confirm_jobs_per_target=max_confirm_jobs_per_target,
        max_confirm_jobs_total=max_confirm_jobs_total,
        max_confirm_jobs_per_class=max_confirm_jobs_per_class,
        confirm_job_cooldown_sec=confirm_job_cooldown_sec,
        quality_telemetry=quality_telemetry,
        toggles=toggles,
        promising=promising,
        signal_contract=signal_contract,
        runtime_decision=runtime_decision,
        enqueue_followup_task_fn=enqueue_followup_task_fn,
        dedup_key_fn=dedup_key,
        attack_family_fn=attack_family,
        host_from_target_fn=host_from_target,
        next_followup_family_fn=next_followup_family,
        clamp_aggression_fn=clamp_aggression,
        capped_aggression_fn=capped_aggression,
        adaptive_aggression_fn=adaptive_aggression,
        post_run_decision_fn=post_run_decision,
        log_event_fn=log_event,
    )



def _quality_aware_followup_admission_hint(task: dict, result: dict | None, runtime_decision: dict | None) -> dict:
    return resolve_quality_aware_followup_admission_hint(
        task,
        result,
        runtime_decision,
        adaptive_quality_context_fn=adaptive_quality_context,
    )


def handle_post_run_actions(*, task: dict, result: dict, qual: dict, classification: str, auditor: str, engine_status: str, success_eval_status: str, summary_text: str, reason_code: str, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, retry_counts: dict, retry_limit: int, followup_queue: list, followup_counts: dict, followup_recent: dict, max_followups_per_target: int, scheduled_keys: set, host_weak_count: dict, host_family_owner_gate: dict, confirm_counts: dict, confirm_recent: dict, confirm_total: int, confirm_class_counts: dict, max_confirm_jobs_per_target: int, max_confirm_jobs_total: int, max_confirm_jobs_per_class: int, confirm_job_cooldown_sec: int, quality_telemetry: dict, toggles: dict, promising: bool, signal_contract: dict | None = None, runtime_decision: dict | None = None, enqueue_followup_task_fn: Callable[[dict, bool], None] | None = None) -> tuple[int, dict]:
    return resolve_run_post_run_actions(
        task=task,
        result=result,
        qual=qual,
        classification=classification,
        auditor=auditor,
        engine_status=engine_status,
        success_eval_status=success_eval_status,
        summary_text=summary_text,
        reason_code=reason_code,
        target=target,
        objective=objective,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        mode=mode,
        retry_counts=retry_counts,
        retry_limit=retry_limit,
        followup_queue=followup_queue,
        followup_counts=followup_counts,
        followup_recent=followup_recent,
        max_followups_per_target=max_followups_per_target,
        scheduled_keys=scheduled_keys,
        host_weak_count=host_weak_count,
        host_family_owner_gate=host_family_owner_gate,
        confirm_counts=confirm_counts,
        confirm_recent=confirm_recent,
        confirm_total=confirm_total,
        confirm_class_counts=confirm_class_counts,
        max_confirm_jobs_per_target=max_confirm_jobs_per_target,
        max_confirm_jobs_total=max_confirm_jobs_total,
        max_confirm_jobs_per_class=max_confirm_jobs_per_class,
        confirm_job_cooldown_sec=confirm_job_cooldown_sec,
        quality_telemetry=quality_telemetry,
        toggles=toggles,
        promising=promising,
        signal_contract=signal_contract,
        runtime_decision=runtime_decision,
        enqueue_followup_task_fn=enqueue_followup_task_fn,
        quality_aware_followup_admission_hint_fn=_quality_aware_followup_admission_hint,
        apply_post_run_admission_hint_fn=resolve_apply_post_run_admission_hint,
        build_post_run_action_inputs_fn=_build_post_run_action_inputs,
        apply_effective_decision_fn=apply_effective_decision,
    )


def payload_signature(target: str) -> str:
    parsed = urlparse(str(target or ''))
    q = parse_qsl(parsed.query, keep_blank_values=True)
    if not q:
        return 'nopayload'
    q_sorted = '&'.join(f"{k}={v}" for k,v in sorted(q))
    return hashlib.sha1(q_sorted.encode('utf-8')).hexdigest()[:12]


def dedup_key(objective: str, target: str) -> tuple[str, str, str]:
    host = host_from_target(target).strip().lower()
    family = attack_family(objective, target)
    sig = payload_signature(target)
    return (host, family, sig)
def render_host_summary(runs: list[dict]) -> str:
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
    lines = [
        "# Auto Campaign Host Summary",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    for host, host_runs in groups.items():
        lines.append(f"## {host}")
        lines.append(f"- Runs: {len(host_runs)}")
        latest = host_runs[-1]
        cls = latest.get("classification")
        lines.append(f"- Latest classification: {cls} ({classify_note(cls)})")
        lines.append(
            f"- Engine status: {latest.get('engine_status')} | Mode: {latest.get('mode', 'fast')}"
        )
        lines.append("- Objectives:")
        for run in host_runs:
            lines.append(
                f"  - [{run.get('mode', 'fast')}] {run.get('objective', 'n/a')} → {run.get('engine_status')} ({run.get('classification')})"
            )
        lines.append("")
    return "\n".join(lines)
def write_host_summary(
    runs: list[dict], path: str = str(REPORTS_DIR / "auto-campaign-summary.md")
) -> str:
    text = render_host_summary(runs)
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
        lines = [
            f"# Run {idx}: {name}",
            "",
            f"- Objective: {run.get('objective')}",
            f"- Target: {run.get('target')}",
            f"- Mode: {run.get('mode')}",
            f"- Aggression: {run.get('aggression')}",
            f"- Owner override: {run.get('owner_override')}",
            f"- Auditor decision: {run.get('auditor_decision')}",
            f"- Engine status: {run.get('engine_status')} | Classification: {run.get('classification')}",
            "",
            "## Stdout preview",
            "```",
            run.get("engine_stdout_preview") or "",
            "```",
        ]
        filename.write_text("\n".join(lines), encoding="utf-8")
def record_run(runs: list[dict], info: dict) -> None:
    runs.append(info)
    try:
        rec = dict(info or {})
        rec["campaign_key"] = _current_campaign_key()
        rec["recorded_at"] = datetime.now(timezone.utc).isoformat()
        FINDINGS_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with FINDINGS_HISTORY_PATH.open("a", encoding="utf-8") as h:
            h.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except (OSError, TypeError, ValueError) as exc:
        _warn_runner(f"failed to append findings history to {FINDINGS_HISTORY_PATH}: {exc}")


def parse_rc_metrics(text: str) -> dict:
    out = {}
    if not text:
        return out
    m = SIGNAL_REGEX["metrics"].findall(text)
    if not m:
        return out
    seg = m[-1]
    for tok in seg.split():
        if '=' not in tok:
            continue
        k, v = tok.split('=', 1)
        out[k.strip()] = v.strip()
    return out


def _load_output_sample_from_command(planned_cmd: object) -> str:
    cmd = ' '.join(str(x) for x in planned_cmd) if isinstance(planned_cmd, list) else str(planned_cmd or '')
    m = re.search(r"(?:^|\s)-o\s+([^\s]+)", cmd)
    if not m:
        return ''
    raw = m.group(1).strip().strip("'\"")
    pth = Path(raw)
    try:
        if not pth.exists() or pth.stat().st_size <= 0 or pth.stat().st_size > 300000:
            return ''
        return pth.read_text(encoding='utf-8', errors='ignore')[:12000]
    except OSError:
        return ''



def _append_json_signal_observations(sample: str, out: dict) -> None:
    low = sample.lower()
    if any(k in low for k in ['traceback', 'exception', 'stack trace', 'sql syntax', 'whitelabel error', 'nullreference']):
        out['findings'].append({'code':'error_trace_signal','severity':'mid','message':'Error/stack fingerprint exposed in response body'})
    if SIGNAL_REGEX["jwt"].search(sample) or SIGNAL_REGEX["akia"].search(sample) or 'begin private key' in low:
        out['findings'].append({'code':'secret_leak_signal','severity':'high','message':'Potential credential/token material observed in response body'})
    if any(k in low for k in ['owner_id','account_id','user_id','tenant_id','permissions','role']):
        out['findings'].append({'code':'authz_boundary_signal','severity':'mid','message':'Object/ownership fields suggest possible authz boundary weakness'})
    if any(k in low for k in ['idempotency', 'duplicate', 'replay', 'state transition', 'settlement', 'insufficient funds']):
        out['findings'].append({'code':'business_logic_signal','severity':'mid','message':'Business-logic/idempotency/state anomaly indicators present'})
    if any(k in low for k in ['cloudflare', 'akamai', 'captcha', 'bot detection', 'access denied']):
        out['info'].append({'code':'waf_fingerprint_signal','message':'WAF/CDN protection fingerprint detected'})
    if any(k in low for k in ['redirect_uri', 'return_to', 'next=']) and ('http://' in low or 'https://' in low):
        out['info'].append({'code':'redirect_handling_signal','message':'Redirect parameter reflection/handling pattern observed'})
    looks_json = sample.lstrip().startswith('{') or sample.lstrip().startswith('[')
    looks_html = '<html' in low or '<body' in low
    if looks_json and 'content-type: text/html' in low:
        out['info'].append({'code':'content_type_mismatch_signal','message':'JSON-like body with HTML content-type hint'})
    if looks_html and 'application/json' in low:
        out['info'].append({'code':'content_type_mismatch_signal','message':'HTML-like body with JSON content-type hint'})
    if any(k in low for k in ['set-cookie', 'x-powered-by', 'access-control-allow-origin', 'x-envoy', 'via:']):
        out['info'].append({'code':'header_exposure_signal','message':'Interesting header/security-policy tokens present in response text'})
    if any(k in low for k in ['fmt=json', 'role=admin', 'amount=2', 'idempotency_key']):
        out['info'].append({'code':'diff_probe_marker','message':'Response captured for differential tampering probe'})
    if any(k in low for k in ['/swagger', 'openapi', 'actuator', '.well-known', 'debug']):
        out['findings'].append({'code':'exposed_debug_surface_signal','severity':'low','message':'Potential debug/discovery surface exposure in response'})
    if sample.strip().startswith('{') or sample.strip().startswith('['):
        key_hits = [k for k in ['error','errors','message','stack','trace','debug','token','secret','internal','exception','id'] if f'"{k}"' in low]
        if key_hits:
            out['signal'] = True
            out['severity'] = 'mid' if any(k in key_hits for k in ['stack','trace','debug','token','secret','exception']) else 'low'
            out['keys'] = key_hits[:6]
            out['note'] = f"JSON response contains interesting keys: {', '.join(out['keys'])}"



def inspect_json_signal_from_command(planned_cmd: object) -> dict:
    out = {'signal': False, 'severity': 'low', 'note': '', 'keys': [], 'info': [], 'findings': []}
    sample = _load_output_sample_from_command(planned_cmd)
    stripped = sample.strip()
    if len(stripped) <= 8 and stripped in {'', '{}', '[]', 'null', 'ok'}:
        return out
    _append_json_signal_observations(sample, out)
    if out['findings']:
        out['signal'] = True
        out['severity'] = out['findings'][0].get('severity', out['severity'])
        out['note'] = out['findings'][0].get('message', out['note'])
    out['info'] = out['info'][:8]
    out['findings'] = out['findings'][:8]
    return out



def summarize_result(result: dict) -> tuple[str, str, str, str, bool]:
    return resolve_runner_result_summary(
        result,
        classify_fn=classify,
        parse_rc_metrics_fn=parse_rc_metrics,
    )


@dataclass
class RuntimeSessionBootstrap:
    runs: list[dict]
    history: list[dict]
    host_state: dict
    executed_keys: set
    run_started: datetime
    max_runs: int
    target_load_limit: int
    time_budget_min: int
    retry_policy: str
    retry_limit: int
    curated_plan: list[dict]
    runtime_plan_meta: dict
    host_dns_cache: dict[str, bool]
    toggles: dict
    planner_hints_cache: dict
    followup_queue: list[dict]
    precision_queue: list[dict]



def _load_runtime_session_bootstrap() -> RuntimeSessionBootstrap:
    return resolve_runtime_session_bootstrap(
        runtime_session_bootstrap_cls=RuntimeSessionBootstrap,
        load_existing_runs_fn=load_existing_runs,
        load_host_state_fn=load_host_state,
        dedup_key_fn=dedup_key,
        current_campaign_key_fn=_current_campaign_key,
        campaign_settings_for_key_fn=campaign_settings_for_key,
        load_curated_plan_fn=load_curated_plan,
        load_runtime_plan_meta_fn=load_runtime_plan_meta,
        host_from_target_fn=host_from_target,
        is_resolvable_host_fn=is_resolvable_host,
        load_runtime_toggles_fn=load_runtime_toggles,
        pipeline_config_path=PIPELINE_CONFIG_PATH,
        normalize_pipeline_flags_fn=normalize_pipeline_flags,
        warn_fn=_warn_runner,
        load_planner_hints_fn=load_planner_hints,
        load_queue_state_fn=load_queue_state,
    )



def _build_runtime_session_state_from_bootstrap(bootstrap: RuntimeSessionBootstrap) -> RuntimeSessionState:
    return resolve_runtime_session_state_from_bootstrap(
        runtime_session_state_cls=RuntimeSessionState,
        bootstrap=bootstrap,
    )



def build_runtime_session_state() -> tuple[dict, RuntimeSessionState, datetime, int, int, int, str, int]:
    return resolve_runtime_session_state(
        reports_dir=REPORTS_DIR,
        validate_campaign_fn=validate_campaign,
        selected_scope_path_fn=_selected_scope_path,
        runtime_session_state_cls=RuntimeSessionState,
        load_runtime_session_bootstrap_fn=_load_runtime_session_bootstrap,
        build_runtime_session_state_from_bootstrap_fn=_build_runtime_session_state_from_bootstrap,
    )


def _build_runtime_execution_deps(*, qualification_mode: str, qualification_promising_threshold: str) -> RuntimeExecutionDeps:
    return build_runtime_execution_deps(
        runtime_execution_deps_cls=RuntimeExecutionDeps,
        summarize_result_fn=summarize_result,
        post_result_common_fn=post_result_common,
        qualify_and_finalize_run_fn=qualify_and_finalize_run,
        inspect_json_signal_from_command_fn=inspect_json_signal_from_command,
        parse_rc_metrics_fn=parse_rc_metrics,
        run_control_comparison_fn=lambda planned_cmd, timeout_sec: acc.run_control_comparison(planned_cmd, timeout_sec=timeout_sec),
        attack_family_fn=attack_family,
        repeated_consistency_ok_fn=repeated_consistency_ok,
        qualify_fn=lambda payload: vq.qualify(payload).as_dict(),
        can_be_confirmed_fn=lambda qual: evp.can_be_confirmed(qual, require_repro_pass=True),
        compute_promising_fn=lambda qual, summary_text, classification: compute_promising(qual, summary_text, classification, qualification_mode, qualification_promising_threshold),
        finding_lifecycle_fn=finding_lifecycle,
        adaptive_aggression_fn=adaptive_aggression,
        normalize_pipeline_status_fn=normalize_pipeline_status,
        log_event_fn=log_event,
        run_pipeline_fn=run_pipeline,
    )


def _build_runtime_runner_deps(*, apply_post_run_actions_fn: Callable[..., tuple[int, dict]], project_runtime_decision_to_run_info_fn: Callable[..., dict], maybe_reconsult_planner_fn: Callable[..., None], refresh_planner_hints_and_reprioritize_fn: Callable[..., None], prepare_task_precheck_fn: Callable[..., dict], prepare_curated_task_fn: Callable[..., dict | None], prepare_runtime_task_fn: Callable[..., dict | None], reprioritize_queues_fn: Callable[[], None], persist_recorded_run_fn: Callable[..., float], apply_runtime_adaptation_fn: Callable[[dict], None]) -> RuntimeRunnerDeps:
    return build_runtime_runner_deps(
        runtime_runner_deps_cls=RuntimeRunnerDeps,
        apply_post_run_actions_fn=apply_post_run_actions_fn,
        project_runtime_decision_to_run_info_fn=project_runtime_decision_to_run_info_fn,
        maybe_reconsult_planner_fn=maybe_reconsult_planner_fn,
        refresh_planner_hints_and_reprioritize_fn=refresh_planner_hints_and_reprioritize_fn,
        prepare_task_precheck_fn=prepare_task_precheck_fn,
        prepare_curated_task_fn=prepare_curated_task_fn,
        prepare_runtime_task_fn=prepare_runtime_task_fn,
        reprioritize_queues_fn=reprioritize_queues_fn,
        persist_recorded_run_fn=persist_recorded_run_fn,
        apply_runtime_adaptation_fn=apply_runtime_adaptation_fn,
    )


@dataclass
class ExecuteRunnerSessionInputs:
    state: RuntimeSessionState
    max_runs: int
    target_load_limit: int
    time_budget_min: int
    retry_policy: str
    run_started: datetime
    scope_targets: list[str]
    preempt_in_curated: bool
    queue_coordinator: Any
    log_event_fn: Callable[..., None]
    read_runtime_control_state_fn: Callable[[], dict]
    read_runtime_owner_override_fn: Callable[..., bool]
    read_runtime_aggression_override_fn: Callable[..., int | None]
    apply_runtime_overrides_fn: Callable[..., tuple[bool, bool, int | None, int | None]]
    handle_post_run_actions_fn: Callable[..., tuple[int, dict]]
    prepare_curated_task_fn: Callable[..., dict | None]
    prepare_runtime_task_fn: Callable[..., dict | None]
    reprioritize_queues_fn: Callable[..., None]
    persist_recorded_run_fn: Callable[..., float]
    maybe_trigger_plan_regeneration_fn: Callable[..., None]
    execute_runtime_task_fn: Callable[..., tuple[float, int]]
    resolve_main_loop_candidate_fn: Callable[..., dict]
    record_run_fn: Callable[..., None]
    persist_live_summary_fn: Callable[[], None]
    normalize_runtime_task_fn: Callable[..., dict]
    reconcile_active_plan_if_needed_fn: Callable[..., None]
    maybe_preempt_curated_entry_fn: Callable[..., bool]
    dedup_key_fn: Callable[..., str]
    build_deduped_target_plan_fn: Callable[..., list[dict]]
    prepare_deps: RuntimePrepareDeps
    propose_next_vector_fn: Callable[[list[dict]], tuple[str, str]]
    unpack_queued_task_fn: Callable[..., dict]
    clamp_aggression_fn: Callable[[int], int]
    capped_aggression_fn: Callable[[str, str, int], int]
    run_curated_loop_fn: Callable[..., None]
    run_main_loop_fn: Callable[..., None]
    out_path: str
    reports_dir: Path
    archive_root: Path
    campaign_validation: dict
    quality_telemetry: dict
    finalize_outputs_fn: Callable[..., dict]
    flush_precheck_summary_fn: Callable[..., None]
    flush_dns_skip_summary_fn: Callable[..., None]
    flush_host_cooldown_summary_fn: Callable[..., None]
    flush_execution_gate_summary_fn: Callable[..., None]
    log_operation_fn: Callable[..., None]



def _build_execute_runner_session_inputs(*, state: RuntimeSessionState, max_runs: int, target_load_limit: int, time_budget_min: int, retry_policy: str, run_started: datetime, scope_targets: list[str], toggles: dict, queue_coordinator: Any, prepare_deps: RuntimePrepareDeps, quality_telemetry: dict, campaign_validation: dict, execute_runtime_task_fn: Callable[..., tuple[float, int]], maybe_trigger_plan_regeneration_fn: Callable[..., None], reconcile_active_plan_if_needed_fn: Callable[..., None], persist_live_summary_fn: Callable[[], None], flush_precheck_summary_fn: Callable[..., None], flush_dns_skip_summary_fn: Callable[..., None], flush_host_cooldown_summary_fn: Callable[..., None], flush_execution_gate_summary_fn: Callable[..., None], log_operation_fn: Callable[..., None]) -> ExecuteRunnerSessionInputs:
    return build_execute_runner_session_inputs(
        state=state,
        max_runs=max_runs,
        target_load_limit=target_load_limit,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        run_started=run_started,
        scope_targets=scope_targets,
        toggles=toggles,
        queue_coordinator=queue_coordinator,
        prepare_deps=prepare_deps,
        quality_telemetry=quality_telemetry,
        campaign_validation=campaign_validation,
        execute_runtime_task_fn=execute_runtime_task_fn,
        maybe_trigger_plan_regeneration_fn=maybe_trigger_plan_regeneration_fn,
        reconcile_active_plan_if_needed_fn=reconcile_active_plan_if_needed_fn,
        persist_live_summary_fn=persist_live_summary_fn,
        flush_precheck_summary_fn=flush_precheck_summary_fn,
        flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
        flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
        flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
        log_operation_fn=log_operation_fn,
        log_event_fn=log_event,
        read_runtime_control_state_fn=read_runtime_control_state,
        read_runtime_owner_override_fn=read_runtime_owner_override,
        read_runtime_aggression_override_fn=read_runtime_aggression_override,
        apply_runtime_overrides_fn=apply_runtime_overrides,
        handle_post_run_actions_fn=handle_post_run_actions,
        prepare_curated_task_fn=prepare_curated_task,
        prepare_runtime_task_fn=prepare_runtime_task,
        reprioritize_queues_fn=apply_queue_reprioritization,
        persist_recorded_run_fn=persist_recorded_run,
        resolve_main_loop_candidate_fn=resolve_main_loop_candidate,
        record_run_fn=record_run,
        normalize_runtime_task_fn=normalize_runtime_task,
        maybe_preempt_curated_entry_fn=maybe_preempt_curated_entry,
        dedup_key_fn=dedup_key,
        build_deduped_target_plan_fn=build_deduped_target_plan,
        propose_next_vector_fn=propose_next_vector,
        unpack_queued_task_fn=unpack_queued_task,
        clamp_aggression_fn=clamp_aggression,
        capped_aggression_fn=capped_aggression,
        run_curated_loop_fn=run_curated_loop,
        run_main_loop_fn=run_main_loop,
        out_path=OUT_PATH,
        reports_dir=REPORTS_DIR,
        archive_root=ARCHIVE_ROOT,
        finalize_outputs_fn=acr.finalize_outputs,
    )


def _build_finalize_runner_exception_inputs(*, state: RuntimeSessionState, campaign_validation: dict, run_started: datetime, max_runs: int, time_budget_min: int, retry_policy: str, quality_telemetry: dict, flush_precheck_summary_fn: Callable[..., None], flush_dns_skip_summary_fn: Callable[..., None], flush_host_cooldown_summary_fn: Callable[..., None], flush_execution_gate_summary_fn: Callable[..., None], log_operation_fn: Callable[..., None], error: Exception) -> FinalizeRunnerExceptionInputs:
    return build_finalize_runner_exception_inputs(
        state=state,
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=max_runs,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        quality_telemetry=quality_telemetry,
        flush_precheck_summary_fn=flush_precheck_summary_fn,
        flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
        flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
        flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
        log_operation_fn=log_operation_fn,
        error=error,
        out_path=OUT_PATH,
        reports_dir=REPORTS_DIR,
        archive_root=ARCHIVE_ROOT,
        finalize_outputs_fn=acr.finalize_outputs,
    )


def _build_queue_coordinator(*, followup_queue: Any, precision_queue: Any, host_rr: Any, host_success_count: Any, host_fail_count: Any) -> QueueCoordinator:
    return resolve_queue_coordinator_wrapper(
        build_queue_coordinator_fn=build_queue_coordinator,
        queue_coordinator_cls=QueueCoordinator,
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        host_rr=host_rr,
        host_success_count=host_success_count,
        host_fail_count=host_fail_count,
    )



def _build_runtime_precheck_context_inputs(*, unresolved_hosts: set, dns_skip_count: dict, host_dns_cache: dict, host_cooldown_until: dict, host_cooldown_skip_count: dict, autodiscover_deep_skip: bool, executed_keys: set, precheck_skip_examples: list, host_precheck_burst: dict, host_state: dict, deep_budget: dict, host_fail_streak: dict, host_success_count: dict, host_fail_count: dict, gate_skip_count: dict, gate_skip_examples: dict, increment_precheck_skip_fn: Callable[[], None], on_executed_key_fn: Callable[[], None], is_sensitive_host_fn: Callable[[str], bool], host_warmup_complete_fn: Callable[[dict, str], bool], host_health_cooldown_sec: int = 900, deep_budget_cap_per_host_family: int = 2, precheck_burst_cooldown_threshold: int = 10, precheck_burst_cooldown_sec: int = 300, host_fail_streak_backoff_step_sec: float = 0.4, host_fail_streak_backoff_cap_sec: float = 2.0) -> RuntimePrecheckContext:
    return resolve_precheck_context_wrapper(
        build_runtime_precheck_context_inputs_fn=build_runtime_precheck_context_inputs,
        runtime_precheck_context_cls=RuntimePrecheckContext,
        unresolved_hosts=unresolved_hosts,
        dns_skip_count=dns_skip_count,
        host_dns_cache=host_dns_cache,
        host_cooldown_until=host_cooldown_until,
        host_cooldown_skip_count=host_cooldown_skip_count,
        autodiscover_deep_skip=autodiscover_deep_skip,
        executed_keys=executed_keys,
        precheck_skip_examples=precheck_skip_examples,
        host_precheck_burst=host_precheck_burst,
        host_state=host_state,
        deep_budget=deep_budget,
        host_fail_streak=host_fail_streak,
        host_success_count=host_success_count,
        host_fail_count=host_fail_count,
        gate_skip_count=gate_skip_count,
        gate_skip_examples=gate_skip_examples,
        increment_precheck_skip_fn=increment_precheck_skip_fn,
        on_executed_key_fn=on_executed_key_fn,
        dedup_key_fn=dedup_key,
        family_allowed_for_host_stage_fn=lambda _host_state, _target, _family: family_allowed_for_host_stage(_host_state, _target, _family, is_sensitive_host=is_sensitive_host_fn, host_warmup_complete=host_warmup_complete_fn),
        log_skip_fn=lambda decision, _host, result: log_event('AUTO_CAMPAIGN', decision, 'skipped', result, actor='auto_campaign'),
        host_health_cooldown_sec=host_health_cooldown_sec,
        deep_budget_cap_per_host_family=deep_budget_cap_per_host_family,
        precheck_burst_cooldown_threshold=precheck_burst_cooldown_threshold,
        precheck_burst_cooldown_sec=precheck_burst_cooldown_sec,
        host_fail_streak_backoff_step_sec=host_fail_streak_backoff_step_sec,
        host_fail_streak_backoff_cap_sec=host_fail_streak_backoff_cap_sec,
    )



def _build_runtime_persist_services(*, reprioritize_queues_fn: Callable[[], None], persist_recorded_run_fn: Callable[..., float], maybe_trigger_plan_regeneration_fn: Callable[[str], None]) -> RuntimePersistServices:
    return build_runtime_persist_services(
        reprioritize_queues_fn=reprioritize_queues_fn,
        persist_recorded_run_fn=persist_recorded_run_fn,
        maybe_trigger_plan_regeneration_fn=maybe_trigger_plan_regeneration_fn,
    )



def _build_record_and_persist_run_inputs(*, services: RuntimePersistServices, state: RuntimeSessionState, run_info: dict, last_persist_ts: float, persist_live_summary_fn: Callable[[], None], update_learning_fn: Callable[..., None], save_host_state_fn: Callable[..., None], attack_family_fn: Callable[[str, str, str], str]) -> RecordAndPersistRunInputs:
    return build_record_and_persist_run_inputs(
        services=services,
        state=state,
        run_info=run_info,
        last_persist_ts=last_persist_ts,
        persist_live_summary_fn=persist_live_summary_fn,
        update_learning_fn=update_learning_fn,
        save_host_state_fn=save_host_state_fn,
        attack_family_fn=attack_family_fn,
        record_run_fn=record_run,
    )



@dataclass
class ExecuteRuntimeTaskInputs:
    task_ctx: dict
    objective: str
    target: str
    mode: str
    aggression: int
    owner_auth: bool
    owner_override: bool
    plan_name: str | None
    run_index: int
    last_heartbeat_ts: float
    runs_count: int
    followup_queue_len: int
    precision_queue_len: int
    deps: RuntimeExecutionDeps
    host_family_owner_gate: dict
    host_cooldown_until: dict
    host_code000_streak: dict
    host_code000_total: dict
    host_403_streak: dict
    host_fail_streak: dict
    host_fail_count: dict
    host_success_count: dict
    code000_streak_threshold: int
    code000_cooldown_sec: int
    code000_session_cap: int
    runs: list[dict]
    toggles: dict
    host_weak_count: dict
    quality_telemetry: dict
    qualification_mode: str
    qualification_promising_threshold: str



def _build_execute_runtime_task_inputs(*, task_ctx: dict, objective: str, target: str, mode: str, aggression: int, owner_auth: bool, owner_override: bool, plan_name: str | None, run_index: int, last_heartbeat_ts: float, confirm_total: int, state: RuntimeSessionState, execution_deps: RuntimeExecutionDeps, host_family_owner_gate: dict, host_cooldown_until: dict, host_code000_streak: dict, host_code000_total: dict, host_403_streak: dict, host_fail_streak: dict, host_fail_count: dict, host_success_count: dict, code000_streak_threshold: int, code000_cooldown_sec: int, code000_session_cap: int, toggles: dict, qualification_mode: str, qualification_promising_threshold: str) -> ExecuteRuntimeTaskInputs:
    return resolve_execute_task_inputs_wrapper(
        build_execute_runtime_task_inputs_fn=build_execute_runtime_task_inputs,
        execute_runtime_task_inputs_cls=ExecuteRuntimeTaskInputs,
        task_ctx=task_ctx,
        objective=objective,
        target=target,
        mode=mode,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        plan_name=plan_name,
        run_index=run_index,
        last_heartbeat_ts=last_heartbeat_ts,
        state=state,
        execution_deps=execution_deps,
        host_family_owner_gate=host_family_owner_gate,
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        host_fail_streak=host_fail_streak,
        host_fail_count=host_fail_count,
        host_success_count=host_success_count,
        code000_streak_threshold=code000_streak_threshold,
        code000_cooldown_sec=code000_cooldown_sec,
        code000_session_cap=code000_session_cap,
        toggles=toggles,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
    )



@dataclass
class CompleteRuntimeRunInputs:
    run_info: dict
    task_ctx: dict
    result: dict
    qual: dict
    classification: str
    auditor: str
    engine_status: str
    success_eval_status: str
    summary_text: str
    reason_code: str
    target: str
    objective: str
    aggression: int
    owner_auth: bool
    owner_override: bool
    mode: str
    confirm_total: int
    promising: bool
    runtime_decision: dict
    deps: RuntimeRunnerDeps
    record_and_persist_run_fn: Callable[[dict], None]
    toggles: dict
    runs: list[dict]
    promising_hits_ref: list[int]
    host_state: dict



def _build_complete_runtime_run_inputs(*, task_ctx: dict, result: dict, qual: dict, classification: str, auditor: str, engine_status: str, success_eval_status: str, summary_text: str, reason_code: str, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, confirm_total: int, promising: bool, run_info: dict, runner_deps: RuntimeRunnerDeps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, state: RuntimeSessionState) -> CompleteRuntimeRunInputs:
    return resolve_complete_run_inputs_wrapper(
        build_complete_runtime_run_inputs_fn=build_complete_runtime_run_inputs,
        task_ctx=task_ctx,
        result=result,
        qual=qual,
        classification=classification,
        auditor=auditor,
        engine_status=engine_status,
        success_eval_status=success_eval_status,
        summary_text=summary_text,
        reason_code=reason_code,
        target=target,
        objective=objective,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        mode=mode,
        confirm_total=confirm_total,
        promising=promising,
        run_info=run_info,
        runner_deps=runner_deps,
        record_and_persist_run_fn=record_and_persist_run_fn,
        toggles=toggles,
        state=state,
    )



def _run_record_and_persist_stage(*, services: RuntimePersistServices, state: RuntimeSessionState, run_info: dict, last_persist_ts: float, persist_live_summary_fn: Callable[[], None], update_learning_fn: Callable[..., None], save_host_state_fn: Callable[..., None], attack_family_fn: Callable[[str, str, str], str]) -> float:
    return resolve_record_persist_stage_wrapper(
        run_record_and_persist_stage_fn=run_record_and_persist_stage,
        build_record_and_persist_run_inputs_fn=_build_record_and_persist_run_inputs,
        record_and_persist_runtime_run_fn=record_and_persist_runtime_run,
        services=services,
        state=state,
        run_info=run_info,
        last_persist_ts=last_persist_ts,
        persist_live_summary_fn=persist_live_summary_fn,
        update_learning_fn=update_learning_fn,
        save_host_state_fn=save_host_state_fn,
        attack_family_fn=attack_family_fn,
    )


@dataclass
class RuntimeSessionBundleInputs:
    apply_post_run_actions_fn: Callable[..., tuple[int, dict]]
    project_runtime_decision_to_run_info_fn: Callable[..., dict]
    maybe_reconsult_planner_fn: Callable[..., None]
    refresh_planner_hints_and_reprioritize_fn: Callable[..., None]
    prepare_task_precheck_fn: Callable[..., dict]
    prepare_curated_task_fn: Callable[..., dict | None]
    prepare_runtime_task_fn: Callable[..., dict | None]
    build_execute_runtime_request_fn: Callable[..., dict]
    reprioritize_queues_fn: Callable[[], None]
    persist_recorded_run_fn: Callable[..., float]
    apply_runtime_adaptation_fn: Callable[[dict], None]
    summarize_result_fn: Callable[..., dict]
    post_result_common_fn: Callable[..., dict]
    qualify_and_finalize_run_fn: Callable[..., dict]
    inspect_json_signal_from_command_fn: Callable[..., dict]
    parse_rc_metrics_fn: Callable[[str], dict]
    run_control_comparison_fn: Callable[..., dict]
    attack_family_fn: Callable[[str, str, str], str]
    repeated_consistency_ok_fn: Callable[[list[dict], str, str], bool]
    qualify_fn: Callable[[dict], dict]
    can_be_confirmed_fn: Callable[[dict], bool]
    compute_promising_fn: Callable[[dict, str, str], bool]
    finding_lifecycle_fn: Callable[..., dict]
    adaptive_aggression_fn: Callable[..., int]
    normalize_pipeline_status_fn: Callable[[str], str]
    log_event_fn: Callable[..., None]
    run_pipeline_fn: Callable[..., dict]



def _build_runtime_session_bundle_inputs(*, apply_post_run_actions_fn: Callable[..., tuple[int, dict]], project_runtime_decision_to_run_info_fn: Callable[..., dict], maybe_reconsult_planner_fn: Callable[..., None], refresh_planner_hints_and_reprioritize_fn: Callable[..., None], prepare_task_precheck_fn: Callable[..., dict], prepare_curated_task_fn: Callable[..., dict | None], prepare_runtime_task_fn: Callable[..., dict | None], build_execute_runtime_request_fn: Callable[..., dict], reprioritize_queues_fn: Callable[[], None], persist_recorded_run_fn: Callable[..., float], apply_runtime_adaptation_fn: Callable[[dict], None], qualification_mode: str, qualification_promising_threshold: str) -> RuntimeSessionBundleInputs:
    return resolve_session_bundle_inputs_wrapper(
        build_runtime_session_bundle_inputs_fn=build_runtime_session_bundle_inputs,
        runtime_session_bundle_inputs_cls=RuntimeSessionBundleInputs,
        runtime_runner_deps_cls=RuntimeRunnerDeps,
        runtime_execution_deps_cls=RuntimeExecutionDeps,
        apply_post_run_actions_fn=apply_post_run_actions_fn,
        project_runtime_decision_to_run_info_fn=project_runtime_decision_to_run_info_fn,
        maybe_reconsult_planner_fn=maybe_reconsult_planner_fn,
        refresh_planner_hints_and_reprioritize_fn=refresh_planner_hints_and_reprioritize_fn,
        prepare_task_precheck_fn=prepare_task_precheck_fn,
        prepare_curated_task_fn=prepare_curated_task_fn,
        prepare_runtime_task_fn=prepare_runtime_task_fn,
        build_execute_runtime_request_fn=build_execute_runtime_request_fn,
        reprioritize_queues_fn=reprioritize_queues_fn,
        persist_recorded_run_fn=persist_recorded_run_fn,
        apply_runtime_adaptation_fn=apply_runtime_adaptation_fn,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
        summarize_result_fn=summarize_result,
        post_result_common_fn=post_result_common,
        qualify_and_finalize_run_fn=qualify_and_finalize_run,
        inspect_json_signal_from_command_fn=inspect_json_signal_from_command,
        parse_rc_metrics_fn=parse_rc_metrics,
        run_control_comparison_fn=lambda planned_cmd, timeout_sec: acc.run_control_comparison(planned_cmd, timeout_sec=timeout_sec),
        attack_family_fn=attack_family,
        repeated_consistency_ok_fn=repeated_consistency_ok,
        qualify_fn=lambda payload: vq.qualify(payload).as_dict(),
        can_be_confirmed_fn=lambda qual: evp.can_be_confirmed(qual, require_repro_pass=True),
        compute_promising_fn=lambda qual, summary_text, classification: compute_promising(qual, summary_text, classification, qualification_mode, qualification_promising_threshold),
        finding_lifecycle_fn=finding_lifecycle,
        adaptive_aggression_fn=adaptive_aggression,
        normalize_pipeline_status_fn=normalize_pipeline_status,
        log_event_fn=log_event,
        run_pipeline_fn=run_pipeline,
    )



def _build_main_state_aliases(state: RuntimeSessionState) -> MainStateAliases:
    return resolve_state_aliases_wrapper(
        build_main_state_aliases_fn=build_main_state_aliases,
        state=state,
    )



def _make_skip_summary_flusher(*, precheck_skip_count_ref: list[int], precheck_skip_examples_ref: list[str], dns_skip_count_ref: dict[str, int], host_cooldown_skip_count_ref: dict[str, int], execution_gate_skip_count_ref: dict[str, int], execution_gate_skip_examples_ref: dict[str, list[str]]) -> Callable[[bool], None]:
    return resolve_skip_flusher_wrapper(
        make_skip_summary_flusher_fn=make_skip_summary_flusher,
        flush_skip_summaries_fn=acst.flush_skip_summaries,
        log_event_fn=log_event,
        precheck_skip_count_ref=precheck_skip_count_ref,
        precheck_skip_examples_ref=precheck_skip_examples_ref,
        dns_skip_count_ref=dns_skip_count_ref,
        host_cooldown_skip_count_ref=host_cooldown_skip_count_ref,
        execution_gate_skip_count_ref=execution_gate_skip_count_ref,
        execution_gate_skip_examples_ref=execution_gate_skip_examples_ref,
    )



def _build_main_skip_summary_flushers(*, precheck_skip_count_ref: list[int], precheck_skip_examples: list[str], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], execution_gate_skip_examples: dict[str, list[str]]) -> dict:
    return resolve_skip_summary_wrapper(
        build_main_skip_summary_flushers_fn=build_main_skip_summary_flushers,
        make_skip_summary_flusher_fn=_make_skip_summary_flusher,
        precheck_skip_count_ref=precheck_skip_count_ref,
        precheck_skip_examples=precheck_skip_examples,
        dns_skip_count=dns_skip_count,
        host_cooldown_skip_count=host_cooldown_skip_count,
        execution_gate_skip_count=execution_gate_skip_count,
        execution_gate_skip_examples=execution_gate_skip_examples,
    )



def _build_main_planner_callbacks(*, state: RuntimeSessionState, toggles: dict, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], planner_hints_cache_ref: list[dict], last_regen_run_index_ref: list[int], curated_plan_ref: list[list[dict]], active_plan_revision_ref: list[int], active_plan_hash_ref: list[str], reprioritize_queues_fn: Callable[[], None]) -> dict:
    return resolve_planner_callbacks_passthrough_wrapper(
        resolve_main_planner_callback_wrapper_fn=resolve_main_planner_callback_wrapper,
        resolve_main_planner_callbacks_fn=resolve_main_planner_callbacks,
        state=state,
        toggles=toggles,
        runs=runs,
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        planner_hints_cache_ref=planner_hints_cache_ref,
        last_regen_run_index_ref=last_regen_run_index_ref,
        curated_plan_ref=curated_plan_ref,
        active_plan_revision_ref=active_plan_revision_ref,
        active_plan_hash_ref=active_plan_hash_ref,
        reprioritize_queues_fn=reprioritize_queues_fn,
        summarize_planner_feedback_fn=summarize_planner_feedback,
        load_planner_hints_fn=load_planner_hints,
        apply_planner_hints_refresh_fn=apply_planner_hints_refresh,
        apply_plan_regeneration_fn=apply_plan_regeneration,
        regenerate_runtime_plan_fn=regenerate_runtime_plan_from_blueprint,
        apply_plan_reconciliation_fn=apply_plan_reconciliation,
        load_runtime_plan_meta_fn=load_runtime_plan_meta,
        load_curated_plan_fn=load_curated_plan,
        dedup_key_fn=dedup_key,
        log_event_fn=log_event,
    )



def _persist_main_runtime_snapshot(*, campaign_validation: dict, run_started: datetime, max_runs: int, time_budget_min: int, retry_policy: str, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], precheck_skip_count_ref: list[int], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], quality_telemetry: dict, host_state: dict) -> None:
    return resolve_snapshot_wrapper(
        persist_main_runtime_snapshot_fn=persist_main_runtime_snapshot,
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=max_runs,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        runs=runs,
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        precheck_skip_count_ref=precheck_skip_count_ref,
        dns_skip_count=dns_skip_count,
        host_cooldown_skip_count=host_cooldown_skip_count,
        execution_gate_skip_count=execution_gate_skip_count,
        quality_telemetry=quality_telemetry,
        host_state=host_state,
        out_path=OUT_PATH,
        save_queue_state_fn=save_queue_state,
        current_campaign_key_fn=_current_campaign_key,
        runtime_snapshot_path=str(RUNTIME_SNAPSHOT_PATH),
        load_runtime_plan_meta_fn=load_runtime_plan_meta,
        persist_live_snapshot_fn=acst.persist_live_snapshot,
        warn_fn=_warn_runner,
    )



def _refresh_main_runtime_overrides(owner_override_global: bool, last_override_state: bool, aggression_override_global: int | None, last_aggression_override: int | None) -> tuple[bool, bool, int | None, int | None]:
    return resolve_overrides_wrapper(
        refresh_main_runtime_overrides_fn=refresh_main_runtime_overrides,
        owner_override_global=owner_override_global,
        last_override_state=last_override_state,
        aggression_override_global=aggression_override_global,
        last_aggression_override=last_aggression_override,
        apply_runtime_overrides_fn=apply_runtime_overrides,
        read_runtime_owner_override_fn=read_runtime_owner_override,
        read_runtime_aggression_override_fn=read_runtime_aggression_override,
        log_event_fn=log_event,
    )



def _build_main_runtime_callbacks(*, campaign_validation: dict, run_started: datetime, max_runs: int, time_budget_min: int, retry_policy: str, runs: list[dict], followup_queue: list[dict], precision_queue: list[dict], precheck_skip_count_ref: list[int], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], quality_telemetry: dict, host_state: dict, queue_coordinator: QueueCoordinator) -> dict:
    return resolve_runtime_callbacks_wrapper(
        build_main_runtime_callbacks_fn=build_main_runtime_callbacks,
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=max_runs,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        runs=runs,
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        precheck_skip_count_ref=precheck_skip_count_ref,
        dns_skip_count=dns_skip_count,
        host_cooldown_skip_count=host_cooldown_skip_count,
        execution_gate_skip_count=execution_gate_skip_count,
        quality_telemetry=quality_telemetry,
        host_state=host_state,
        queue_coordinator=queue_coordinator,
        persist_main_runtime_snapshot_fn=_persist_main_runtime_snapshot,
        refresh_main_runtime_overrides_fn=_refresh_main_runtime_overrides,
    )



def _build_main_precheck_hooks(*, precheck_skip_count_ref: list[int], flush_precheck_summary_fn: Callable[[], None], flush_dns_skip_summary_fn: Callable[[], None], flush_host_cooldown_summary_fn: Callable[[], None], flush_execution_gate_summary_fn: Callable[[], None]) -> dict:
    return resolve_precheck_hooks_wrapper(
        build_main_precheck_hooks_fn=build_main_precheck_hooks,
        precheck_skip_count_ref=precheck_skip_count_ref,
        flush_precheck_summary_fn=flush_precheck_summary_fn,
        flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
        flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
        flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
    )



def _reprioritize_main_prepare_queues(*, state: RuntimeSessionState, toggles: dict, planner_hints_cache_ref: list[dict]) -> None:
    return reprioritize_main_prepare_queues(
        state=state,
        toggles=toggles,
        planner_hints_cache_ref=planner_hints_cache_ref,
        attack_family_fn=attack_family,
        family_allowed_for_host_stage_fn=family_allowed_for_host_stage,
        planner_vector_weight_fn=planner_vector_weight,
        host_from_target_fn=host_from_target,
        apply_queue_reprioritization_fn=apply_queue_reprioritization,
    )



def _prepare_task_precheck_from_context(precheck_ctx: RuntimePrecheckContext, *, objective: str, target: str, mode: str, task_family: str, dedup_mode_suffix: bool, runtime_task: dict | None = None):
    return prepare_task_precheck_from_context(
        precheck_ctx,
        objective=objective,
        target=target,
        mode=mode,
        task_family=task_family,
        dedup_mode_suffix=dedup_mode_suffix,
        runtime_task=runtime_task,
    )



def _build_main_prepare_callbacks(*, precheck_ctx: RuntimePrecheckContext, scheduled_keys: set, toggles: dict, state: RuntimeSessionState, planner_hints_cache_ref: list[dict]) -> dict:
    return resolve_prepare_callbacks_wrapper(
        build_main_prepare_callbacks_fn=build_main_prepare_callbacks,
        precheck_ctx=precheck_ctx,
        scheduled_keys=scheduled_keys,
        toggles=toggles,
        state=state,
        planner_hints_cache_ref=planner_hints_cache_ref,
        attack_family_fn=attack_family,
        prepare_curated_task_fn=prepare_curated_task,
        prepare_runtime_task_fn=prepare_runtime_task,
        capped_aggression_fn=capped_aggression,
        family_allowed_for_host_stage_fn=family_allowed_for_host_stage,
        planner_vector_weight_fn=planner_vector_weight,
        host_from_target_fn=host_from_target,
        apply_queue_reprioritization_fn=apply_queue_reprioritization,
    )



def _build_main_post_run_actions_callback(*, retry_counts: dict, retry_limit: int, followup_queue: list, followup_counts: dict, followup_recent: dict, max_followups_per_target: int, scheduled_keys: set, host_weak_count: dict, host_family_owner_gate: dict, confirm_counts: dict, confirm_recent: dict, confirm_class_counts: dict, max_confirm_jobs_per_target: int, max_confirm_jobs_total: int, max_confirm_jobs_per_class: int, confirm_job_cooldown_sec: int, quality_telemetry: dict, toggles: dict, enqueue_followup_task_fn: Callable[[dict, bool], None]) -> Callable[..., tuple[int, dict]]:
    return resolve_post_run_actions_wrapper(
        build_main_post_run_actions_callback_fn=build_main_post_run_actions_callback,
        handle_post_run_actions_fn=handle_post_run_actions,
        retry_counts=retry_counts,
        retry_limit=retry_limit,
        followup_queue=followup_queue,
        followup_counts=followup_counts,
        followup_recent=followup_recent,
        max_followups_per_target=max_followups_per_target,
        scheduled_keys=scheduled_keys,
        host_weak_count=host_weak_count,
        host_family_owner_gate=host_family_owner_gate,
        confirm_counts=confirm_counts,
        confirm_recent=confirm_recent,
        confirm_class_counts=confirm_class_counts,
        max_confirm_jobs_per_target=max_confirm_jobs_per_target,
        max_confirm_jobs_total=max_confirm_jobs_total,
        max_confirm_jobs_per_class=max_confirm_jobs_per_class,
        confirm_job_cooldown_sec=confirm_job_cooldown_sec,
        quality_telemetry=quality_telemetry,
        toggles=toggles,
        enqueue_followup_task_fn=enqueue_followup_task_fn,
    )



def _complete_execute_runtime_pipeline_result(*, task_ctx: dict, target: str, objective: str, aggression: int, owner_auth: bool, owner_override: bool, mode: str, confirm_total: int, pipeline_result: tuple, runner_deps: RuntimeRunnerDeps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, state: RuntimeSessionState) -> int:
    return resolve_execute_completion_wrapper(
        complete_execute_runtime_pipeline_result_fn=complete_execute_runtime_pipeline_result,
        task_ctx=task_ctx,
        target=target,
        objective=objective,
        aggression=aggression,
        owner_auth=owner_auth,
        owner_override=owner_override,
        mode=mode,
        confirm_total=confirm_total,
        pipeline_result=pipeline_result,
        runner_deps=runner_deps,
        record_and_persist_run_fn=record_and_persist_run_fn,
        toggles=toggles,
        state=state,
        build_complete_runtime_run_inputs_fn=_build_complete_runtime_run_inputs,
        complete_runtime_run_fn=complete_runtime_run,
    )



def _build_main_execute_runtime_task_callback(*, state: RuntimeSessionState, execution_deps: RuntimeExecutionDeps, runner_deps: RuntimeRunnerDeps, record_and_persist_run_fn: Callable[[dict], None], toggles: dict, host_family_owner_gate: dict, host_cooldown_until: dict, host_code000_streak: dict, host_code000_total: dict, host_403_streak: dict, host_fail_streak: dict, host_fail_count: dict, host_success_count: dict, code000_streak_threshold: int, code000_cooldown_sec: int, code000_session_cap: int, qualification_mode: str, qualification_promising_threshold: str) -> Callable[..., tuple[float, int]]:
    return resolve_execute_task_callback_wrapper(
        build_main_execute_runtime_task_callback_fn=build_main_execute_runtime_task_callback,
        state=state,
        execution_deps=execution_deps,
        runner_deps=runner_deps,
        record_and_persist_run_fn=record_and_persist_run_fn,
        toggles=toggles,
        host_family_owner_gate=host_family_owner_gate,
        host_cooldown_until=host_cooldown_until,
        host_code000_streak=host_code000_streak,
        host_code000_total=host_code000_total,
        host_403_streak=host_403_streak,
        host_fail_streak=host_fail_streak,
        host_fail_count=host_fail_count,
        host_success_count=host_success_count,
        code000_streak_threshold=code000_streak_threshold,
        code000_cooldown_sec=code000_cooldown_sec,
        code000_session_cap=code000_session_cap,
        qualification_mode=qualification_mode,
        qualification_promising_threshold=qualification_promising_threshold,
        build_execute_runtime_task_inputs_fn=_build_execute_runtime_task_inputs,
        execute_runtime_task_pipeline_fn=execute_runtime_task_pipeline,
        complete_execute_runtime_pipeline_result_fn=_complete_execute_runtime_pipeline_result,
    )



def _build_main_persist_callbacks(*, persist_services: RuntimePersistServices, state: RuntimeSessionState, last_persist_ts_ref: list[float], persist_live_summary_fn: Callable[[], None]) -> dict:
    return resolve_persist_callbacks_passthrough_wrapper(
        build_main_persist_callbacks_fn=build_main_persist_callbacks,
        persist_services=persist_services,
        state=state,
        last_persist_ts_ref=last_persist_ts_ref,
        persist_live_summary_fn=persist_live_summary_fn,
        run_record_and_persist_stage_fn=_run_record_and_persist_stage,
        apply_runtime_adaptation_fn=apply_runtime_adaptation,
    )



def _run_main_execution_stage(*, state: RuntimeSessionState, campaign_validation: dict, run_started: datetime, max_runs: int, target_load_limit: int, time_budget_min: int, retry_policy: str, toggles: dict, queue_coordinator: QueueCoordinator, prepare_deps: RuntimePrepareDeps, quality_telemetry: dict, execute_runtime_task_fn: Callable[..., tuple[float, int]], maybe_trigger_plan_regeneration_fn: Callable[..., None], reconcile_active_plan_if_needed_fn: Callable[..., None], persist_live_summary_fn: Callable[[], None], flush_precheck_summary_fn: Callable[..., None], flush_dns_skip_summary_fn: Callable[..., None], flush_host_cooldown_summary_fn: Callable[..., None], flush_execution_gate_summary_fn: Callable[..., None], log_operation_fn: Callable[..., None]) -> None:
    return resolve_execution_stage_passthrough_wrapper(
        resolve_run_main_execution_stage_fn=resolve_run_main_execution_stage,
        state=state,
        campaign_validation=campaign_validation,
        run_started=run_started,
        max_runs=max_runs,
        target_load_limit=target_load_limit,
        time_budget_min=time_budget_min,
        retry_policy=retry_policy,
        toggles=toggles,
        queue_coordinator=queue_coordinator,
        prepare_deps=prepare_deps,
        quality_telemetry=quality_telemetry,
        execute_runtime_task_fn=execute_runtime_task_fn,
        maybe_trigger_plan_regeneration_fn=maybe_trigger_plan_regeneration_fn,
        reconcile_active_plan_if_needed_fn=reconcile_active_plan_if_needed_fn,
        persist_live_summary_fn=persist_live_summary_fn,
        flush_precheck_summary_fn=flush_precheck_summary_fn,
        flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
        flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
        flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
        log_operation_fn=log_operation_fn,
        build_execute_runner_session_inputs_fn=_build_execute_runner_session_inputs,
        current_scope_targets_fn=_current_scope_targets,
        execute_runner_session_fn=execute_runner_session,
        build_finalize_runner_exception_inputs_fn=_build_finalize_runner_exception_inputs,
        finalize_runner_exception_fn=finalize_runner_exception,
        globals_dict=globals(),
    )



def _build_main_session_base_fields(state: RuntimeSessionState) -> MainSessionBaseFields:
    return resolve_session_base_fields_wrapper(
        build_main_session_base_fields_fn=build_main_session_base_fields,
        state=state,
    )



def _build_main_session_alias_fields(state_aliases: MainStateAliases, queue_coordinator: QueueCoordinator) -> MainSessionAliasFields:
    return resolve_session_alias_fields_wrapper(
        build_main_session_alias_fields_fn=build_main_session_alias_fields,
        state_aliases=state_aliases,
        queue_coordinator=queue_coordinator,
    )



def _build_main_session_setup(state: RuntimeSessionState) -> MainSessionSetup:
    return resolve_session_setup_wrapper(
        build_main_session_setup_fn=build_main_session_setup,
        state=state,
        build_main_runtime_controls_fn=build_main_runtime_controls,
        build_main_state_aliases_fn=_build_main_state_aliases,
        build_queue_coordinator_fn=_build_queue_coordinator,
        build_main_session_alias_fields_fn=_build_main_session_alias_fields,
    )



def main() -> None:
    return resolve_run_main_entry(
        build_runtime_session_state_fn=build_runtime_session_state,
        log_event_fn=log_event,
        build_main_session_setup_fn=_build_main_session_setup,
        build_main_skip_summary_flushers_fn=_build_main_skip_summary_flushers,
        build_main_runtime_callbacks_fn=_build_main_runtime_callbacks,
        build_main_post_run_actions_callback_fn=_build_main_post_run_actions_callback,
        build_main_precheck_hooks_fn=_build_main_precheck_hooks,
        build_runtime_precheck_context_inputs_fn=_build_runtime_precheck_context_inputs,
        build_main_prepare_callbacks_fn=_build_main_prepare_callbacks,
        build_main_planner_callbacks_fn=_build_main_planner_callbacks,
        build_runtime_persist_services_fn=_build_runtime_persist_services,
        build_main_persist_callbacks_fn=_build_main_persist_callbacks,
        build_runtime_session_bundle_inputs_fn=_build_runtime_session_bundle_inputs,
        build_runtime_session_bundles_fn=build_runtime_session_bundles,
        build_main_execute_runtime_task_callback_fn=_build_main_execute_runtime_task_callback,
        run_main_execution_stage_fn=_run_main_execution_stage,
        project_runtime_decision_to_run_info_fn=project_runtime_decision_to_run_info,
        maybe_reconsult_planner_fn=maybe_reconsult_planner,
        summarize_planner_feedback_fn=summarize_planner_feedback,
        build_execute_runtime_request_fn=build_execute_runtime_request,
        persist_recorded_run_fn=persist_recorded_run,
        log_operation_fn=log_operation,
        is_sensitive_host_fn=is_sensitive_host,
        host_warmup_complete_fn=host_warmup_complete,
    )
if __name__ == "__main__":
    main()
