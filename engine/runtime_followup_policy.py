from __future__ import annotations

from typing import Any

from learning_store import top_progression_hints  # type: ignore
from runtime_archetype_inference import adaptive_followup_explainability, infer_runtime_archetypes  # type: ignore
from runtime_plan_control import adaptive_quality_context, recon_to_exploit_synthesis  # type: ignore


EXPLOIT_FAMILIES = {'authz', 'idor', 'auth_flow', 'logic', 'workflow', 'state_transition'}
SAFE_VALIDATION_FAMILIES = {'recon', 'historical_url_mining', 'content_discovery', 'tls_assessment'}
EXPLOIT_SURFACE_TOKENS = {'authenticated_or_boundary_mapping', 'admin', 'billing', 'tenant', 'organization', 'api', 'auth', 'account'}


def quality_aware_followup_family(candidate_family: str, current_family: str, next_stage: str, target_type: str, target_surface: list[str], result: dict | None) -> str:
    candidate = str(candidate_family or '').strip().lower()
    fam = str(current_family or '').strip().lower()
    stage = str(next_stage or '').strip().lower()
    target_type_l = str(target_type or '').strip().lower()
    surface = [str(x or '').strip().lower() for x in (target_surface or []) if str(x or '').strip()]
    if not isinstance(result, dict):
        return candidate
    feedback = result.get('planner_feedback') if isinstance(result.get('planner_feedback'), dict) else {}
    if not feedback and isinstance(result.get('result_context'), dict):
        feedback = result['result_context'].get('planner_feedback') if isinstance(result['result_context'].get('planner_feedback'), dict) else {}
    quality = adaptive_quality_context(feedback)
    synthesis = recon_to_exploit_synthesis(
        planner_feedback=feedback,
        next_stage=next_stage,
        target_type=target_type_l,
        target_surface_rationale=surface,
        current_family=fam,
    )
    quality_strong = bool(quality.get('quality_structural', False))
    if str(synthesis.get('recommended_branch_action') or '') == 'pivot' and candidate in EXPLOIT_FAMILIES and stage in {'validation', 'bounded_exploit_proof', 'control_boundary_confirmation'}:
        if stage == 'validation':
            return 'content_discovery' if target_type_l in {'api', 'auth', 'integration', 'web'} else (fam if fam in SAFE_VALIDATION_FAMILIES else 'recon')
        if 'artifact_capture' in surface or target_type_l in {'static', 'support'}:
            return 'tls_assessment'
        if target_type_l in {'api', 'auth', 'integration', 'web'}:
            return 'content_discovery'
        if fam in SAFE_VALIDATION_FAMILIES:
            return fam
        return 'recon'
    if str(synthesis.get('recommended_branch_action') or '') == 'deepen' and quality_strong and stage == 'bounded_exploit_proof' and candidate in {'logic'}:
        if fam in EXPLOIT_FAMILIES:
            return fam
        if target_type_l in {'api', 'auth', 'integration'} or any(x in surface for x in EXPLOIT_SURFACE_TOKENS):
            return 'authz'
    return candidate


def attach_adaptive_followup_explainability(*, result: dict | None, inferred: dict[str, Any] | None, planner_feedback: dict[str, Any] | None, selected_family: str, current_family: str, next_stage: str, target_type: str, target_surface_rationale: list[str] | None) -> None:
    if not isinstance(result, dict):
        return
    result.setdefault('followup_explainability', {}).update(
        adaptive_followup_explainability(
            inferred=inferred,
            planner_feedback=planner_feedback,
            selected_family=selected_family,
            current_family=current_family,
            next_stage=next_stage,
            target_type=target_type,
            target_surface_rationale=target_surface_rationale,
        )
    )


