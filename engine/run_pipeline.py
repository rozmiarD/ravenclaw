#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.append(str(ENGINE_DIR))
from campaign_utils import extract_host_from_url, host_in_scope, load_scope_domains  # type: ignore
from campaign_validator import validate_campaign  # type: ignore
from executor import ExecutionEngine  # type: ignore
from status_utils import normalize_pipeline_status, normalize_engine_status, normalize_auditor_decision  # type: ignore
from aggression_policy import clamp_aggression  # type: ignore
from contracts import remap_aggression_for_policy, sanitize_action_spec, sanitize_action_spec_auth_modes, validate_action_spec, validate_auditor_payload  # type: ignore
from paths import wp, ep, rsp, REPORTS_DIR, LOGDASH_DIR  # type: ignore
from policy_gateway import evaluate_action_spec  # type: ignore
from runtime_campaign_state import resolve_campaign_key  # type: ignore
from runtime_plan_service import load_planner_ui_state  # type: ignore
from runtime_agent_io import ask_json  # type: ignore
from runtime_signal_eval import high_signal, interesting_http_signal, evaluate_success_criteria  # type: ignore
from govengine.action_schema import ACTION_TYPE_TO_CAPABILITY, ACTION_TYPE_TO_EXPERIMENT_SHAPE
from govengine.capability_recipes import can_resolve_tool_from_capability
from policy_core import get_runtime_brain_allowed_tools  # type: ignore
from execution_contracts import build_prepared_execution_spec, build_approved_execution_spec, redact_prepared_execution_spec_for_auditor  # type: ignore
from govengine.semantic_loss_policy import semantic_loss_runtime_gate
from public_delivery import apply_delivery_profile_to_pipeline, resolve_delivery_profile, run_auditor_adapter, run_brain_adapter, run_execution_adapter  # type: ignore
from scl_ravenclaw_adapter import build_lifecycle_artifacts_v02  # type: ignore


def _selected_scope_path() -> Path:
    try:
        ui = load_planner_ui_state()
        raw = str((ui or {}).get('scope_txt') or '').strip()
        if raw:
            p = Path(raw)
            if p.exists():
                return p
    except Exception:
        pass
    demo_scope = ENGINE_DIR / 'planer' / 'examples' / 'sample_scope.txt'
    if os.environ.get('RAVENCLAW_MODE') == 'demo' and demo_scope.exists():
        return demo_scope
    return wp('scope', 'scope.txt')


from pipeline_governance import (
    policy_gate as _policy_gate,
    record_approval_transform as _record_approval_transform,
    tracked_auditor_constraint_raise as _tracked_auditor_constraint_raise,
    tracked_auditor_replace as _tracked_auditor_replace,
)
from pipeline_postprocess import (
    run_analysis_stage,
    run_light_stage,
    truncate_text as _truncate_text,
)
from pipeline_execution import (
    _apply_required_headers_to_args,
    apply_required_headers,
    prepare_action_spec_for_execution,
)
from pipeline_planning import (
    apply_intent_guidance_to_brain as _apply_intent_guidance_to_brain,
    enforce_brain_tool_whitelist as _enforce_brain_tool_whitelist,
    fallback_brain_action as _fallback_brain_action,
    preferred_tools_for_task_family as _preferred_tools_for_task_family,
)
from pipeline_context import (
    _coerce_json_dict,
    _coerce_json_list,
    _merge_intent_runtime_context,
    append_context_entry,
    compact_recent_context,
    contextual_brain_tooling,
    filter_recent_context_for_target,
    load_context_history,
    load_credentials_runtime_policy,
    load_pipeline_config,
    load_planner_hints as _load_planner_hints,
    save_pipeline_config,
    summarize_recent_runtime_state,
)


def truncate_text(value: str, limit: int = 4000) -> str:
    return _truncate_text(value, limit)


def record_approval_transform(chain: list[dict], source: str, before: dict, after: dict) -> None:
    _record_approval_transform(chain, source, before, after)


def tracked_auditor_replace(chain: list[dict], source: str, auditor: dict, **patch: Any) -> dict:
    return _tracked_auditor_replace(chain, source, auditor, **patch)


def tracked_auditor_constraint_raise(chain: list[dict], source: str, auditor: dict, aggression: int, reason_suffix: str, reason_code: str) -> dict:
    return _tracked_auditor_constraint_raise(chain, source, auditor, aggression, reason_suffix, reason_code)


