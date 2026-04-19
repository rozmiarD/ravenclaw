# Logdash Full UI Pass — 2026-03-10

## Scope
Full pass over all major Logdash tabs after the pipeline/runtime refactor:
- Pipeline monitoring
- Findings
- Campaign setup
- Owner actions
- System settings

## Main issues found

### 1. Old planner/document actions remained in UI after pipeline refactor
`campaign_setup.html` still expected planner/document endpoints that were no longer registered.

Fixed by restoring:
- `/api/planner/run`
- `/api/planner/scope-view`
- `/api/planner/blueprint-view`
- `/api/planner/budgets-view`

### 2. `campaign-info` semantics drifted from runtime-plan reality
The UI could show stale/incorrect readiness because `campaign-info` did not expose enough post-refactor runtime-plan state.

Fixed by adding/normalizing:
- `planner_scope_targets`
- `prepared_attacks`
- `runtime_plan_ok`
- `runtime_plan_error_preview`
- `runtime_plan_revision`
- `runtime_plan_quality_grade`
- `runtime_plan_quality_score`

### 3. Labels overstated precision of derived placeholder metrics
Several cards still used terms like “findings”, “critical findings”, “CVSS”, or “stage” where the backend only exposed derived or simplified telemetry.

Adjusted wording across tabs to make it clear when values are:
- displayed only,
- derived,
- rendered summaries,
- runtime-state indicators,
- not yet true evidence-grade findings.

### 4. Findings/host views assumed fields that may be absent after refactor
Host-state display assumed `evidence_density` and other optional fields.

Fixed by making those labels/strings conditional.

## UI wording changes

### Pipeline monitoring
Examples:
- `Total findings` -> `Observed items`
- `Critical findings` -> `Error-class items`
- `Avg confidence` -> `Derived confidence`
- `Highest CVSS` -> `Derived CVSS max`
- `Current stage` -> `Runtime state`
- `Queue` -> `Remaining run budget`
- `Severity distribution` -> `Derived severity mix`

### Findings
Examples:
- `Total findings` -> `Displayed items`
- `Critical findings` -> `Derived high severity`
- `Confidence / CVSS` -> `Derived confidence / CVSS`
- table headers renamed to indicate rendered/derived values

### Campaign setup
Examples:
- `Scope weight` -> `Targets / tasks`
- `Last planner result` -> `Planner status`
- `Readiness` -> `Activation readiness`
- `Recommended lvl` -> `Recommended aggression`
- `LLM confidence` -> `Interpretation confidence`
- `Conflicts / ambiguities` -> `Planner conflicts / ambiguities`

## Remaining long-term recommendations

1. Replace placeholder/derived metrics with stricter findings/evidence contracts.
2. Add frontend contract tests for user-visible labels tied to specific payload fields.
3. Add “derived” badges/tooltips anywhere metrics are not raw evidence.
4. Continue aligning UI language with runtime truth whenever pipeline schemas evolve.