def next_followup_family(current_family: str, result: dict | None = None, *, host_from_target_fn, top_progression_hints_fn=top_progression_hints) -> str:
    fam = str(current_family or '').strip().lower()
    if isinstance(result, dict):
        analysis = result.get('analysis') if isinstance(result.get('analysis'), dict) else {}
        hinted = str((analysis or {}).get('next_family_hint') or '').strip().lower()
        if hinted:
            return hinted
        runtime_task = result.get('runtime_task') if isinstance(result.get('runtime_task'), dict) else {}
        planner_rationale = result.get('planner_rationale') if isinstance(result.get('planner_rationale'), dict) else (runtime_task.get('planner_rationale') if isinstance(runtime_task.get('planner_rationale'), dict) else {})
        planning_ladder = result.get('planning_ladder') if isinstance(result.get('planning_ladder'), dict) else (runtime_task.get('planning_ladder') if isinstance(runtime_task.get('planning_ladder'), dict) else (planner_rationale.get('planning_ladder') if isinstance(planner_rationale.get('planning_ladder'), dict) else {}))
        target_profile = planner_rationale.get('target_profile_summary') if isinstance(planner_rationale.get('target_profile_summary'), dict) else {}
        target_type = str((analysis or {}).get('target_type') or target_profile.get('target_type') or '').strip().lower()
        next_stage = str((analysis or {}).get('next_stage_hint') or planning_ladder.get('next_stage') or '').strip().lower()
        target_surface = [str(x or '').strip().lower() for x in (planner_rationale.get('target_surface_rationale') or []) if str(x or '').strip()]
        target = str(result.get('target') or runtime_task.get('target') or '').strip()
        host = host_from_target_fn(target) if target else ''
        archetypes = infer_runtime_archetypes(target_type=target_type, host=host)
        archetype_flags = archetypes.get('flags') if isinstance(archetypes.get('flags'), dict) else {}
        progression_hints = top_progression_hints_fn(
            family=fam,
            target_type=target_type,
            target_surface_signal=str(target_surface[0] if target_surface else ''),
            next_stage=next_stage,
            limit=2,
        )
        suggested_families = [str(item.get('next_family') or '').strip().lower() for item in progression_hints if str(item.get('next_family') or '').strip()]
        if suggested_families:
            return quality_aware_followup_family(suggested_families[0], fam, next_stage, target_type, target_surface, result)
        if next_stage == 'control_boundary_confirmation':
            if bool(archetype_flags.get('auth_heavy')) or bool(archetype_flags.get('admin_surface')):
                selected = quality_aware_followup_family('authz', fam, next_stage, target_type, target_surface, result)
                attach_adaptive_followup_explainability(result=result, inferred=archetypes, planner_feedback=result.get('planner_feedback'), selected_family=selected, current_family=fam, next_stage=next_stage, target_type=target_type, target_surface_rationale=target_surface)
                return selected
            return quality_aware_followup_family('authz' if target_type in {'api', 'auth', 'integration'} else (fam or 'logic'), fam, next_stage, target_type, target_surface, result)
        if next_stage == 'state_transition_confirmation':
            return quality_aware_followup_family('auth_flow' if target_type == 'auth' else ('workflow' if fam in {'recon', 'content_discovery', 'historical_url_mining'} else (fam or 'workflow')), fam, next_stage, target_type, target_surface, result)
        if next_stage == 'bounded_exploit_proof':
            if fam in EXPLOIT_FAMILIES:
                return quality_aware_followup_family(fam, fam, next_stage, target_type, target_surface, result)
            if bool(archetype_flags.get('auth_heavy')) or bool(archetype_flags.get('admin_surface')):
                selected = quality_aware_followup_family('authz', fam, next_stage, target_type, target_surface, result)
                attach_adaptive_followup_explainability(result=result, inferred=archetypes, planner_feedback=result.get('planner_feedback'), selected_family=selected, current_family=fam, next_stage=next_stage, target_type=target_type, target_surface_rationale=target_surface)
                return selected
            if target_type in {'api', 'auth', 'integration'} or any(x in target_surface for x in EXPLOIT_SURFACE_TOKENS):
                return quality_aware_followup_family('authz', fam, next_stage, target_type, target_surface, result)
            return quality_aware_followup_family('logic', fam, next_stage, target_type, target_surface, result)
        if next_stage == 'report_artifact_capture':
            if bool(archetype_flags.get('static_edge')):
                selected = quality_aware_followup_family('tls_assessment' if fam in {'recon', 'historical_url_mining', 'content_discovery'} else (fam or 'tls_assessment'), fam, next_stage, target_type, target_surface, result)
                attach_adaptive_followup_explainability(result=result, inferred=archetypes, planner_feedback=result.get('planner_feedback'), selected_family=selected, current_family=fam, next_stage=next_stage, target_type=target_type, target_surface_rationale=target_surface)
                return selected
            if target_type in {'static', 'support'} or 'artifact_capture' in target_surface:
                return quality_aware_followup_family('tls_assessment' if fam in {'recon', 'historical_url_mining', 'content_discovery'} else (fam or 'tls_assessment'), fam, next_stage, target_type, target_surface, result)
            return quality_aware_followup_family(fam or 'recon', fam, next_stage, target_type, target_surface, result)
        if next_stage == 'validation' and fam in {'recon', 'historical_url_mining'}:
            if bool(archetype_flags.get('static_edge')):
                selected = quality_aware_followup_family('tls_assessment', fam, next_stage, target_type, target_surface, result)
                attach_adaptive_followup_explainability(result=result, inferred=archetypes, planner_feedback=result.get('planner_feedback'), selected_family=selected, current_family=fam, next_stage=next_stage, target_type=target_type, target_surface_rationale=target_surface)
                return selected
            return quality_aware_followup_family('content_discovery' if target_type in {'api', 'auth', 'integration', 'web'} else fam, fam, next_stage, target_type, target_surface, result)
    mapping = {
        'recon': 'historical_url_mining',
        'historical_url_mining': 'content_discovery',
        'content_discovery': 'input_tamper',
        'tls_assessment': 'content_discovery',
        'client_input': 'content_discovery',
        'auth_flow': 'authz',
        'authz': 'logic',
    }
    return mapping.get(fam, fam or 'recon')