def _clone_namespace(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(**vars(args))


def _mock_brain_action(objective: str, target: str, aggression: int, *, task_family: str = '') -> Dict[str, Any]:
    return {
        'intent': 'mock_demo_brain_action',
        'target': str(target or ''),
        'tool': 'curl',
        'tool_candidates': ['curl'],
        'tool_preferences': {'prefer_tool': 'curl'},
        'args': ['-sS', '-I', str(target or '')],
        'action_type': 'single_probe',
        'experiment_shape': 'single_step',
        'capability': ACTION_TYPE_TO_CAPABILITY.get('single_probe', 'http_probe'),
        'probe_recipe': {},
        'constraints': {'aggression': max(1, min(int(aggression or 1), 2))},
        'planner_alignment': 'aligned',
        'task_family': str(task_family or ''),
        'why_now': 'mock adapter path for public demo delivery',
        'expected_signal': 'bounded demo-safe HTTP preview',
        'redundancy_risk': 'low',
    }



def _local_auditor_decision(*, aggression: int, delivery_profile: Dict[str, Any], semantic_loss_rereview_required: bool) -> Dict[str, Any]:
    demo_mode = bool(delivery_profile.get('demo_mode'))
    if semantic_loss_rereview_required:
        return {
            'decision': 'approve',
            'reason': 'local_delivery_adapter_approved_bounded_semantic_rereview' if not demo_mode else 'demo_mode_local_adapter_approved_bounded_semantic_rereview',
            'reason_code': 'approve_in_scope',
            'risk_band': 'low',
            'owner_gate': False,
            'constraints': {'aggression': int(aggression or 1)},
        }
    return {
        'decision': 'approve',
        'reason': 'local_delivery_adapter_approved_bounded_flow' if not demo_mode else 'demo_mode_local_adapter_approved_bounded_flow',
        'reason_code': 'approve_in_scope',
        'risk_band': 'low',
        'owner_gate': False,
        'constraints': {'aggression': int(aggression or 1)},
    }



def _mock_auditor_decision(*, aggression: int) -> Dict[str, Any]:
    return {
        'decision': 'approve',
        'reason': 'mock_delivery_adapter_approved_bounded_flow',
        'reason_code': 'approve_in_scope',
        'risk_band': 'low',
        'owner_gate': False,
        'constraints': {'aggression': int(aggression or 1)},
    }



def _mock_execution_result(approved_execution_spec: Dict[str, Any], *, effective_dry_run: bool) -> Dict[str, Any]:
    execution_truth = approved_execution_spec.get('execution_truth') if isinstance(approved_execution_spec.get('execution_truth'), dict) else {}
    preview = list(execution_truth.get('command_preview') or [])
    return {
        'status': 'dry-run' if effective_dry_run else 'mocked',
        'returncode': 0,
        'stdout': '',
        'stderr': '',
        'reason': 'mock_execution_adapter',
        'compiled_action': {
            'action_type': str(approved_execution_spec.get('action_type') or 'single_probe'),
            'compiler_tool_choice': str(approved_execution_spec.get('resolved_tool') or (preview[0] if preview else '')),
            'execution_mode': str(approved_execution_spec.get('execution_mode') or 'normalized'),
            'recipe_name': '',
        },
        'planned_commands': [preview] if preview else [],
        'executed_commands': [] if effective_dry_run or not preview else [preview],
        'execution_source': 'mock_adapter',
        'command_input_summary': dict(execution_truth.get('command_input_summary') or {}),
    }


def _append_aggression_normalization_step(
    chain: List[Dict[str, Any]],
    *,
    stage: str,
    before: int,
    after: int,
    reason: str,
    **details: Any,
) -> Dict[str, Any]:
    step: Dict[str, Any] = {
        'stage': str(stage or '').strip().lower(),
        'before': int(before),
        'after': int(after),
        'reason': str(reason or '').strip().lower(),
    }
    for key, value in details.items():
        if value in (None, '', [], {}):
            continue
        step[str(key)] = value
    chain.append(step)
    return step


def normalize_runtime_aggression(
    args: argparse.Namespace,
    *,
    cfg: Dict[str, Any],
    target: str,
    raw_action_spec: Dict[str, Any] | None = None,
    creds_policy: Dict[str, Any] | None = None,
    requested_aggression: int | None = None,
    existing_chain: List[Dict[str, Any]] | None = None,
    log_stage_fn=None,
) -> tuple[argparse.Namespace, Dict[str, Any]]:
    effective_args = _clone_namespace(args)
    chain: List[Dict[str, Any]] = [dict(item) for item in list(existing_chain or []) if isinstance(item, dict)]
    new_steps: List[Dict[str, Any]] = []
    requested = int(requested_aggression if requested_aggression is not None else getattr(args, 'aggression', 0) or 0)
    current = int(getattr(effective_args, 'aggression', requested) or requested)

    clamped = int(clamp_aggression(current))
    if clamped != current:
        new_steps.append(
            _append_aggression_normalization_step(
                chain,
                stage='global_clamp',
                before=current,
                after=clamped,
                reason='global_clamp',
            )
        )
        current = clamped

    target_host = extract_host_from_url(target)
    force_target_in_scope = bool(cfg.get('force_target_in_scope', False))
    target_in_scope = force_target_in_scope or (host_in_scope(target_host, load_scope_domains()) if target_host else False)
    out_scope_cap = int(cfg.get('out_of_scope_aggression_cap', cfg.get('out_of_scope_max_aggression', 1)) or 1)
    out_scope_allowed = int(cfg.get('out_of_scope_allowed_aggression', out_scope_cap) or out_scope_cap)
    effective_out_scope_cap = min(out_scope_cap, out_scope_allowed)
    if not target_in_scope and current > effective_out_scope_cap:
        new_steps.append(
            _append_aggression_normalization_step(
                chain,
                stage='out_of_scope_cap',
                before=current,
                after=effective_out_scope_cap,
                reason='out_of_scope_aggression_cap',
                cap=effective_out_scope_cap,
                host=target_host or target,
            )
        )
        current = effective_out_scope_cap

    policy_remap_note: Dict[str, Any] | None = None
    if isinstance(raw_action_spec, dict) and isinstance(creds_policy, dict):
        remapped, remap_note = remap_aggression_for_policy(raw_action_spec, creds_policy, current)
        if remapped != current:
            policy_remap_note = dict(remap_note or {}) if isinstance(remap_note, dict) else {}
            new_steps.append(
                _append_aggression_normalization_step(
                    chain,
                    stage='policy_remap',
                    before=current,
                    after=int(remapped),
                    reason=str((policy_remap_note or {}).get('reason') or 'policy_remap'),
                    details=policy_remap_note,
                )
            )
            current = int(remapped)

    effective_args.aggression = current

    if callable(log_stage_fn):
        for step in new_steps:
            stage = str(step.get('stage') or '')
            before = int(step.get('before', current) or 0)
            after = int(step.get('after', current) or 0)
            if stage == 'global_clamp':
                log_stage_fn('POLICY', 'aggression_clamp', 'warning', f'adjusted:{before}->{after}')
            elif stage == 'out_of_scope_cap':
                log_stage_fn('POLICY', 'out_of_scope_aggression_cap', 'warning', f"clamped:{before}->{after};cap={int(step.get('cap', after) or after)};host={str(step.get('host') or target)}")
            elif stage == 'policy_remap':
                log_stage_fn('POLICY', 'aggression_remapped', 'warning', f"requested={before};effective={after};reason={str(step.get('reason') or 'policy_remap')}")

    state: Dict[str, Any] = {
        'requested_aggression': requested,
        'effective_aggression': current,
        'target_host': str(target_host or ''),
        'target_in_scope': bool(target_in_scope),
        'chain': chain,
    }
    if policy_remap_note:
        state['policy_aggression_remap'] = policy_remap_note
    return effective_args, state


def _compact_prepared_execution_spec_for_auditor(spec: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(spec, dict):
        return {'error': 'invalid_prepared_execution_spec'}
    execution_plan = spec.get('execution_plan') if isinstance(spec.get('execution_plan'), list) else []
    compact_plan: List[Dict[str, Any]] = []
    for step in execution_plan[:3]:
        if not isinstance(step, dict):
            continue
        step_args = [str(x) for x in list(step.get('args') or [])[:12]]
        step_out = {
            'tool': str(step.get('tool') or ''),
            'role': str(step.get('role') or ''),
            'args': step_args,
            'args_truncated': len(list(step.get('args') or [])) > len(step_args),
        }
        if 'stdin_present' in step:
            step_out['stdin_present'] = bool(step.get('stdin_present', False))
            step_out['stdin_line_count'] = int(step.get('stdin_line_count', 0) or 0)
            step_out['stdin_char_count'] = int(step.get('stdin_char_count', 0) or 0)
            step_out['stdin_preview'] = str(step.get('stdin_preview') or '')
            step_out['stdin_preview_truncated'] = bool(step.get('stdin_preview_truncated', False))
        compact_plan.append(step_out)
    normalized_args = [str(x) for x in list(spec.get('normalized_args') or [])[:16]]
    return {
        'spec_version': str(spec.get('spec_version') or ''),
        'target': str(spec.get('target') or ''),
        'target_host': str(spec.get('target_host') or ''),
        'target_in_scope': bool(spec.get('target_in_scope', False)),
        'task_family': str(spec.get('task_family') or ''),
        'action_type': str(spec.get('action_type') or ''),
        'capability': str(spec.get('capability') or ''),
        'execution_mode': str(spec.get('execution_mode') or ''),
        'resolved_planner_profiles': list(spec.get('resolved_planner_profiles') or []),
        'resolved_tool': str(spec.get('resolved_tool') or ''),
        'tool_candidates': list(spec.get('tool_candidates') or []),
        'normalized_args': normalized_args,
        'normalized_args_truncated': len(list(spec.get('normalized_args') or [])) > len(normalized_args),
        'stdin_present': bool(spec.get('stdin_present', False)),
        'stdin_line_count': int(spec.get('stdin_line_count', 0) or 0),
        'stdin_char_count': int(spec.get('stdin_char_count', 0) or 0),
        'stdin_preview': str(spec.get('stdin_preview') or ''),
        'stdin_preview_truncated': bool(spec.get('stdin_preview_truncated', False)),
        'execution_plan_total': len(execution_plan),
        'execution_plan': compact_plan,
        'request_decoration': dict(spec.get('request_decoration') or {}) if isinstance(spec.get('request_decoration'), dict) else {},
        'scope_facts': dict(spec.get('scope_facts') or {}) if isinstance(spec.get('scope_facts'), dict) else {},
        'credentials_policy_snapshot': dict(spec.get('credentials_policy_snapshot') or {}) if isinstance(spec.get('credentials_policy_snapshot'), dict) else {},
        'arg_hosts_detected': list(spec.get('arg_hosts_detected') or []),
        'execution_plan_hosts_detected': list(spec.get('execution_plan_hosts_detected') or []),
        'all_hosts_detected': list(spec.get('all_hosts_detected') or []),
        'mismatched_hosts_detected': list(spec.get('mismatched_hosts_detected') or []),
        'target_host_match_status': str(spec.get('target_host_match_status') or ''),
        'request_shape_hygiene_status': str(spec.get('request_shape_hygiene_status') or ''),
        'request_shape_hygiene_reason': str(spec.get('request_shape_hygiene_reason') or ''),
        'request_shape_hygiene_source': str(spec.get('request_shape_hygiene_source') or ''),
        'compiler': dict(spec.get('compiler') or {}) if isinstance(spec.get('compiler'), dict) else {},
    }



def _request_shape_hygiene_record(prepared_execution_spec: Dict[str, Any]) -> Dict[str, Any]:
    spec = prepared_execution_spec if isinstance(prepared_execution_spec, dict) else {}
    return {
        'deterministic': True,
        'classification_timing': 'pre_auditor',
        'target_host': str(spec.get('target_host') or ''),
        'arg_hosts_detected': list(spec.get('arg_hosts_detected') or []),
        'execution_plan_hosts_detected': list(spec.get('execution_plan_hosts_detected') or []),
        'all_hosts_detected': list(spec.get('all_hosts_detected') or []),
        'mismatched_hosts_detected': list(spec.get('mismatched_hosts_detected') or []),
        'target_host_match_status': str(spec.get('target_host_match_status') or ''),
        'request_shape_hygiene_status': str(spec.get('request_shape_hygiene_status') or ''),
        'request_shape_hygiene_reason': str(spec.get('request_shape_hygiene_reason') or ''),
        'request_shape_hygiene_source': str(spec.get('request_shape_hygiene_source') or ''),
    }


def _log_request_shape_hygiene(*, log_stage_fn, request_shape_hygiene: Dict[str, Any], target_in_scope: bool) -> None:
    hygiene = request_shape_hygiene if isinstance(request_shape_hygiene, dict) else {}
    status_key = str(hygiene.get('request_shape_hygiene_status') or 'ambiguous').strip().lower()
    log_status = 'success' if status_key == 'clean' else 'warning'
    result = (
        f"status={status_key or 'unknown'};match={str(hygiene.get('target_host_match_status') or '')};"
        f"target_host={str(hygiene.get('target_host') or '-')};"
        f"detected={','.join(list(hygiene.get('all_hosts_detected') or [])) or '-'};"
        f"mismatched={','.join(list(hygiene.get('mismatched_hosts_detected') or [])) or '-'};"
        f"source={str(hygiene.get('request_shape_hygiene_source') or 'none')};"
        f"reason={str(hygiene.get('request_shape_hygiene_reason') or '')[:160]}"
    )
    log_stage_fn('INTERPRETER', 'request_shape_hygiene', log_status, result)
    mismatch = bool(list(hygiene.get('mismatched_hosts_detected') or []))
    if target_in_scope and mismatch:
        log_stage_fn(
            'POLICY',
            'request_shape_hygiene_diag',
            'warning',
            f"in_scope_target_with_cross_host_mismatch;target_host={str(hygiene.get('target_host') or '-')};mismatched={','.join(list(hygiene.get('mismatched_hosts_detected') or [])) or '-'}"
        )



def _compact_string_list(values: Any, limit: int = 4) -> List[str]:
    out: List[str] = []
    if not isinstance(values, list):
        return out
    for item in values:
        text = str(item or '').strip()
        if text:
            out.append(text)
        if len(out) >= limit:
            break
    return out



def _normalize_hypothesis_fanout_item(item: Any) -> Dict[str, Any]:
    if not isinstance(item, dict):
        return {}
    tool_preferences = dict(item.get('tool_preferences') or {}) if isinstance(item.get('tool_preferences'), dict) else {}
    prefer_tool = str(tool_preferences.get('prefer_tool') or item.get('prefer_tool') or item.get('tool') or '').strip().lower()
    normalized = {
        'hypothesis': str(item.get('hypothesis') or '').strip()[:220],
        'action_type': str(item.get('action_type') or '').strip().lower()[:80],
        'capability': str(item.get('capability') or '').strip().lower()[:80],
        'expected_signal': str(item.get('expected_signal') or '').strip()[:160],
        'evidence_goal': str(item.get('evidence_goal') or '').strip()[:160],
        'tool_preferences': ({'prefer_tool': prefer_tool} if prefer_tool else {}),
    }
    return {k: v for k, v in normalized.items() if v not in ('', {}, [])}



def _build_hypothesis_fanout(brain: Dict[str, Any], *, primary_hypothesis: str = '') -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in list(brain.get('sibling_hypotheses') or [])[:2]:
        item = _normalize_hypothesis_fanout_item(raw)
        if not item:
            continue
        key = (
            str(item.get('hypothesis') or '').strip().lower(),
            str(item.get('action_type') or '').strip().lower(),
            str(item.get('capability') or '').strip().lower(),
        )
        if not any(key):
            continue
        if primary_hypothesis and key[0] == primary_hypothesis.strip().lower():
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out



def _summarize_hypothesis_fanout(fanout: List[Dict[str, Any]]) -> Dict[str, Any]:
    capabilities = sorted({str(item.get('capability') or '').strip().lower() for item in fanout if str(item.get('capability') or '').strip()})
    action_types = sorted({str(item.get('action_type') or '').strip().lower() for item in fanout if str(item.get('action_type') or '').strip()})
    prefer_tools = sorted({str((item.get('tool_preferences') or {}).get('prefer_tool') or '').strip().lower() for item in fanout if isinstance(item.get('tool_preferences'), dict) and str((item.get('tool_preferences') or {}).get('prefer_tool') or '').strip()})
    return {
        'fanout_count': len(fanout),
        'capability_diversity': len(capabilities),
        'action_diversity': len(action_types),
        'preferred_tools': prefer_tools[:3],
        'capabilities': capabilities[:4],
        'action_types': action_types[:4],
    }



def generate_vector_family_motifs(*, task_family: str, capability: str, action_type: str) -> List[Dict[str, Any]]:
    fam = str(task_family or '').strip().lower()
    cap = str(capability or '').strip().lower()
    act = str(action_type or '').strip().lower()
    motifs: List[Dict[str, Any]] = []
    if fam in {'authz', 'auth_flow', 'workflow'}:
        motifs.extend([
            {'hypothesis': 'header/context differential sibling', 'action_type': 'variant_probe', 'capability': cap or 'http_probe', 'expected_signal': 'boundary-dependent header/status delta', 'evidence_goal': 'differential response', 'prefer_tool': 'curl'},
            {'hypothesis': 'state-transition boundary sibling', 'action_type': 'state_transition_probe', 'capability': 'state_transition', 'expected_signal': 'workflow/state divergence across actors', 'evidence_goal': 'state transition evidence', 'prefer_tool': 'curl'},
        ])
    elif fam in {'logic'}:
        motifs.extend([
            {'hypothesis': 'state precondition sibling', 'action_type': 'state_transition_probe', 'capability': cap or 'state_transition', 'expected_signal': 'precondition-dependent logic branch', 'evidence_goal': 'stateful differential', 'prefer_tool': 'curl'},
            {'hypothesis': 'idempotency / replay sibling', 'action_type': 'variant_probe', 'capability': cap or 'http_probe', 'expected_signal': 'repeat-sequence divergence', 'evidence_goal': 'sequence differential', 'prefer_tool': 'curl'},
        ])
    elif fam in {'client_input', 'input_tamper'}:
        motifs.extend([
            {'hypothesis': 'content-type parser sibling', 'action_type': 'variant_probe', 'capability': cap or 'http_probe', 'expected_signal': 'parser differential', 'evidence_goal': 'status/body divergence', 'prefer_tool': 'httpx'},
            {'hypothesis': 'encoding / body-shape sibling', 'action_type': 'variant_probe', 'capability': cap or 'http_probe', 'expected_signal': 'encoding-dependent parser delta', 'evidence_goal': 'response differential', 'prefer_tool': 'curl'},
        ])
    elif fam in {'redirect_trust'}:
        motifs.extend([
            {'hypothesis': 'host-context confusion sibling', 'action_type': 'variant_probe', 'capability': cap or 'http_probe', 'expected_signal': 'redirect target trust differential', 'evidence_goal': 'redirect destination delta', 'prefer_tool': 'curl'},
            {'hypothesis': 'scheme/authority rewrite sibling', 'action_type': 'variant_probe', 'capability': cap or 'http_probe', 'expected_signal': 'authority-dependent redirect behavior', 'evidence_goal': 'redirect behavior differential', 'prefer_tool': 'curl'},
        ])
    return [_normalize_hypothesis_fanout_item(item) for item in motifs[:2] if _normalize_hypothesis_fanout_item(item)]



def _merge_hypothesis_fanout(primary_hypothesis: str, explicit_fanout: List[Dict[str, Any]], motif_fanout: List[Dict[str, Any]], limit: int = 2) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for source in (explicit_fanout, motif_fanout):
        for item in source:
            key = (
                str(item.get('hypothesis') or '').strip().lower(),
                str(item.get('action_type') or '').strip().lower(),
                str(item.get('capability') or '').strip().lower(),
            )
            if not any(key):
                continue
            if primary_hypothesis and key[0] == primary_hypothesis.strip().lower():
                continue
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= limit:
                return merged
    return merged[:limit]



def _compact_mapping(value: Any, *, value_limit: int = 6, string_limit: int = 120) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, Any] = {}
    for key, raw in list(value.items())[:value_limit]:
        k = str(key or '').strip()
        if not k:
            continue
        if isinstance(raw, list):
            items = _compact_string_list(raw, limit=4)
            if items:
                out[k] = items
        elif isinstance(raw, dict):
            nested: Dict[str, Any] = {}
            for nk, nv in list(raw.items())[:4]:
                nested_key = str(nk or '').strip()
                nested_val = str(nv or '').strip()
                if nested_key and nested_val:
                    nested[nested_key] = nested_val[:string_limit]
            if nested:
                out[k] = nested
        else:
            text = str(raw or '').strip()
            if text:
                out[k] = text[:string_limit]
    return out



def compact_planner_hints_for_brain(planner_hints: Dict[str, Any] | None) -> Dict[str, Any]:
    hints = planner_hints if isinstance(planner_hints, dict) else {}
    return {
        'preferred_vectors_for_target': _compact_string_list(hints.get('preferred_vectors_for_target'), limit=3),
        'deprioritized_task_families': _compact_string_list(hints.get('deprioritized_task_families'), limit=2),
        'ambiguities': _compact_string_list(hints.get('ambiguities'), limit=2),
        'interpretation_conflicts': _compact_string_list(hints.get('interpretation_conflicts'), limit=2),
        'target_profile': {
            'task_family_seeds': _compact_string_list(((hints.get('target_profile') or {}).get('task_family_seeds') if isinstance(hints.get('target_profile'), dict) else []), limit=4),
            'preferred_vectors_for_target': _compact_string_list(((hints.get('target_profile') or {}).get('preferred_vectors_for_target') if isinstance(hints.get('target_profile'), dict) else []), limit=3),
            'notes': _compact_string_list(((hints.get('target_profile') or {}).get('notes') if isinstance(hints.get('target_profile'), dict) else []), limit=2),
        },
        'task_family_context': _compact_mapping(hints.get('task_family_context'), value_limit=4, string_limit=80),
    }



def compact_intent_runtime_context_for_brain(intent_runtime_context: Dict[str, Any] | None) -> Dict[str, Any]:
    ctx = intent_runtime_context if isinstance(intent_runtime_context, dict) else {}
    return {
        'experiment_intent_id': str(ctx.get('experiment_intent_id') or '')[:80],
        'capability_candidates': _compact_string_list(ctx.get('capability_candidates'), limit=4),
        'recommended_action_types': _compact_string_list(ctx.get('recommended_action_types'), limit=4),
        'hypothesis_candidates': _compact_string_list(ctx.get('hypothesis_candidates'), limit=3),
        'open_questions': _compact_string_list(ctx.get('open_questions'), limit=3),
        'planner_constraints': _compact_mapping(ctx.get('planner_constraints'), value_limit=5, string_limit=80),
        'planner_preferences': _compact_mapping(ctx.get('planner_preferences'), value_limit=5, string_limit=80),
        'planning_ladder': _compact_mapping(ctx.get('planning_ladder'), value_limit=5, string_limit=80),
        'target_surface_rationale': _compact_string_list(ctx.get('target_surface_rationale'), limit=4),
    }



def compact_tooling_summary_for_brain(*, profiles: List[str], allowed_tools: List[str], preferred_tools: List[str]) -> Dict[str, Any]:
    shortlist = preferred_tools[:6] if preferred_tools else allowed_tools[:8]
    return {
        'resolved_planner_profiles': list(profiles or []),
        'allowed_tool_count': int(len(allowed_tools or [])),
        'preferred_tools': list(preferred_tools[:6] if preferred_tools else []),
        'tool_shortlist': list(shortlist),
    }



def build_brain_contract_hint() -> str:
    return (
        '{"intent":"...","target":"...","task_family":"...","resolved_planner_profiles":["core"],'
        '"action_type":"single_probe|differential_probe|confirmatory_probe|enumeration_probe|variant_probe|fingerprint_probe|state_transition_probe",'
        '"capability":"...","tool":"optional_planner_allowed_tool","tool_preferences":{"prefer_tool":"optional_planner_allowed_tool"},'
        '"tool_candidates":["optional_planner_allowed_tool"],"args":["..."],'
        '"probe_recipe":{"comparison_mode":"...","variant_count":1,"evidence_goal":"..."},'
        '"constraints":{"aggression":1},"hypothesis":"...","why_now":"...","planner_alignment":"aligned|override|unknown",'
        '"planner_override_reason":"...","expected_signal":"...","evidence_goal":"...","next_if_positive":"...",'
        '"next_if_negative":"...","redundancy_risk":"low|medium|high","experiment_intent_id":"...",'
        '"sibling_hypotheses":[{"hypothesis":"...","action_type":"variant_probe","capability":"...","expected_signal":"...","evidence_goal":"...","prefer_tool":"optional_planner_allowed_tool"}],'
        '"planner_constraints":{},"planner_preferences":{}}'
    )



def _load_exploit_motif_hints(task_family: str, limit: int = 3) -> List[Dict[str, Any]]:
    path = rsp('exploit-motif-memory.json')
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding='utf-8'))
            items = [item for item in list(payload.get('items') or []) if isinstance(item, dict)]
            filtered = [item for item in items if str(item.get('task_family') or '').strip().lower() == str(task_family or '').strip().lower()]
            return filtered[:limit]
    except Exception:
        pass
    return []



