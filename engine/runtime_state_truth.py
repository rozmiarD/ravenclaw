from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeStateArtifact:
    artifact_id: str
    path: str
    artifact_class: str
    owner: str
    canonical_path_attr: str = ''
    legacy_paths: tuple[str, ...] = ()
    govengine_projection: str = ''

    def as_dict(self) -> dict[str, object]:
        return {
            'artifact_id': self.artifact_id,
            'path': self.path,
            'artifact_class': self.artifact_class,
            'owner': self.owner,
            'canonical_path_attr': self.canonical_path_attr,
            'legacy_paths': list(self.legacy_paths),
            'govengine_projection': self.govengine_projection,
        }


def runtime_state_artifacts() -> tuple[RuntimeStateArtifact, ...]:
    """Return persisted Ravenclaw runtime truth sources and compatibility paths."""

    return (
        RuntimeStateArtifact(
            artifact_id='planner_ui_state',
            path='reports/.planner.ui.state.json',
            artifact_class='runtime_control_plane_state',
            owner='runtime_plan_service/logdash',
        ),
        RuntimeStateArtifact(
            artifact_id='campaign_settings',
            path='reports/.campaign.settings.json',
            artifact_class='runtime_control_plane_state',
            owner='runtime_campaign_state/logdash',
        ),
        RuntimeStateArtifact(
            artifact_id='orchestrator_state',
            path='reports/.orchestrator.state.json',
            artifact_class='runtime_control_plane_state',
            owner='runtime_campaign_state/logdash',
            govengine_projection='gov_orchestrator_state_projection',
        ),
        RuntimeStateArtifact(
            artifact_id='runtime_control_state',
            path='reports/.auto_campaign.state.json',
            artifact_class='runtime_control_plane_state',
            owner='auto_campaign_runtime/logdash',
            govengine_projection='gov_run_state_projection',
        ),
        RuntimeStateArtifact(
            artifact_id='runtime_queue_state',
            path='reports/.auto_campaign.queues.json',
            artifact_class='runtime_control_plane_state',
            owner='auto_campaign_state/logdash',
            govengine_projection='gov_queue_snapshot_projection',
        ),
        RuntimeStateArtifact(
            artifact_id='runtime_plan_meta',
            path='reports/.runtime_plan.meta.json',
            artifact_class='runtime_control_plane_state',
            owner='runtime_plan_service',
        ),
        RuntimeStateArtifact(
            artifact_id='runtime_plan_tasks',
            path='reports/state/public_targets_plan.json',
            artifact_class='generated_runtime_snapshot_state',
            owner='runtime_plan_service',
            canonical_path_attr='RUNTIME_PLAN_PATH',
            legacy_paths=('engine/public_targets_plan.json',),
        ),
        RuntimeStateArtifact(
            artifact_id='host_state',
            path='reports/.host_state.json',
            artifact_class='runtime_control_plane_learned_state',
            owner='auto_campaign_runtime',
        ),
        RuntimeStateArtifact(
            artifact_id='context_summary',
            path='reports/cache/context_summary.json',
            artifact_class='generated_runtime_cache',
            owner='run_pipeline/pipeline_context',
            canonical_path_attr='CONTEXT_SUMMARY_PATH',
            legacy_paths=('engine/context_summary.json',),
        ),
        RuntimeStateArtifact(
            artifact_id='runtime_snapshot',
            path='reports/.runtime_snapshot.json',
            artifact_class='runtime_control_plane_snapshot',
            owner='runtime_persistence/logdash',
            govengine_projection='gov_runtime_snapshot_projection',
        ),
    )


def runtime_state_artifact_paths() -> tuple[str, ...]:
    return tuple(artifact.path for artifact in runtime_state_artifacts())


def projected_runtime_state_artifacts() -> tuple[RuntimeStateArtifact, ...]:
    return tuple(artifact for artifact in runtime_state_artifacts() if artifact.govengine_projection)
