from __future__ import annotations

from typing import Any, Callable

from runtime_plan_control import adaptive_quality_context, recon_to_exploit_synthesis  # type: ignore


FOLLOWUP_ARCHETYPE_REASON_MAP = {
    'auth_heavy': 'prefer_authz_for_auth_heavy_archetype',
    'admin_surface': 'prefer_authz_for_admin_surface_archetype',
    'static_edge': 'prefer_tls_assessment_for_static_edge_archetype',
}


def infer_runtime_archetypes(*, target_type: str = '', host: str = '', top_archetype_hints_fn: Callable[..., list[dict[str, Any]]] | None = None, limit: int = 3) -> dict[str, Any]:
    target_type_l = str(target_type or '').strip().lower()
    host_l = str(host or '').strip().lower()
    hints_fn = top_archetype_hints_fn
    if hints_fn is None:
        from learning_store import top_archetype_hints  # type: ignore

        hints_fn = top_archetype_hints
    hints = hints_fn(target_type=target_type_l, host=host_l, limit=max(1, int(limit or 3)))
    normalized_hints = [item for item in hints if isinstance(item, dict)]
    archetypes = [str(item.get('archetype') or '').strip().lower() for item in normalized_hints if str(item.get('archetype') or '').strip()]
    confidence = max([float(item.get('score', 0.0) or 0.0) for item in normalized_hints], default=0.0)
    primary = archetypes[0] if archetypes else ''
    flags = {
        'auth_heavy': 'auth_heavy' in archetypes,
        'api_first': 'api_first' in archetypes,
        'workflow_app': 'workflow_app' in archetypes,
        'admin_surface': 'admin_surface' in archetypes,
        'static_edge': 'static_edge' in archetypes,
    }
    return {
        'primary_archetype': primary,
        'archetypes': archetypes[: max(1, int(limit or 3))],
        'confidence': round(confidence, 3),
        'flags': flags,
    }



def archetype_followup_explainability(*, inferred: dict[str, Any] | None, selected_family: str = '', next_stage: str = '') -> dict[str, Any]:
    data = inferred if isinstance(inferred, dict) else {}
    flags = data.get('flags') if isinstance(data.get('flags'), dict) else {}
    selected = str(selected_family or '').strip().lower()
    stage = str(next_stage or '').strip().lower()
    primary = str(data.get('primary_archetype') or '').strip().lower()
    confidence = round(float(data.get('confidence', 0.0) or 0.0), 3)
    reasons: list[str] = []
    if selected == 'authz' and stage in {'control_boundary_confirmation', 'bounded_exploit_proof'}:
        for key in ('auth_heavy', 'admin_surface'):
            if bool(flags.get(key)):
                reasons.append(FOLLOWUP_ARCHETYPE_REASON_MAP[key])
    if selected == 'tls_assessment' and stage in {'validation', 'report_artifact_capture'} and bool(flags.get('static_edge')):
        reasons.append(FOLLOWUP_ARCHETYPE_REASON_MAP['static_edge'])
    return {
        'archetype_primary': primary,
        'archetype_confidence': confidence,
        'archetype_hints': [str(x or '').strip().lower() for x in (data.get('archetypes') or []) if str(x or '').strip()],
        'archetype_followup_reasons': reasons,
    }



def adaptive_followup_explainability(*, inferred: dict[str, Any] | None, planner_feedback: dict[str, Any] | None = None, selected_family: str = '', current_family: str = '', next_stage: str = '', target_type: str = '', target_surface_rationale: list[str] | None = None) -> dict[str, Any]:
    surface = [str(x or '').strip().lower() for x in (target_surface_rationale or []) if str(x or '').strip()]
    feedback = planner_feedback if isinstance(planner_feedback, dict) else {}
    selected = str(selected_family or '').strip().lower()
    current = str(current_family or '').strip().lower()
    stage = str(next_stage or '').strip().lower()
    quality = adaptive_quality_context(feedback)
    synthesis = recon_to_exploit_synthesis(
        planner_feedback=feedback,
        next_stage=stage,
        target_type=str(target_type or '').strip().lower(),
        target_surface_rationale=surface,
        current_family=current,
    )
    out = archetype_followup_explainability(inferred=inferred, selected_family=selected, next_stage=stage)
    out.update({
        'selected_family': selected,
        'current_family': current,
        'quality_dead_end_heavy': bool(quality.get('dead_end_heavy', False)),
        'quality_structural': bool(quality.get('quality_structural', False)),
        'synthesis_recommended_action': str(synthesis.get('recommended_branch_action') or '').strip().lower(),
        'synthesis_reason': str(synthesis.get('synthesis_reason') or '').strip().lower(),
    })
    return out