def build_brain_base_prompt(
    *,
    args: argparse.Namespace,
    task_family: str,
    contextual_profiles: List[str],
    allowed_tools_sorted: List[str],
    preferred_tools: List[str],
    planner_hints: Dict[str, Any],
    intent_runtime_context: Dict[str, Any],
    experimental_mode: bool,
) -> str:
    compact_hints = compact_planner_hints_for_brain(planner_hints)
    compact_intent = compact_intent_runtime_context_for_brain(intent_runtime_context)
    tooling_summary = compact_tooling_summary_for_brain(
        profiles=contextual_profiles,
        allowed_tools=allowed_tools_sorted,
        preferred_tools=preferred_tools,
    )
    rules = (
        "You are BRAIN in RAVEN-CLAW strict pipeline. In-scope security research only. "
        "Return one valid action specification, not prose. "
        "Hard rules: capability-first planning; bounded non-destructive probing; one primary target; no shell helpers, pseudo-tools, placeholders, or meta-tools (forbidden: exec/execute/shell/command/cmd/echo/cat/ls/bash/python3). "
        "Args must be hermetic literal tool arguments only. Never include pipes, semicolons, redirects, command substitution, chained commands, grep/xargs fragments, or shell syntax inside args/tool_chain args. "
        "Use one action_type from single_probe|differential_probe|confirmatory_probe|enumeration_probe|variant_probe|fingerprint_probe|state_transition_probe with a matching capability. Keep probe_recipe explicit. Tool choice is optional when capability + task family already determine execution. "
    )
    creative = (
        "EXPERIMENTAL MODE ON: prefer high-skill, low-noise ideas: parser differentials, protocol edges, authz canaries, state-machine/idempotency checks, and subtle header/context interactions. Avoid generic scanner-like probes. "
        if experimental_mode else
        ""
    )
    task_truth = (
        f"TaskTruth: objective={args.objective}; target={args.target}; aggression={args.aggression}; family={task_family or 'generic'}. "
        + (f"task_success={args.task_success_criteria}. " if str(getattr(args, 'task_success_criteria', '') or '').strip() else "")
        + (f"campaign_success={args.campaign_success_criteria}. " if str(getattr(args, 'campaign_success_criteria', '') or '').strip() else "")
        + (f"checks={args.acceptance_checks}. " if str(getattr(args, 'acceptance_checks', '') or '').strip() else "")
        + (f"evidence={args.evidence_required}. " if str(getattr(args, 'evidence_required', '') or '').strip() else "")
    )
    vector_family_motifs = generate_vector_family_motifs(
        task_family=task_family,
        capability=str((compact_intent.get('capability_candidates') or [''])[0] if list(compact_intent.get('capability_candidates') or []) else ''),
        action_type=str((compact_intent.get('recommended_action_types') or [''])[0] if list(compact_intent.get('recommended_action_types') or []) else ''),
    )
    exploit_motif_hints = _load_exploit_motif_hints(task_family, limit=3)
    compact_sections = (
        f"ExperimentIntentContext: {json.dumps(compact_intent, ensure_ascii=False)}. "
        f"PlannerHints: {json.dumps(compact_hints, ensure_ascii=False)}. "
        f"ExploitMotifs: {json.dumps(exploit_motif_hints, ensure_ascii=False)}. "
        f"ToolingSummary: {json.dumps(tooling_summary, ensure_ascii=False)}. "
        f"VectorFamilyMotifs: {json.dumps(vector_family_motifs, ensure_ascii=False)}. "
    )
    guidance = (
        "Treat planner hints as priority guidance. Prefer ExperimentIntentContext capability/action candidates unless you have a compact planner_override_reason. "
        "You may include up to 2 bounded sibling_hypotheses. If you specify a tool, it must be planner-allowed here. Prefer the smallest sufficient realization. "
    )
    return rules + creative + task_truth + compact_sections + guidance
    if target_in_scope and status_key == 'cross_host_mismatch':
        log_stage_fn(
            'POLICY',
            'request_shape_hygiene_diag',
            'warning',
            f"in_scope_target_with_cross_host_mismatch:target_host={str(hygiene.get('target_host') or '-')};mismatched={','.join(list(hygiene.get('mismatched_hosts_detected') or [])) or '-'};source={str(hygiene.get('request_shape_hygiene_source') or 'none')}",
        )


