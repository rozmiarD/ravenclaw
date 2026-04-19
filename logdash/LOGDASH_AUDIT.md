# Logdash Audit — 2026-03-10

## Summary

Logdash was partially broken after refactors. The main failures found during audit were:

1. startup crash due to missing global `STATE`
2. missing page routes (`/`, `/findings`, `/campaign-setup`, `/owner-actions`, `/system-settings`)
3. missing `/api/agents-status`, which caused the `Agentic Roles` tiles to render empty
4. frontend templates referencing many API endpoints that were no longer registered in `app.py`
5. stale UI block (`Runtime Logs`) removed by request, but related JS handlers remained temporarily

---

## Template → API audit

### `index.html`
Expected APIs:
- `/api/agents-status`
- `/api/campaign-info`
- `/api/campaign/control`
- `/api/family-yield`
- `/api/finding-quality`
- `/api/host-state`
- `/api/metrics`
- `/api/queue-state`
- `/api/runtime-health`
- `/api/runtime-state`

### `findings.html`
Expected APIs:
- `/api/campaign-info`
- `/api/family-yield`
- `/api/finding-quality`
- `/api/findings-table`
- `/api/host-explain`
- `/api/host-state`
- `/api/metrics`
- `/api/planner/candidate-targets`
- `/api/planner/runtime-plan-view`

### `campaign_setup.html`
Expected APIs:
- `/api/campaign-info`
- `/api/campaign/activate-from-blueprint`
- `/api/campaign/settings`
- `/api/campaign/validate-plan`
- `/api/planner-info`
- `/api/planner/approve`
- `/api/planner/campaigns`
- `/api/planner/selection`

### `owner_actions.html`
Expected APIs:
- `/api/campaign-info`
- `/api/campaign/control`
- `/api/campaign/delete-current`
- `/api/campaign/owner-override`
- `/api/campaign/settings`
- `/api/logs`
- `/api/logs/clear`
- `/api/owner-approvals`
- `/api/owner-approvals/approve-all`
- `/api/owner-approvals/delete-all`

### `system_settings.html`
Expected APIs:
- `/api/campaign-info`
- `/api/campaign/settings`
- `/api/pipeline-config`

---

## Missing backend routes found during audit

At audit time, these template-referenced endpoints were missing from live `app.py`:

- `/api/campaign-info`
- `/api/campaign/control`
- `/api/campaign/delete-current`
- `/api/campaign/owner-override`
- `/api/campaign/settings`
- `/api/family-yield`
- `/api/finding-quality`
- `/api/findings-table`
- `/api/host-explain`
- `/api/host-state`
- `/api/logs`
- `/api/logs/clear`
- `/api/metrics`
- `/api/owner-approvals`
- `/api/owner-approvals/approve-all`
- `/api/owner-approvals/delete-all`
- `/api/planner/campaigns`
- `/api/planner/selection`
- `/api/queue-state`
- `/api/runtime-health`
- `/api/runtime-state`

---

## Cleanup actions performed

- restored page routes
- restored `/api/agents-status`
- removed `Runtime Logs` block from `index.html`
- removed orphaned runtime-log button handlers from frontend JS
- restored core missing API surface required by templates
- prepared initial modularization of page and supplemental API registration
- split planner API into `api_planner.py`
- split runtime/status API into `api_runtime.py`
- added smoke tests for key pages and API routes

---

## Remaining recommendations

1. keep route registration split by concern (`pages`, `supplemental api`, later planner/runtime/logs)
2. move helper/state logic out of `app.py` into dedicated modules gradually
3. add CI to run Logdash smoke tests on each refactor
4. avoid template fetches to endpoints that do not have tests
