# Logdash

Logdash is the operator-facing dashboard and control plane for RAVENCLAW.

It began as a lightweight Flask + SQLite log viewer, but the live app now also coordinates planning visibility, runtime-plan generation, campaign activation, owner actions, system settings, and operator-visible runtime/evaluation truth surfaces.

---

## What Logdash does today

Logdash currently provides:

- pipeline and orchestrator log visibility,
- runtime campaign state display,
- campaign selection and activation,
- planner approval flow,
- candidate-target review and promotion,
- runtime-plan generation, validation, and document viewing,
- owner action / approval surfaces,
- pipeline flag and system-settings management,
- exploit-ladder / evidence-truth visibility,
- planner/runtime trace visibility,
- replay/evaluation governance summaries,
- persisted SQLite event browsing.

In short: it is no longer just a log viewer. It is the main operator control surface for the live RAVENCLAW runtime.

---

## Main files

- `app.py` — Flask app bootstrap / wiring root
- `services.py` — shared service helpers and canonical state projections used by API/control surfaces
- `state.py` — shared state/path helpers and state-loading glue
- `api_runtime.py` — runtime/control-plane API surface
- `api_planner.py` — planner/campaign-setup API surface
- `api_supplemental.py` — supplemental findings/metrics/trace/control-plane APIs
- `db.py` — SQLite helpers
- `log_event.py` — event ingestion helper for scripts/runtime
- `templates/` — operator UI pages
- `static/styles.css` — dashboard styling
- `logs.db` — local event store

---

## UI areas

Current dashboard pages include:

- **Pipeline Monitoring** — live runtime status, logs, and agent state
- **Findings** — findings review and candidate/finding workflows
- **Campaign Setup** — planner, scope, blueprint, runtime plan, activation flow
- **Owner Actions** — owner-gated actions and approvals
- **System Settings** — runtime/pipeline flags and related controls

---

## Important API capabilities

The live app exposes more than `/api/logs`.

Representative capabilities include:

- `GET /api/logs`
- `POST /api/logs/clear`
- `GET /api/campaign-info`
- `POST /api/campaign/control`
- `POST /api/campaign/settings` (includes campaign-scoped credentials and request-decoration state)
- `POST /api/campaign/owner-override`
- `POST /api/planner/approve`
- `POST /api/planner/promote-candidate-target`
- `GET /api/planner/candidate-targets`
- `POST /api/planner/review-candidate-target`
- `POST /api/planner/generate-runtime-plan`
- `GET /api/planner/runtime-plan-view`
- `GET /api/campaign/validate-plan`
- `POST /api/campaign/activate-from-blueprint`
- `GET /api/planner-info`
- `GET/POST /api/pipeline-config`
- `GET /api/pipeline-config/meta`
- `GET /api/pipeline-config/schema`

Treat the assembled Flask wiring (`app.py` + `api_*` modules) as the authoritative source for current endpoint coverage.

---

## Quick start

```bash
cd logdash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py --port 9091
```

If the runtime root should differ from the script checkout, export `RAVENCLAW_WORKSPACE=/path/to/workspace` before starting the app. Use `RAVENCLAW_REPORTS_DIR=/path/to/reports`, `RAVENCLAW_LOGDASH_DB=/path/to/logs.db`, and `RAVENCLAW_PIPELINE_CONFIG=/path/to/pipeline_config.json` when runtime state, SQLite storage, or pipeline configuration must live outside the checkout.

By default it binds to `127.0.0.1:9091`.

---

## Logging events from runtime/scripts

```bash
cd logdash
source .venv/bin/activate
python log_event.py \
  --tor "AUTO_CAMPAIGN" \
  --agent "auto_campaign" \
  --decision "fetch sitemap.xml" \
  --status success \
  --result "200 OK, 1.2 MB"
```

The helper auto-creates `logs.db` if needed.

---

## State integration

Logdash is tightly coupled to runtime state files under `reports/` and to shared helper/state code under `engine/` / `logdash/`.

Examples:
- `reports/.planner.ui.state.json`
- `reports/.campaign.settings.json`
- `reports/.orchestrator.state.json`
- `reports/.auto_campaign.state.json`
- `reports/.runtime_plan.meta.json`
- `reports/.host_state.json`
- `reports/.runtime_snapshot.json`
- `reports/state/public_targets_plan.json`

Compatibility note:
- legacy `engine/public_targets_plan.json` may still exist as a compatibility mirror during the Phase-6 transition.
- canonical generated-artifact path resolution should prefer `engine/paths.py` / shared helpers rather than endpoint-local path guesses.

Recent capability-architecture work also means operator-visible state now includes capability-aware queue previews, latest-run capability/intent lineage, and capability yield telemetry in addition to legacy family-level summaries.

Recent state-ownership cleanup also centralized selected-campaign snapshot filtering/projection into shared helpers so API endpoints do not each carry their own mismatch logic.

Earlier hardening work associated with the historical `1.0.0` line also tightened operator-visible truth contracts around:
- lifecycle control semantics for `start` / `resume` / `pause` / `stop` / `activate-from-blueprint`
- restart/recovery truth around stale PID cleanup and paused/stopped persistence
- source/provenance labels such as `runtime_snapshot_source`, `normalized_runtime_plan_meta`, `normalized_host_state_file`, and `empty_selected_campaign_queue`

Use `../references/logdash-operator-truth-contracts.md` as the short reference for those operator-facing semantics.

For the shared state catalog, see `../STATE_FILES.md`.

---

## Service / deployment notes

See `README-service.md` for the user-level systemd service workflow.

---

## Design notes

Logdash is intentionally not the executor.

It should:
- expose state,
- drive explicit control actions,
- surface owner approvals,
- make runtime decisions inspectable.

Current rule of thumb:
- endpoint code should prefer shared `services.py` / `state.py` helper paths over ad hoc file-topology logic where possible.

It should not silently become a second execution engine with duplicated business logic.

---

## Documentation status

If this README disagrees with the current Flask wiring or shared service/state helpers, trust the live code path first and update this file.