def _build_auditor_context_summary(
    *,
    args: argparse.Namespace,
    target_in_scope: bool,
    recent_runtime_summary: str,
    planner_hints: Dict[str, Any],
    brain_reasoning: Dict[str, Any],
    semantic_loss_policy: Dict[str, Any],
    intent_runtime_context: Dict[str, Any],
    request_shape_hygiene: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    planner_target_profile = dict(planner_hints.get('target_profile') or {}) if isinstance(planner_hints.get('target_profile'), dict) else {}
    hygiene = request_shape_hygiene if isinstance(request_shape_hygiene, dict) else {}
    return {
        'objective': truncate_text(str(args.objective or ''), 220),
        'target': str(args.target or ''),
        'task_family': str(getattr(args, 'task_family', '') or ''),
        'aggression': int(getattr(args, 'aggression', 1) or 1),
        'target_in_scope': bool(target_in_scope),
        'owner_override': bool(getattr(args, 'owner_override', False)),
        'owner_approved_auth': bool(getattr(args, 'owner_approved_auth', False)),
        'task_success_criteria': truncate_text(str(getattr(args, 'task_success_criteria', '') or ''), 220),
        'campaign_success_criteria': truncate_text(str(getattr(args, 'campaign_success_criteria', '') or ''), 220),
        'acceptance_checks': truncate_text(str(getattr(args, 'acceptance_checks', '') or ''), 160),
        'evidence_required': truncate_text(str(getattr(args, 'evidence_required', '') or ''), 160),
        'recent_runtime_summary': truncate_text(str(recent_runtime_summary or ''), 240),
        'brain_reasoning_summary': {
            'hypothesis': truncate_text(str(brain_reasoning.get('hypothesis') or ''), 180),
            'why_now': truncate_text(str(brain_reasoning.get('why_now') or ''), 180),
            'expected_signal': truncate_text(str(brain_reasoning.get('expected_signal') or ''), 180),
            'evidence_goal': truncate_text(str(brain_reasoning.get('evidence_goal') or ''), 180),
            'planner_alignment': str(brain_reasoning.get('planner_alignment') or 'unknown'),
            'redundancy_risk': str(brain_reasoning.get('redundancy_risk') or 'unknown'),
        },
        'deterministic_scope_gate': {
            'target_in_scope': bool(target_in_scope),
            'requested_aggression': int(getattr(args, 'aggression', 1) or 1),
        },
        'planner_context_summary': {
            'preferred_vectors_for_target': list((planner_hints.get('preferred_vectors_for_target') or [])[:4]),
            'deprioritized_task_families': list((planner_hints.get('deprioritized_task_families') or [])[:4]),
            'ambiguities': list((planner_hints.get('ambiguities') or [])[:3]),
            'interpretation_conflicts': list((planner_hints.get('interpretation_conflicts') or [])[:3]),
            'target_profile': {
                'target_type': planner_target_profile.get('target_type'),
                'surface_keywords': list((planner_target_profile.get('surface_keywords') or [])[:5]),
                'family_preferences': list((planner_target_profile.get('family_preferences') or [])[:5]),
            },
            'intent_runtime_context': {
                'experiment_intent_id': str(intent_runtime_context.get('experiment_intent_id') or ''),
                'capability_candidates': list((intent_runtime_context.get('capability_candidates') or [])[:4]),
                'recommended_action_types': list((intent_runtime_context.get('recommended_action_types') or [])[:4]),
            },
        },
        'semantic_loss_policy': dict(semantic_loss_policy or {}),
        'request_shape_hygiene': {
            'deterministic': bool(hygiene.get('deterministic', False)),
            'classification_timing': str(hygiene.get('classification_timing') or ''),
            'target_host_match_status': str(hygiene.get('target_host_match_status') or ''),
            'request_shape_hygiene_status': str(hygiene.get('request_shape_hygiene_status') or ''),
            'request_shape_hygiene_reason': str(hygiene.get('request_shape_hygiene_reason') or ''),
            'request_shape_hygiene_source': str(hygiene.get('request_shape_hygiene_source') or ''),
            'mismatched_hosts_detected': list(hygiene.get('mismatched_hosts_detected') or []),
        },
    }



def _build_auditor_prompt(*, prepared_execution_spec: Dict[str, Any], context_summary: Dict[str, Any]) -> str:
    return (
        "You are AUDITOR in RAVEN-CLAW strict runtime pipeline. "
        "You are a deterministic policy gate, not a planner. "
        "Audit only the CANONICAL_PREPARED_EXECUTION_SPEC below. Do not invent steps, tools, or reinterpret the objective. "
        "If the CANONICAL_PREPARED_EXECUTION_SPEC block is present, do not claim it is missing. "
        "Approve only when the prepared step is clearly in-scope, low-risk for the requested aggression, and does not require owner review. "
        "Use owner_approval_required for uncertainty, auth sensitivity, elevated risk, or policy ambiguity. "
        "Reject only on clear invalidity or clear policy violation. "
        "Return compact machine-friendly JSON only. "
        "Prefer short reason codes from this set when applicable: approve_in_scope, reject_invalid_contract, reject_policy_gate, reject_out_of_scope, owner_approval_required_risk, owner_approval_required_auth, owner_approval_required_uncertain, owner_approval_required_policy.\n"
        f"CANONICAL_PREPARED_EXECUTION_SPEC={json.dumps(prepared_execution_spec, ensure_ascii=False)}\n"
        f"DECISION_CONTEXT={json.dumps(context_summary, ensure_ascii=False)}"
    )

OPENCLAW_BIN = shutil.which('openclaw') or '/usr/local/bin/openclaw'
LOGDASH_VENV_PY = LOGDASH_DIR / '.venv' / 'bin' / 'python'
LOG_EVENT_SCRIPT = LOGDASH_DIR / 'log_event.py'


def log_event(
    tor: str,
    decision: str,
    status: str,
    result: str,
    actor: str | None = None,
    row_type: str = 'entry',
    highlight: bool = False,
) -> None:
    if not (LOG_EVENT_SCRIPT.exists() and LOGDASH_VENV_PY.exists()):
        return
    try:
        cmd = [
            str(LOGDASH_VENV_PY),
            str(LOG_EVENT_SCRIPT),
            '--tor', tor,
            '--decision', decision,
            '--status', status,
            '--result', (result if result else status),
            '--row-type', row_type,
        ]
        if actor:
            cmd.extend(['--agent', actor])
        if highlight:
            cmd.append('--highlight')
        subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception:
        pass


def log_stage(stage: str, decision: str, status: str, result: str) -> None:
    log_event('PIPELINE', decision, status, result, actor=stage)



def load_planner_hints(target: str = '', task_family: str = '', limit_vectors: int = 5, limit_ambiguities: int = 3, limit_conflicts: int = 3, selected_campaign_key: str = '') -> Dict[str, Any]:
    resolved_key = resolve_campaign_key(selected_campaign_key)
    return _load_planner_hints(
        target=target,
        task_family=task_family,
        limit_vectors=limit_vectors,
        limit_ambiguities=limit_ambiguities,
        limit_conflicts=limit_conflicts,
        selected_campaign_key=resolved_key,
    )



def policy_gate(brain: Dict[str, Any], target: str, owner_approved_auth: bool) -> Dict[str, Any]:
    return _policy_gate(
        brain,
        target,
        owner_approved_auth,
        load_credentials_runtime_policy_fn=load_credentials_runtime_policy,
    )




def _recent_high_context(recent_context: List[Dict[str, Any]]) -> bool:
    for item in (recent_context or [])[-6:]:
        if not isinstance(item, dict):
            continue
        analysis = item.get('analysis') if isinstance(item.get('analysis'), dict) else {}
        risk = str(analysis.get('risk') or '').lower()
        if risk in {'high', 'critical'}:
            return True
        status = str(item.get('status') or '').lower()
        if status in {'failed', 'error'}:
            return True
        out = (str(item.get('stdout_preview') or '') + ' ' + str(item.get('stderr_preview') or '')).lower()
        if any(k in out for k in ['xss','idor','sqli','sql injection','token leak','bypass','unauthorized']):
            return True
    return False




def fallback_brain_action(objective: str, target: str, aggression: int, task_family: str = '', recent_context: List[Dict[str, Any]] | None = None, intent_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _fallback_brain_action(
        objective,
        target,
        aggression,
        task_family=task_family,
        recent_context=recent_context,
        intent_context=intent_context,
        contextual_brain_tooling_fn=contextual_brain_tooling,
    )


def preferred_tools_for_task_family(task_family: str, objective: str, recent_context: List[Dict[str, Any]] | None = None, capability_candidates: List[str] | None = None, recommended_action_types: List[str] | None = None) -> List[str]:
    return _preferred_tools_for_task_family(
        task_family,
        objective,
        recent_context=recent_context,
        capability_candidates=capability_candidates,
        recommended_action_types=recommended_action_types,
        contextual_brain_tooling_fn=contextual_brain_tooling,
    )


def apply_intent_guidance_to_brain(brain: Dict[str, Any], intent_context: Dict[str, Any], *, objective: str, target: str, aggression: int, task_family: str = '', recent_context: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    return _apply_intent_guidance_to_brain(
        brain,
        intent_context,
        objective=objective,
        target=target,
        aggression=aggression,
        task_family=task_family,
        recent_context=recent_context,
        preferred_tools_for_task_family_fn=preferred_tools_for_task_family,
    )


def enforce_brain_tool_whitelist(brain: Dict[str, Any], objective: str, target: str, aggression: int, task_family: str = '', recent_context: List[Dict[str, Any]] | None = None, execution_mode: str = 'normalized') -> tuple[Dict[str, Any], Dict[str, Any] | None]:
    return _enforce_brain_tool_whitelist(
        brain,
        objective,
        target,
        aggression,
        task_family=task_family,
        recent_context=recent_context,
        execution_mode=execution_mode,
        contextual_brain_tooling_fn=contextual_brain_tooling,
        fallback_brain_action_fn=fallback_brain_action,
    )

def _decouple_semantic_action_from_realization(spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(spec or {})
    execution_mode = str(out.get('execution_mode') or 'normalized').strip().lower() or 'normalized'
    if execution_mode != 'normalized':
        return out
    if list(out.get('tool_chain') or []):
        return out
    if str(out.get('recipe_name') or '').strip():
        return out
    action_type = str(out.get('action_type') or '').strip().lower()
    capability = str(out.get('capability') or '').strip().lower()
    task_family = str(out.get('task_family') or '').strip().lower()
    profiles = list(out.get('resolved_planner_profiles') or [])
    explicit_tool = str(out.get('tool') or '').strip().lower()
    if not explicit_tool:
        return out
    tool_preferences = dict(out.get('tool_preferences') or {}) if isinstance(out.get('tool_preferences'), dict) else {}
    preferred_tool = str(tool_preferences.get('prefer_tool') or '').strip().lower() or explicit_tool
    if not can_resolve_tool_from_capability(
        capability,
        action_type=action_type,
        task_family=task_family,
        requested_profiles=profiles or None,
        preferred_tool=preferred_tool,
        tool_candidates=list(out.get('tool_candidates') or []) or [explicit_tool],
    ):
        return out
    tool_preferences['prefer_tool'] = preferred_tool
    out['tool_preferences'] = tool_preferences
    out['tool'] = ''
    if list(out.get('tool_candidates') or []):
        out['tool_candidates'] = [x for x in list(out.get('tool_candidates') or []) if str(x or '').strip().lower() != explicit_tool]
    out['realization_decoupled'] = True
    out['realization_hint_source'] = 'brain_tool_demoted_to_preference'
    return out



def _build_raw_action_spec(
    brain: Dict[str, Any],
    *,
    args: argparse.Namespace,
    task_family: str,
    execution_mode: str,
    intent_runtime_context: Dict[str, Any],
) -> Dict[str, Any]:
    action_type = str(brain.get('action_type') or '').strip().lower()
    primary_hypothesis = str(brain.get('hypothesis') or '').strip()
    explicit_hypothesis_fanout = _build_hypothesis_fanout(brain, primary_hypothesis=primary_hypothesis)
    motif_hypothesis_fanout = generate_vector_family_motifs(
        task_family=task_family,
        capability=str(brain.get('capability') or ACTION_TYPE_TO_CAPABILITY.get(action_type, 'http_probe')),
        action_type=action_type,
    )
    hypothesis_fanout = _merge_hypothesis_fanout(primary_hypothesis, explicit_hypothesis_fanout, motif_hypothesis_fanout, limit=2)
    raw = {
        'action_type': brain.get('action_type'),
        'capability': brain.get('capability') or ACTION_TYPE_TO_CAPABILITY.get(action_type, 'http_probe'),
        'experiment_shape': brain.get('experiment_shape') or ACTION_TYPE_TO_EXPERIMENT_SHAPE.get(action_type, 'single_step'),
        'target_cardinality': brain.get('target_cardinality') or 'single',
        'tool': brain.get('tool'),
        'tool_candidates': list(brain.get('tool_candidates') or []),
        'tool_preferences': dict(brain.get('tool_preferences') or {}) if isinstance(brain.get('tool_preferences'), dict) else {},
        'tool_chain': list(brain.get('tool_chain') or []) if isinstance(brain.get('tool_chain'), list) else [],
        'args': list(brain.get('args') or []),
        'probe_recipe': dict(brain.get('probe_recipe') or {}) if isinstance(brain.get('probe_recipe'), dict) else {},
        'constraints': dict(brain.get('constraints') or {}) if isinstance(brain.get('constraints'), dict) else {},
        'task_family': task_family,
        'resolved_planner_profiles': list(brain.get('resolved_planner_profiles') or []),
        'target': args.target,
        'execution_mode': execution_mode,
        'recipe_name': str(brain.get('recipe_name') or ''),
        'experiment_intent_id': str(brain.get('experiment_intent_id') or intent_runtime_context.get('experiment_intent_id') or ''),
        'planner_constraints': dict(brain.get('planner_constraints') or intent_runtime_context.get('planner_constraints') or {}) if isinstance(brain.get('planner_constraints') or intent_runtime_context.get('planner_constraints') or {}, dict) else {},
        'planner_preferences': dict(brain.get('planner_preferences') or intent_runtime_context.get('planner_preferences') or {}) if isinstance(brain.get('planner_preferences') or intent_runtime_context.get('planner_preferences') or {}, dict) else {},
        'capability_candidates': list(brain.get('capability_candidates') or intent_runtime_context.get('capability_candidates') or []),
        'recommended_action_types': list(brain.get('recommended_action_types') or intent_runtime_context.get('recommended_action_types') or []),
        'hypothesis_candidates': list(brain.get('hypothesis_candidates') or intent_runtime_context.get('hypothesis_candidates') or []),
        'primary_hypothesis': primary_hypothesis,
        'hypothesis_fanout': hypothesis_fanout,
        'hypothesis_fanout_count': len(hypothesis_fanout),
        'hypothesis_fanout_summary': _summarize_hypothesis_fanout(hypothesis_fanout),
        'hypothesis_fanout_source': 'explicit_plus_motif' if explicit_hypothesis_fanout and motif_hypothesis_fanout else ('explicit' if explicit_hypothesis_fanout else ('motif_backfill' if motif_hypothesis_fanout else 'none')),
    }
    return _decouple_semantic_action_from_realization(raw)



def _build_initial_output(
    *,
    correlation_id: str,
    args: argparse.Namespace,
    cfg: Dict[str, Any],
    experimental_mode: bool,
    execution_mode: str,
    planner_hints: Dict[str, Any],
    brain: Dict[str, Any],
    gate: Dict[str, Any],
    semantic_loss_policy: Dict[str, Any],
    semantic_loss_rereview_required: bool,
    prepared_execution_spec: Dict[str, Any],
    action_spec: Dict[str, Any],
    intent_runtime_context: Dict[str, Any],
    delivery_profile: Dict[str, Any],
    delivery_notes: Dict[str, Any],
) -> Dict[str, Any]:
    output: Dict[str, Any] = {
        'correlation_id': correlation_id,
        'aggression_level': args.aggression,
        'runtime_task': {
            'target': args.target,
            'task_family': str(getattr(args, 'task_family', '') or ''),
            'intent_class': str(getattr(args, 'task_family', '') or ''),
            'action_type': str(action_spec.get('action_type') or brain.get('action_type') or 'single_probe'),
            'priority_score': 1.0,
            'cost_band': str(getattr(args, 'cost_band', '') or ''),
            'recommended_tools': [],
            'acceptance_checks': str(getattr(args, 'acceptance_checks', '') or ''),
            'evidence_required': str(getattr(args, 'evidence_required', '') or ''),
            'experiment_intent_id': str(intent_runtime_context.get('experiment_intent_id') or ''),
            'capability_candidates': list(intent_runtime_context.get('capability_candidates') or []),
            'recommended_action_types': list(intent_runtime_context.get('recommended_action_types') or []),
            'hypothesis_candidates': list(intent_runtime_context.get('hypothesis_candidates') or []),
            'planner_constraints': dict(intent_runtime_context.get('planner_constraints') or {}),
            'planner_preferences': dict(intent_runtime_context.get('planner_preferences') or {}),
            'open_questions': list(intent_runtime_context.get('open_questions') or []),
        },
        'settings': {
            'verbose_commands': bool(cfg.get('verbose_commands', True)),
            'enable_analysis': bool(cfg.get('enable_analysis', False)),
            'enable_light': bool(cfg.get('enable_light', False)),
            'experimental_payloads': experimental_mode,
            'execution_mode': execution_mode,
            'analysis_min_bytes': int(cfg.get('analysis_min_bytes', 0) or 0),
            'runtime_mode': str(delivery_profile.get('runtime_mode') or 'local'),
            'forced_dry_run': bool(delivery_profile.get('forced_dry_run', False)),
        },
        'planner_hints': planner_hints,
        'brain': brain,
        'brain_reasoning_summary': {
            'action_type': str(brain.get('action_type') or 'single_probe'),
            'planner_alignment': str(brain.get('planner_alignment') or 'unknown'),
            'redundancy_risk': str(brain.get('redundancy_risk') or 'unknown'),
            'expected_signal': str(brain.get('expected_signal') or '')[:180],
        },
        'policy_gate': gate,
        'semantic_loss_policy': semantic_loss_policy,
        'semantic_loss_rereview_required': semantic_loss_rereview_required,
        'semantic_loss_rereview_completed': False,
        'semantic_loss_rereview_decision': '',
        'request_shape_hygiene': _request_shape_hygiene_record(prepared_execution_spec),
        'delivery_profile': dict(delivery_profile or {}),
        'delivery_notes': dict(delivery_notes or {}),
        'integration_adapters': {
            'runtime_mode': str(delivery_profile.get('runtime_mode') or 'local'),
            'brain': dict((((delivery_profile.get('adapters') or {}) if isinstance(delivery_profile.get('adapters'), dict) else {}).get('brain') or {})),
            'auditor': dict((((delivery_profile.get('adapters') or {}) if isinstance(delivery_profile.get('adapters'), dict) else {}).get('auditor') or {})),
            'execution': dict((((delivery_profile.get('adapters') or {}) if isinstance(delivery_profile.get('adapters'), dict) else {}).get('execution') or {})),
        },
        'auditor': None,
        'auditor_raw_decision': None,
        'approval_transform_chain': [],
        'approval_source': '',
        'final_approval_decision': '',
        'prepared_execution_spec': prepared_execution_spec,
        'approved_execution_spec': None,
        'planned_command': None,
        'engine': None,
        'analysis': None,
        'light': None,
    }
    if cfg.get('verbose_commands', True):
        preview_args = list(action_spec.get('args', []) or [])
        output['planned_command'] = [str(action_spec.get('tool') or ''), *[str(a) for a in preview_args]]
    return output



def _finalize_engine_output(
    *,
    output: Dict[str, Any],
    engine_res: Dict[str, Any],
    auditor: Dict[str, Any],
    brain: Dict[str, Any],
    execution_mode: str,
) -> tuple[str, str, bool]:
    if isinstance(engine_res.get('compiled_action'), dict):
        output['engine_compiler'] = {
            'action_type': str(engine_res['compiled_action'].get('action_type') or 'single_probe'),
            'compiler_strategy': str(engine_res['compiled_action'].get('compiler_strategy') or ''),
            'compiler_tool_choice': str(engine_res['compiled_action'].get('compiler_tool_choice') or ''),
            'compiler_tool_choice_source': str(engine_res['compiled_action'].get('compiler_tool_choice_source') or ''),
            'compiler_variant_count': int(engine_res['compiled_action'].get('compiler_variant_count', 1) or 1),
            'recipe_name': str(engine_res['compiled_action'].get('recipe_name') or ''),
            'execution_mode': str(engine_res['compiled_action'].get('execution_mode') or execution_mode),
            'semantic_loss_detected': bool(engine_res['compiled_action'].get('semantic_loss_detected', False)),
            'normalization_reason': str(engine_res['compiled_action'].get('normalization_reason') or ''),
            'semantic_loss_policy': dict(engine_res['compiled_action'].get('semantic_loss_policy') or {}),
        }
    output['engine_status_normalized'] = normalize_engine_status(engine_res.get('status'))
    stdout_snip = engine_res.get('stdout') or ''
    stderr_snip = engine_res.get('stderr') or ''
    error_flag = (
        (engine_res.get('status') or '').lower() in {'failed', 'error', 'timeout'}
        or (engine_res.get('returncode') not in (0, None))
    )
    summary_base = (stdout_snip or stderr_snip or str(engine_res.get('reason') or '').strip())
    if not summary_base:
        rc = engine_res.get('returncode')
        est = engine_res.get('status')
        summary_base = f"execution failed with no stderr/stdout (status={est}, rc={rc})" if est in {'failed','error','blocked'} else str(est or 'no output')
    summary_text = summary_base[:240]
    final_status = normalize_pipeline_status(engine_res.get('status'), auditor.get('decision'), error_flag)
    log_stage('ENGINE', str((engine_res.get('compiled_action') or {}).get('compiler_tool_choice') or brain.get('tool') or 'engine_execute'), engine_res.get('status') or 'unknown', summary_text)
    return final_status, summary_text, error_flag



def execute_flow(
    args: argparse.Namespace,
    cfg: Dict[str, Any],
    recent_context: List[Dict[str, Any]],
    context_limit: int,
) -> tuple[Dict[str, Any], str, str]:
    delivery_profile = resolve_delivery_profile(explicit_mode=str(getattr(args, 'runtime_mode', '') or cfg.get('runtime_mode') or ''))
    seed_args, cfg, delivery_notes = apply_delivery_profile_to_pipeline(args, cfg, delivery_profile=delivery_profile)
    prebrain_args, prebrain_aggression_state = normalize_runtime_aggression(
        seed_args,
        cfg=cfg,
        target=str(getattr(seed_args, 'target', '') or ''),
        log_stage_fn=log_stage,
    )
    task_family = str(getattr(prebrain_args, 'task_family', '') or '')
    host_bound_recent_context = filter_recent_context_for_target(recent_context, target=prebrain_args.target, limit=max(6, int(context_limit or 0)))
    planner_hints = load_planner_hints(target=prebrain_args.target, task_family=task_family, limit_vectors=5, limit_ambiguities=3, limit_conflicts=3)
    intent_runtime_context = _merge_intent_runtime_context(prebrain_args, planner_hints, target=prebrain_args.target)
    explicit_success_semantics = _coerce_json_dict(getattr(prebrain_args, 'success_semantics_json', ''))
    json_retries = max(0, int(cfg.get('json_contract_retries', 1) or 1))
    experimental_mode = bool(cfg.get('experimental_payloads', False))
    strict_deterministic = bool(cfg.get('strict_deterministic', True))
    execution_mode = str(cfg.get('execution_mode', 'normalized') or 'normalized').strip().lower()
    if execution_mode not in {'normalized', 'faithful'}:
        execution_mode = 'normalized'
    stage_timers: Dict[str, float] = {}
    prompt_token_budget = max(0, int(cfg.get("prompt_token_budget", 900) or 0))
    auditor_prompt_token_budget = max(0, int(cfg.get("auditor_prompt_token_budget", max(prompt_token_budget, 900)) or 0))
    contextual_tooling = contextual_brain_tooling(task_family)
    brain_adapter_meta: Dict[str, Any] = {}
    try:
        log_stage('BRAIN', 'brain_wait', 'in_progress', 'waiting_for_brain_response timeout=60s')
        _t0 = time.perf_counter()
        allowed_tools_sorted = list(contextual_tooling.get('tools') or list(get_runtime_brain_allowed_tools(contextual_tooling.get('profiles') or None)))
        preferred_tools = preferred_tools_for_task_family(
            task_family,
            prebrain_args.objective,
            recent_context=host_bound_recent_context,
            capability_candidates=list(intent_runtime_context.get('capability_candidates') or []),
            recommended_action_types=list(intent_runtime_context.get('recommended_action_types') or []),
        )

        def _external_brain_runner() -> Dict[str, Any]:
            return ask_json(
                'brain',
                base_prompt=build_brain_base_prompt(
                    args=prebrain_args,
                    task_family=task_family,
                    contextual_profiles=list(contextual_tooling.get('profiles') or []),
                    allowed_tools_sorted=allowed_tools_sorted,
                    preferred_tools=preferred_tools,
                    planner_hints=planner_hints,
                    intent_runtime_context=intent_runtime_context,
                    experimental_mode=experimental_mode,
                ),
                contract_hint=build_brain_contract_hint(),
                retries=json_retries,
                timeout=60,
                prompt_token_budget=prompt_token_budget
            )

        def _local_brain_runner() -> Dict[str, Any]:
            if bool(delivery_profile.get('demo_mode')):
                return _mock_brain_action(
                    prebrain_args.objective,
                    prebrain_args.target,
                    int(prebrain_args.aggression),
                    task_family=getattr(prebrain_args, 'task_family', '') or '',
                )
            return fallback_brain_action(
                prebrain_args.objective,
                prebrain_args.target,
                int(prebrain_args.aggression),
                task_family=getattr(prebrain_args, 'task_family', '') or '',
                recent_context=host_bound_recent_context,
                intent_context=intent_runtime_context,
            )

        def _mock_brain_runner() -> Dict[str, Any]:
            return _mock_brain_action(
                prebrain_args.objective,
                prebrain_args.target,
                int(prebrain_args.aggression),
                task_family=getattr(prebrain_args, 'task_family', '') or '',
            )

        brain, brain_adapter_meta = run_brain_adapter(
            delivery_profile=delivery_profile,
            external_runner=_external_brain_runner,
            local_runner=_local_brain_runner,
            mock_runner=_mock_brain_runner,
        )
        stage_timers['brain_sec'] = round(time.perf_counter() - _t0, 4)
        log_stage('BRAIN', 'brain_adapter_selected', 'success', f"mode={brain_adapter_meta.get('mode','unknown')};source={brain_adapter_meta.get('source','unknown')}")
    except Exception as exc:
        log_stage('BRAIN', 'propose_action', 'failed', str(exc))
        brain = fallback_brain_action(prebrain_args.objective, prebrain_args.target, int(prebrain_args.aggression), task_family=getattr(prebrain_args, 'task_family', '') or '', recent_context=host_bound_recent_context, intent_context=intent_runtime_context)
        brain_adapter_meta = {'mode': 'local', 'source': 'fallback_after_adapter_error'}
        log_stage('BRAIN', 'fallback_action', 'warning', json.dumps(brain, ensure_ascii=False)[:240])
        log_stage('BRAIN', 'brain_fallback_used', 'warning', f"task_family={str(getattr(prebrain_args, 'task_family', '') or 'generic')[:48]}; tool={str(brain.get('tool') or '')}")

    if isinstance(brain, dict):
        if task_family and not str(brain.get('task_family') or '').strip():
            brain['task_family'] = task_family
        brain = apply_intent_guidance_to_brain(brain, intent_runtime_context, objective=prebrain_args.objective, target=prebrain_args.target, aggression=int(prebrain_args.aggression), task_family=task_family, recent_context=host_bound_recent_context)
        brain['resolved_planner_profiles'] = list(contextual_tooling.get('profiles') or [])
    brain, tool_norm = enforce_brain_tool_whitelist(brain, prebrain_args.objective, prebrain_args.target, int(prebrain_args.aggression), task_family=task_family, recent_context=host_bound_recent_context, execution_mode=execution_mode)
    creds_runtime = load_credentials_runtime_policy()
    if isinstance(brain, dict):
        sanitized_brain, sanitization_notes = sanitize_action_spec(brain)
        if sanitization_notes:
            brain = sanitized_brain
            try:
                log_stage('BRAIN', 'contract_sanitized', 'warning', json.dumps({'notes': sanitization_notes[:6], 'count': len(sanitization_notes)}, ensure_ascii=False)[:240])
            except Exception:
                pass
        auth_sanitized_brain, auth_sanitization_notes = sanitize_action_spec_auth_modes(brain, creds_runtime)
        if auth_sanitization_notes:
            brain = auth_sanitized_brain
            try:
                log_stage('BRAIN', 'contract_auth_mode_sanitized', 'warning', json.dumps({'notes': auth_sanitization_notes[:6], 'count': len(auth_sanitization_notes)}, ensure_ascii=False)[:240])
            except Exception:
                pass
    if isinstance(tool_norm, dict):
        try:
            log_stage('INTERPRETER', 'tool_normalized', 'warning', json.dumps(tool_norm, ensure_ascii=False)[:240])
            log_stage('BRAIN', 'invalid_tool_attempt', 'warning', f"original={tool_norm.get('original_tool')}; normalized={tool_norm.get('normalized_tool')}; reason={tool_norm.get('reason')}")
        except Exception:
            pass
    log_stage('BRAIN', 'propose_action', 'success', json.dumps(brain, ensure_ascii=False)[:240])
    if experimental_mode:
        log_stage('BRAIN', 'experimental_mode_enabled', 'warning', 'creative vector synthesis enabled for this run')
    try:
        log_stage('INTERPRETER', 'brain_interpretation', 'success', f"tool={brain.get('tool')}; target={str(brain.get('target') or prebrain_args.target)[:120]}")
    except Exception:
        pass

    ok_spec, spec_errors = validate_action_spec(brain)
    if not ok_spec:
        output = {
            'brain': brain,
            'auditor': {'decision': 'reject', 'reason': 'invalid_brain_contract:' + ','.join(spec_errors), 'reason_code': 'invalid_brain_contract'},
            'auditor_raw_decision': None,
            'approval_transform_chain': [],
            'approval_source': 'brain_contract',
            'final_approval_decision': 'reject',
            'reason_code': 'invalid_brain_contract',
        }
        log_stage('BRAIN', 'contract_validation', 'failed', ','.join(spec_errors)[:240])
        return output, 'blocked', 'brain_contract_invalid'

    raw_action_spec = _build_raw_action_spec(
        brain,
        args=prebrain_args,
        task_family=task_family,
        execution_mode=execution_mode,
        intent_runtime_context=intent_runtime_context,
    )
    effective_args, aggression_state = normalize_runtime_aggression(
        prebrain_args,
        cfg=cfg,
        target=prebrain_args.target,
        raw_action_spec=raw_action_spec,
        creds_policy=creds_runtime,
        requested_aggression=int(prebrain_aggression_state.get('requested_aggression', getattr(args, 'aggression', 0) or 0)),
        existing_chain=list(prebrain_aggression_state.get('chain') or []),
        log_stage_fn=log_stage,
    )
    requested_aggression = int(aggression_state.get('requested_aggression', getattr(args, 'aggression', 0) or 0))
    effective_aggression = int(aggression_state.get('effective_aggression', getattr(effective_args, 'aggression', 0) or 0))
    aggression_remap_note = dict(aggression_state.get('policy_aggression_remap') or {}) if isinstance(aggression_state.get('policy_aggression_remap'), dict) else None
    action_spec, _prepared_compiled = prepare_action_spec_for_execution(raw_action_spec, target=prebrain_args.target, creds=creds_runtime, execution_mode=execution_mode)
    target_host = extract_host_from_url(prebrain_args.target)
    target_in_scope = bool(cfg.get('force_target_in_scope', False)) or (host_in_scope(target_host, load_scope_domains()) if target_host else False)
    prepared_execution_spec = build_prepared_execution_spec(
        raw_action_spec=raw_action_spec,
        prepared_action_spec=action_spec,
        compiled_action=_prepared_compiled,
        creds_policy=creds_runtime,
        target=prebrain_args.target,
        target_in_scope=target_in_scope,
    )
    semantic_loss_policy = ((_prepared_compiled.get('semantic_loss_policy') if isinstance(_prepared_compiled.get('semantic_loss_policy'), dict) else {}) or ((prepared_execution_spec.get('compiler') or {}).get('semantic_loss_policy') if isinstance(prepared_execution_spec.get('compiler'), dict) else {}))
    semantic_loss_gate = semantic_loss_runtime_gate(semantic_loss_policy)
    semantic_loss_rereview_required = str(semantic_loss_policy.get('policy_response') or '') == 'auditor_rereview'
    effective_owner_approved_auth = bool(prebrain_args.owner_approved_auth or creds_runtime.get('credentials_owner_approved', False))
    gate = evaluate_action_spec(action_spec, prebrain_args.target, effective_owner_approved_auth, creds=creds_runtime)
    if bool(cfg.get('force_target_in_scope', False)) and not gate.get('pass') and 'out_of_scope_target' in str(gate.get('reason') or ''):
        gate = {
            **dict(gate or {}),
            'pass': True,
            'reason': 'demo_scope_target_override',
            'override_source': 'delivery_profile_demo_scope',
        }
        if isinstance(delivery_notes, dict):
            delivery_notes['policy_gate_override'] = 'demo_scope_target_override'

    correlation_id = str(uuid.uuid4())
    output = _build_initial_output(
        correlation_id=correlation_id,
        args=effective_args,
        cfg=cfg,
        experimental_mode=experimental_mode,
        execution_mode=execution_mode,
        planner_hints=planner_hints,
        brain=brain,
        gate=gate,
        semantic_loss_policy=semantic_loss_policy,
        semantic_loss_rereview_required=semantic_loss_rereview_required,
        prepared_execution_spec=prepared_execution_spec,
        action_spec=action_spec,
        intent_runtime_context=intent_runtime_context,
        delivery_profile=delivery_profile,
        delivery_notes=delivery_notes,
    )

    if isinstance(output.get('integration_adapters'), dict):
        brain_adapter_out = output['integration_adapters'].get('brain') if isinstance(output['integration_adapters'].get('brain'), dict) else {}
        brain_adapter_out.update(brain_adapter_meta)
        output['integration_adapters']['brain'] = brain_adapter_out

    output['aggression_normalization'] = aggression_state
    if aggression_remap_note:
        output['policy_aggression_remap'] = aggression_remap_note
    output['requested_aggression'] = requested_aggression
    output['effective_aggression'] = effective_aggression

    request_shape_hygiene = dict(output.get('request_shape_hygiene') or {}) if isinstance(output.get('request_shape_hygiene'), dict) else _request_shape_hygiene_record(prepared_execution_spec)

    try:
        log_stage('INTERPRETER', 'scope_assessment', 'success', f"in_scope={target_in_scope}; host={target_host or args.target}; aggression={effective_args.aggression}")
    except Exception:
        pass
    try:
        _log_request_shape_hygiene(log_stage_fn=log_stage, request_shape_hygiene=request_shape_hygiene, target_in_scope=target_in_scope)
    except Exception:
        pass
    try:
        log_stage('INTERPRETER', 'semantic_loss_assessment', 'warning' if semantic_loss_gate.get('degraded_execution') else 'success', f"loss_class={semantic_loss_policy.get('loss_class','none')};response={semantic_loss_policy.get('policy_response','proceed')};reason={semantic_loss_policy.get('reason_code','semantic_loss_none')}")
    except Exception:
        pass
    if semantic_loss_gate.get('blocked'):
        output['auditor'] = {
            'decision': 'reject',
            'reason': str(semantic_loss_gate.get('blocked_reason') or 'semantic_loss_policy_block'),
            'reason_code': str(semantic_loss_gate.get('blocked_reason_code') or 'semantic_loss_policy_block'),
            'constraints': {'aggression': effective_args.aggression}
        }
        output['auditor_raw_decision'] = None
        output['approval_transform_chain'] = []
        output['approval_source'] = 'semantic_loss_policy'
        output['final_approval_decision'] = 'reject'
        output['reason_code'] = str(semantic_loss_gate.get('blocked_reason_code') or 'semantic_loss_policy_block')
        return output, 'blocked', str(semantic_loss_gate.get('blocked_reason') or 'semantic_loss_policy_block')
    auditor_timeout = int(cfg.get('auditor_timeout_sec', 90) or 90)
    output['runtime_task']['recommended_tools'] = list(
        preferred_tools_for_task_family(
            str(getattr(args, 'task_family', '') or ''),
            args.objective,
            recent_context=host_bound_recent_context,
            capability_candidates=list(intent_runtime_context.get('capability_candidates') or []),
            recommended_action_types=list(intent_runtime_context.get('recommended_action_types') or []),
        )
    )
    recent_context_compact = compact_recent_context(recent_context, limit=4, target=args.target)
    recent_runtime_summary = summarize_recent_runtime_state(recent_context, target=args.target, task_family=str(getattr(args, 'task_family', '') or ''))
    brain_reasoning = {
        'hypothesis': str(brain.get('hypothesis') or ''),
        'why_now': str(brain.get('why_now') or ''),
        'planner_alignment': str(brain.get('planner_alignment') or 'unknown'),
        'planner_override_reason': str(brain.get('planner_override_reason') or ''),
        'expected_signal': str(brain.get('expected_signal') or ''),
        'evidence_goal': str(brain.get('evidence_goal') or ''),
        'next_if_positive': str(brain.get('next_if_positive') or ''),
        'next_if_negative': str(brain.get('next_if_negative') or ''),
        'redundancy_risk': str(brain.get('redundancy_risk') or 'unknown'),
    }
    auditor_prepared_spec = redact_prepared_execution_spec_for_auditor(prepared_execution_spec)
    auditor_compact_spec = _compact_prepared_execution_spec_for_auditor(auditor_prepared_spec)
    context_payload = _build_auditor_context_summary(
        args=effective_args,
        target_in_scope=target_in_scope,
        recent_runtime_summary=recent_runtime_summary,
        planner_hints=planner_hints,
        brain_reasoning=brain_reasoning,
        semantic_loss_policy=semantic_loss_policy,
        intent_runtime_context=intent_runtime_context,
        request_shape_hygiene=request_shape_hygiene,
    )

    if not gate.get('pass'):
        reason = gate.get('reason', 'policy_block')
        output['auditor'] = {
            'decision': 'owner_approval_required',
            'reason': f"policy_gate_block:{reason}",
            'reason_code': 'policy_gate_block',
            'constraints': {'aggression': effective_args.aggression}
        }
        log_stage('POLICY', 'policy_gate', 'blocked', reason)
        try:
            log_stage(
                'POLICY',
                'policy_gate_diag',
                'blocked',
                f"reason={reason};cred_required={bool(creds_runtime.get('credentials_required',False))};cred_owner_approved={bool(creds_runtime.get('credentials_owner_approved',False))};owner_approved_auth={bool(args.owner_approved_auth)};effective_owner_approved_auth={bool(effective_owner_approved_auth)};resolved_campaign_key={str(creds_runtime.get('resolved_campaign_key') or '-')[:24]}",
            )
        except Exception:
            pass
        try:
            log_stage('INTERPRETER', 'policy_decision', 'blocked', f"blocked_by_policy:{reason}")
        except Exception:
            pass
        output['reason_code'] = 'policy_gate_block'
        return output, 'blocked', f"policy_gate:{reason}"

    auditor_adapter_meta: Dict[str, Any] = {}
    try:
        log_stage('AUDITOR', 'auditor_wait', 'in_progress', f'waiting_for_auditor_response timeout={auditor_timeout}s')
        _t0 = time.perf_counter()

        def _external_auditor_runner() -> Dict[str, Any]:
            return ask_json(
                'auditor',
                base_prompt=_build_auditor_prompt(
                    prepared_execution_spec=auditor_compact_spec,
                    context_summary=context_payload,
                ),
                contract_hint='{"decision":"approve|reject|owner_approval_required","reason_code":"approve_in_scope|reject_invalid_contract|reject_policy_gate|reject_out_of_scope|owner_approval_required_risk|owner_approval_required_auth|owner_approval_required_uncertain|owner_approval_required_policy","reason":"compact_detail","risk_band":"low|medium|high","owner_gate":true,"constraints":{"aggression":1}}',
                retries=json_retries,
                timeout=auditor_timeout,
                prompt_token_budget=auditor_prompt_token_budget
            )

        def _local_auditor_runner() -> Dict[str, Any]:
            return _local_auditor_decision(
                aggression=effective_args.aggression,
                delivery_profile=delivery_profile,
                semantic_loss_rereview_required=semantic_loss_rereview_required,
            )

        def _mock_auditor_runner() -> Dict[str, Any]:
            return _mock_auditor_decision(aggression=effective_args.aggression)

        auditor, auditor_adapter_meta = run_auditor_adapter(
            delivery_profile=delivery_profile,
            external_runner=_external_auditor_runner,
            local_runner=_local_auditor_runner,
            mock_runner=_mock_auditor_runner,
        )
        stage_timers['auditor_sec'] = round(time.perf_counter() - _t0, 4)
        log_stage('AUDITOR', 'auditor_adapter_selected', 'success', f"mode={auditor_adapter_meta.get('mode','unknown')};source={auditor_adapter_meta.get('source','unknown')}")
    except Exception as exc:
        log_stage('AUDITOR', 'audit', 'failed', str(exc))
        output['auditor'] = {
            'decision': 'owner_approval_required',
            'reason': f'auditor_timeout_or_failure: {str(exc)[:180]}',
            'reason_code': 'auditor_timeout',
            'constraints': {'aggression': effective_args.aggression},
        }
        output['auditor_raw_decision'] = None
        output['approval_transform_chain'] = []
        output['approval_source'] = 'auditor_error'
        output['final_approval_decision'] = 'owner_approval_required'
        output['reason_code'] = 'auditor_timeout'
        if isinstance(output.get('integration_adapters'), dict):
            auditor_adapter_out = output['integration_adapters'].get('auditor') if isinstance(output['integration_adapters'].get('auditor'), dict) else {}
            auditor_adapter_out.update({'mode': 'error', 'source': 'auditor_adapter_error'})
            output['integration_adapters']['auditor'] = auditor_adapter_out
        return output, 'blocked', 'auditor_timeout_or_failure'

    if isinstance(auditor, dict):
        dec0 = str(auditor.get('decision') or '').strip().lower()
        if not dec0:
            auditor['decision'] = 'owner_approval_required'
            if not str(auditor.get('reason') or '').strip():
                auditor['reason'] = 'auditor_missing_decision_defaulted_to_owner_gate'
            dec0 = 'owner_approval_required'
        rc = str(auditor.get('reason_code') or '').strip().lower()
        if not rc:
            reason0 = str(auditor.get('reason') or '').lower()
            if dec0 == 'approve':
                rc = 'approve_in_scope'
            elif 'out_of_scope' in reason0 or 'out of scope' in reason0:
                rc = 'reject_out_of_scope'
            elif 'auth' in reason0 or 'bearer' in reason0 or 'credential' in reason0:
                rc = 'owner_approval_required_auth'
            elif 'policy' in reason0 or 'gate' in reason0:
                rc = 'reject_policy_gate' if dec0 == 'reject' else 'owner_approval_required_policy'
            elif dec0 == 'reject':
                rc = 'reject_invalid_contract'
            else:
                rc = 'owner_approval_required_uncertain'
            auditor['reason_code'] = rc
        if not str(auditor.get('risk_band') or '').strip().lower():
            rcx = str(auditor.get('reason_code') or '')
            auditor['risk_band'] = 'high' if any(k in rcx for k in ['risk','auth']) else ('medium' if 'policy' in rcx else 'low')
        if 'owner_gate' not in auditor:
            auditor['owner_gate'] = bool(str(auditor.get('decision') or '').lower() == 'owner_approval_required')

    approval_transform_chain: list[dict] = []
    raw_auditor = dict(auditor) if isinstance(auditor, dict) else {}

    ar = (str((auditor.get('reason_code') or '')) + ' ' + str((auditor.get('reason') or ''))).lower()
    scope_mismatch_signals = (
        'out of scope',
        'out_of_scope',
        'allowed aggression constraint of 1',
        'required aggression constraint of 1',
        'mandatory aggression constraint of 1',
        'aggression constraint of 1',
        'exceeds allowed maximum (1)',
        'exceeds permitted maximum (1)',
        'maximum (1)',
        'low-risk actions',
    )
    scope_mismatch = any(sig in ar for sig in scope_mismatch_signals)

    policy_diag_logging = bool(cfg.get('policy_diag_logging', True))
    cred_diag = load_credentials_runtime_policy()

    if policy_diag_logging:
        try:
            log_stage(
                'POLICY',
                'policy_diag',
                'in_progress',
                f"target_in_scope={target_in_scope};auditor_decision={auditor.get('decision')};requested_aggr={requested_aggression};effective_aggr={effective_args.aggression};strict_det={strict_deterministic};cred_required={bool(cred_diag.get('credentials_required',False))};cred_owner_approved={bool(cred_diag.get('credentials_owner_approved',False))};resolved_campaign_key={str(cred_diag.get('resolved_campaign_key') or '-')[:24]};reason={str(auditor.get('reason') or '')[:140]}",
            )
        except Exception:
            pass

    if target_in_scope and scope_mismatch and policy_diag_logging:
        try:
            log_stage('POLICY', 'auditor_scope_mismatch_diag', 'warning', f"in_scope_target_with_oos_like_auditor_reason:{str(auditor.get('reason') or '')[:180]}")
        except Exception:
            pass

    if args.owner_override and auditor.get('decision') in {'owner_approval_required', 'reject', 'deny', 'blocked'}:
        base_reason = str(auditor.get('reason', 'owner approval granted'))
        auditor = tracked_auditor_replace(
            approval_transform_chain,
            'owner_override',
            auditor,
            decision='approve',
            reason=f"owner_override_flag_applied: {base_reason}",
            reason_code='owner_override',
            constraints=auditor.get('constraints', {'aggression': effective_args.aggression}),
            owner_gate=False,
        )

    ok_aud, aud_errors = validate_auditor_payload(auditor)
    if not ok_aud:
        before = dict(auditor) if isinstance(auditor, dict) else {}
        auditor = {'decision': 'reject', 'reason': 'invalid_auditor_contract:' + ','.join(aud_errors), 'reason_code': 'invalid_auditor_contract', 'constraints': {'aggression': effective_args.aggression}}
        record_approval_transform(approval_transform_chain, 'auditor_contract_validation', before, auditor)
        log_stage('AUDITOR', 'contract_validation', 'failed', ','.join(aud_errors)[:240])

    if isinstance(output.get('integration_adapters'), dict):
        auditor_adapter_out = output['integration_adapters'].get('auditor') if isinstance(output['integration_adapters'].get('auditor'), dict) else {}
        auditor_adapter_out.update(auditor_adapter_meta)
        output['integration_adapters']['auditor'] = auditor_adapter_out

    output['auditor_raw_decision'] = raw_auditor
    output['approval_transform_chain'] = approval_transform_chain
    output['approval_source'] = approval_transform_chain[-1]['source'] if approval_transform_chain else ('auditor_rereview' if semantic_loss_rereview_required else 'auditor')
    output['final_approval_decision'] = str((auditor or {}).get('decision') or '')
    output['semantic_loss_rereview_completed'] = bool(semantic_loss_rereview_required and str((auditor or {}).get('decision') or '').strip().lower() == 'approve')
    output['semantic_loss_rereview_decision'] = str((auditor or {}).get('decision') or '') if semantic_loss_rereview_required else ''
    output['auditor'] = auditor
    if isinstance(output.get('auditor'), dict) and not output['auditor'].get('reason_code'):
        dec = str(output['auditor'].get('decision') or '').lower()
        output['auditor']['reason_code'] = {
            'approve': 'auditor_approve',
            'reject': 'auditor_reject',
            'deny': 'auditor_deny',
            'blocked': 'auditor_blocked',
            'owner_approval_required': 'auditor_owner_approval_required',
        }.get(dec, 'auditor_unknown')
    auditor = output['auditor']
    output['auditor_decision_normalized'] = normalize_auditor_decision(auditor.get('decision'))
    log_stage('AUDITOR', 'audit', auditor.get('decision', 'unknown'), f"{str(auditor.get('reason_code') or 'auditor_unknown')}:{str(auditor.get('reason') or '')[:220]}")
    try:
        log_stage('INTERPRETER', 'auditor_interpretation', 'success' if auditor.get('decision')=='approve' else 'blocked', f"decision={auditor.get('decision')}; reason={str(auditor.get('reason') or '')[:180]}")
    except Exception:
        pass
    if semantic_loss_rereview_required:
        try:
            log_stage('AUDITOR', 'semantic_loss_rereview', 'success' if auditor.get('decision') == 'approve' else 'blocked', f"loss_class={semantic_loss_policy.get('loss_class','none')};decision={auditor.get('decision')};reason={str(auditor.get('reason_code') or '')}")
        except Exception:
            pass

    if auditor.get('decision') != 'approve':
        output['reason_code'] = str((auditor or {}).get('reason_code') or 'auditor_blocked')
        prefix = 'auditor_rereview' if semantic_loss_rereview_required else 'auditor'
        return output, 'blocked', f"{prefix}:{auditor.get('reason')}"

    engine = ExecutionEngine()
    owner_override_applied = bool(args.owner_override and str((raw_auditor or {}).get('decision') or '').strip().lower() != 'approve')
    output['approved_execution_spec'] = build_approved_execution_spec(
        prepared_execution_spec,
        auditor=auditor if isinstance(auditor, dict) else {},
        approval_source=str(output.get('approval_source') or ''),
        approval_transform_chain=approval_transform_chain,
        owner_override_applied=owner_override_applied,
    )
    built_cmd = list((output.get('approved_execution_spec') or {}).get('execution_truth', {}).get('command_preview') or [])
    if cfg.get('verbose_commands', True):
        output['planned_command'] = built_cmd or None

    try:
        lifecycle_artifacts_v0_2 = build_lifecycle_artifacts_v02(output)
        output['scl_lifecycle_artifacts_v0_2'] = lifecycle_artifacts_v0_2
        output['execution_contract_v0_2'] = lifecycle_artifacts_v0_2.get('execution_contract.json')
        output['execution_ticket_v0_2'] = lifecycle_artifacts_v0_2.get('execution_ticket.json')
        output['artifact_chain_manifest_v0_2'] = lifecycle_artifacts_v0_2.get('artifact_chain_manifest.json')
        log_stage('ENGINE', 'execution_ticket_gate_prepare', 'success', 'sclite_v0_2_execution_ticket_ready')
    except Exception as exc:
        log_stage('ENGINE', 'execution_ticket_gate_prepare', 'failed', str(exc))
        output['engine'] = {
            'status': 'blocked',
            'returncode': None,
            'stdout': '',
            'stderr': str(exc),
            'reason': 'execution_ticket_gate_prepare_failed',
        }
        output['reason_code'] = 'execution_ticket_gate_prepare_failed'
        return output, 'blocked', 'execution_ticket_gate_prepare_failed'

    execution_adapter_meta: Dict[str, Any] = {}
    try:
        _t0 = time.perf_counter()

        def _local_execution_runner(effective_dry_run: bool) -> Dict[str, Any]:
            if not hasattr(engine, 'execute_approved_spec'):
                raise RuntimeError('execution_engine_missing_approved_spec_path')
            return engine.execute_approved_spec(
                output['approved_execution_spec'],
                dry_run=effective_dry_run,
                execution_ticket=output.get('execution_ticket_v0_2'),
                execution_contract=output.get('execution_contract_v0_2'),
                require_execution_ticket=True,
            )

        def _mock_execution_runner(effective_dry_run: bool) -> Dict[str, Any]:
            return _mock_execution_result(output['approved_execution_spec'], effective_dry_run=effective_dry_run)

        engine_res, execution_adapter_meta = run_execution_adapter(
            delivery_profile=delivery_profile,
            dry_run=bool(effective_args.dry_run),
            local_runner=_local_execution_runner,
            mock_runner=_mock_execution_runner,
        )
        stage_timers['engine_sec'] = round(time.perf_counter() - _t0, 4)
        log_stage('ENGINE', 'execution_adapter_selected', 'success', f"mode={execution_adapter_meta.get('mode','unknown')};source={execution_adapter_meta.get('source','unknown')};dry_run={execution_adapter_meta.get('effective_dry_run')}")
    except Exception as exc:
        log_stage('ENGINE', 'execute', 'failed', str(exc))
        output['engine'] = {
            'status': 'blocked',
            'returncode': None,
            'stdout': '',
            'stderr': str(exc),
            'reason': 'execution_adapter_error',
        }
        if isinstance(output.get('integration_adapters'), dict):
            execution_adapter_out = output['integration_adapters'].get('execution') if isinstance(output['integration_adapters'].get('execution'), dict) else {}
            execution_adapter_out.update({'mode': 'error', 'source': 'execution_adapter_error'})
            output['integration_adapters']['execution'] = execution_adapter_out
        output['reason_code'] = 'execution_adapter_error'
        return output, 'blocked', 'execution_adapter_error'

    output['engine'] = engine_res
    if isinstance(output.get('integration_adapters'), dict):
        execution_adapter_out = output['integration_adapters'].get('execution') if isinstance(output['integration_adapters'].get('execution'), dict) else {}
        execution_adapter_out.update(execution_adapter_meta)
        output['integration_adapters']['execution'] = execution_adapter_out

    output['execution_lineage'] = {
        'approved_execution_spec_version': str((output.get('approved_execution_spec') or {}).get('spec_version') or ''),
        'approved_command_preview': list((output.get('approved_execution_spec') or {}).get('execution_truth', {}).get('command_preview') or []),
        'approved_command_input_summary': dict((output.get('approved_execution_spec') or {}).get('execution_truth', {}).get('command_input_summary') or {}),
        'approved_execution_plan': list((output.get('approved_execution_spec') or {}).get('execution_truth', {}).get('execution_plan') or []),
        'approved_execution_input_summaries': list((output.get('approved_execution_spec') or {}).get('execution_truth', {}).get('execution_input_summaries') or []),
        'engine_planned_commands': list(engine_res.get('planned_commands') or []),
        'engine_executed_commands': list(engine_res.get('executed_commands') or []),
    }
    final_status, summary_text, error_flag = _finalize_engine_output(
        output=output,
        engine_res=engine_res,
        auditor=auditor,
        brain=brain,
        execution_mode=execution_mode,
    )

    stdout_snip = engine_res.get('stdout') or ''
    stderr_snip = engine_res.get('stderr') or ''

    analysis_bytes = len(stdout_snip) + len(stderr_snip)
    min_bytes = int(cfg.get('analysis_min_bytes', 0) or 0)
    signal = high_signal(engine_res, analysis_min_bytes=max(64, min_bytes))
    interesting_http = interesting_http_signal(engine_res, args.objective)
    should_analyze = (
        cfg.get('enable_analysis', False)
        and engine_res.get('status') not in {None, 'dry-run'}
        and (analysis_bytes >= min_bytes or interesting_http)
        and (signal or interesting_http)
    )

    context_entry: Dict[str, Any] = {
        'correlation_id': correlation_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'objective': args.objective,
        'target': args.target,
        'task_family': str(getattr(args, 'task_family', '') or ''),
        'action_type': str(brain.get('action_type') or 'single_probe'),
        'tool': str((engine_res.get('compiled_action') or {}).get('compiler_tool_choice') or brain.get('tool') or ''),
        'mode': 'dry-run' if effective_args.dry_run else 'live',
        'runtime_mode': str(delivery_profile.get('runtime_mode') or 'local'),
        'integration_adapters': {
            'brain': dict((output.get('integration_adapters') or {}).get('brain') or {}),
            'auditor': dict((output.get('integration_adapters') or {}).get('auditor') or {}),
            'execution': dict((output.get('integration_adapters') or {}).get('execution') or {}),
        },
        'status': engine_res.get('status'),
        'returncode': engine_res.get('returncode'),
        'auditor_decision': auditor.get('decision'),
        'owner_override': args.owner_override,
        'brain': {
            'action_type': str(brain.get('action_type') or 'single_probe'),
            'planner_alignment': str(brain.get('planner_alignment') or ''),
            'planner_override_reason': str(brain.get('planner_override_reason') or '')[:180],
            'hypothesis': str(brain.get('hypothesis') or '')[:220],
            'why_now': str(brain.get('why_now') or '')[:220],
            'expected_signal': str(brain.get('expected_signal') or '')[:180],
            'redundancy_risk': str(brain.get('redundancy_risk') or ''),
            'recipe_name': str((engine_res.get('compiled_action') or {}).get('recipe_name') or brain.get('recipe_name') or ''),
            'execution_mode': str((engine_res.get('compiled_action') or {}).get('execution_mode') or execution_mode),
        },
        'stdout_preview': stdout_snip[:200],
        'stderr_preview': stderr_snip[:160],
    }

    analysis_result, analysis_context, analysis_sec = run_analysis_stage(
        cfg=cfg,
        engine_res=engine_res,
        objective=args.objective,
        target=args.target,
        task_success_criteria=str(getattr(args, 'task_success_criteria', '') or ''),
        campaign_success_criteria=str(getattr(args, 'campaign_success_criteria', '') or ''),
        task_family=str(getattr(args, 'task_family', '') or ''),
        acceptance_checks=str(getattr(args, 'acceptance_checks', '') or ''),
        evidence_required=str(getattr(args, 'evidence_required', '') or ''),
        recent_context=recent_context,
        json_retries=json_retries,
        prompt_token_budget=prompt_token_budget,
        analysis_bytes=analysis_bytes,
        min_bytes=min_bytes,
        signal=signal,
        interesting_http=interesting_http,
        ask_json_fn=ask_json,
        log_stage_fn=log_stage,
    )
    output['analysis'] = analysis_result
    if analysis_context:
        context_entry['analysis'] = analysis_context
    if analysis_sec is not None:
        stage_timers['analysis_sec'] = analysis_sec

    analysis_payload_for_light = output.get('analysis') if isinstance(output.get('analysis'), dict) else {}

    success_eval = evaluate_success_criteria(
        str(getattr(args, 'task_success_criteria', '') or ''),
        engine_res,
        summary_text,
        analysis_payload_for_light if isinstance(analysis_payload_for_light, dict) else None,
        task_family=str(getattr(args, 'task_family', '') or ''),
        acceptance_checks=getattr(args, 'acceptance_checks', None),
        evidence_required=getattr(args, 'evidence_required', None),
        success_semantics=explicit_success_semantics,
    )
    output['success_criteria'] = {
        'scope': 'task',
        'task_input': str(getattr(args, 'task_success_criteria', '') or ''),
        'campaign_input': str(getattr(args, 'campaign_success_criteria', '') or ''),
        'task_family': str(getattr(args, 'task_family', '') or ''),
        'acceptance_checks': str(getattr(args, 'acceptance_checks', '') or ''),
        'evidence_required': str(getattr(args, 'evidence_required', '') or ''),
        'success_semantics': dict(explicit_success_semantics or {}),
        **success_eval,
    }
    context_entry['success_criteria'] = output['success_criteria']

    light_result, light_context, light_sec = run_light_stage(
        cfg=cfg,
        signal=signal,
        analysis_payload_for_light=analysis_payload_for_light if isinstance(analysis_payload_for_light, dict) else {},
        engine_res=engine_res,
        objective=args.objective,
        target=args.target,
        recent_context=recent_context,
        json_retries=json_retries,
        prompt_token_budget=prompt_token_budget,
        ask_json_fn=ask_json,
        log_stage_fn=log_stage,
    )
    output['light'] = light_result
    if light_context:
        context_entry['light'] = light_context
    if light_sec is not None:
        stage_timers['light_sec'] = light_sec

    output['stage_timings_sec'] = stage_timers
    output['observability'] = {
        'signal_detected': bool(signal),
        'analysis_enabled': bool(cfg.get('enable_analysis', False)),
        'light_enabled': bool(cfg.get('enable_light', False)),
        'strict_deterministic': strict_deterministic,
    }
    output['final_status'] = final_status
    if final_status in {'success','ok'}:
        output['reason_code'] = 'engine_success'
    elif final_status in {'failed','error'}:
        output['reason_code'] = 'engine_failed'
    elif final_status in {'blocked'}:
        output['reason_code'] = str((auditor or {}).get('reason_code') or 'auditor_blocked')
    else:
        output['reason_code'] = 'pipeline_' + str(final_status)
    append_context_entry(context_entry, context_limit)
    return output, final_status, summary_text


def main() -> None:
    ap = argparse.ArgumentParser(description='RAVEN-CLAW strict multi-agent pipeline runner')
    ap.add_argument('--objective')
    ap.add_argument('--target')
    ap.add_argument('--aggression', type=int, default=6)
    ap.add_argument('--success-criteria', default='')  # backward compatibility
    ap.add_argument('--task-success-criteria', default='')
    ap.add_argument('--campaign-success-criteria', default='')
    ap.add_argument('--task-family', default='')
    ap.add_argument('--acceptance-checks', default='')
    ap.add_argument('--evidence-required', default='')
    ap.add_argument('--success-semantics-json', '--success_semantics_json', dest='success_semantics_json', default='')
    ap.add_argument('--experiment-intent-id', default='')
    ap.add_argument('--capability-candidates-json', default='')
    ap.add_argument('--recommended-action-types-json', default='')
    ap.add_argument('--hypothesis-candidates-json', default='')
    ap.add_argument('--planner-constraints-json', default='')
    ap.add_argument('--planner-preferences-json', default='')
    ap.add_argument('--open-questions-json', default='')
    ap.add_argument('--planner-rationale-json', default='')
    ap.add_argument('--planning-ladder-json', default='')
    ap.add_argument('--target-surface-rationale-json', default='')
    ap.add_argument('--recommended-progression-json', default='')
    ap.add_argument('--semantic-lineage-json', default='')
    ap.add_argument('--semantic-lineage-summary-json', default='')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--runtime-mode', default='', help='delivery/runtime mode override (demo/local/external)')
    ap.add_argument('--owner-approved-auth', action='store_true', help='allow Authorization header actions after explicit owner approval')
    ap.add_argument('--owner-override', action='store_true', help='owner-approved elevated tests (convert owner_approval_required to approve)')
    ap.add_argument('--verbose-commands', choices=['on', 'off'], help='toggle command preview output (persistent)')
    args = ap.parse_args()

    cfg = load_pipeline_config()
    context_limit = int(cfg.get('context_history', 5) or 0)
    recent_context = load_context_history(context_limit)

    if args.verbose_commands:
        cfg['verbose_commands'] = (args.verbose_commands == 'on')
        save_pipeline_config(cfg)
        if not args.objective and not args.target:
            print(json.dumps({'status': 'ok', 'verbose_commands': cfg['verbose_commands']}, ensure_ascii=False, indent=2))
            return

    if not args.objective or not args.target:
        raise SystemExit('Both --objective and --target are required (unless only toggling --verbose-commands).')

    if not str(args.task_success_criteria or '').strip() and str(args.success_criteria or '').strip():
        args.task_success_criteria = str(args.success_criteria)

    campaign_check = validate_campaign(str(_selected_scope_path()))
    if not campaign_check.get('ok'):
        print(json.dumps({
            'status': 'blocked',
            'reason': 'invalid_campaign_configuration',
            'campaign_validation': campaign_check,
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    output, final_status, final_summary = execute_flow(args, cfg, recent_context, context_limit)
    output['campaign_validation'] = campaign_check
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
