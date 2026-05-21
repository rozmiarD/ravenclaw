# Runtime artifact ownership

This is the short reference for generated runtime artifact ownership in the current production path.
Use this when deciding where new runtime state should live, or when reading code that still touches legacy mirror files.

## Canonical rule
Generated runtime artifacts should use canonical paths from `engine/paths.py`.
Do not hard-code `engine/` artifact paths as preferred read/write targets.
`engine/runtime_state_truth.py` is the public manifest for the persisted state
and compatibility paths that the docs must continue to describe.

Primary canonical examples:
- runtime task list: `reports/state/public_targets_plan.json`
- pipeline context cache: `reports/cache/context_summary.json`

## Why legacy mirrors still exist
Two older engine-local files may still appear during the transition:
- `engine/public_targets_plan.json`
- `engine/context_summary.json`

These are legacy compatibility mirrors.
They exist so older readers and transition-era code paths do not break abruptly.
They are not the preferred source of truth.

## Ownership summary
- `engine/paths.py` defines canonical generated-artifact paths.
- `engine/runtime_plan_service.py` owns the canonical runtime-plan artifact flow.
- `engine/run_pipeline.py` and `engine/pipeline_context.py` own the canonical context-summary cache flow.
- docs should describe canonical `reports/state/` and `reports/cache/` ownership first, then mention engine-local mirrors only as compatibility notes.

## Read/write guidance
When touching generated runtime artifacts:
1. prefer canonical path resolution via `engine/paths.py`
2. document ownership explicitly if a compatibility mirror remains
3. avoid introducing new endpoint-local or module-local path guesses
4. avoid creating new engine-local mirrors unless a bounded compatibility need is explicit

## Repo posture rule
`reports/campaign_registry/` is durable planner history.
Most other generated runtime artifacts under `reports/` are local runtime/control-plane state or generated caches.
Do not blur those categories in docs or code comments.

## Current references
- `engine/RUNTIME_MANIFEST.md`
- `README.md`
- `ARCHITECTURE.md`
- `STATE_FILES.md`
- `engine/paths.py`
