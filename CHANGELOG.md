# RAVENCLAW — CHANGELOG.md

## Unreleased
- Raised the GovEngine dependency floor to `govengine>=0.1.4,<0.2` after the public surface registry line was published and verified from PyPI; public install validation now checks the expected GovEngine surface registry shape.
- Raised the GovEngine dependency floor to `govengine>=0.1.3,<0.2` after the artifact-governance control-gate line was published and verified from PyPI.
- Added a GovEngine artifact-governance control-gate adapter for the approved-spec execution path, consuming GovEngine lifecycle/signing/state/execution gates while retaining a defensive unavailable fallback for unsupported local environments.
- Moved Ravenclaw signal, analysis, and evidence-policy seams behind GovEngine compatibility aliases; the current GovEngine dependency floor is `govengine>=0.1.4,<0.2`.
- Added public install validation via `scripts/validate_public_install.py`, clarified runtime-only vs dev/test install paths, and wired the public demo doctor to report dependency readiness.
- Added `references/public-safe-proof-walkthrough.md` plus a refreshed public `THREAT_MODEL.md` so reviewers can follow the dry-run proof trace, trusted-core boundaries, and non-claims from committed artifacts.
- Switched Ravenclaw's public dependency metadata from Git URL pins to the published PyPI packages `sclite-core>=0.2.1,<0.3` and the current `govengine>=0.1.4,<0.2` line.
- Added a multi-repository publication-readiness analysis for SCLite, GovEngine, and Ravenclaw, including recommended PyPI sequencing, versioning posture, and a deferred-adapter boundary.
- Added public-safe OODA receipt/evidence guidance for recording GovEngine control decisions as compact governance evidence without publishing raw stdout/stderr, command logs, private telemetry, or sensitive target details.
- Added a GovEngine OODA adapter seam test proving Ravenclaw host-runner logic can honor `pause`, `abort`, and `cooldown` decisions between approved-spec runner steps without moving live subprocess ownership into GovEngine.
- Added a runtime ExecutionTicket gate for the local approved-spec execution path: Ravenclaw now builds SCLite v0.2 lifecycle artifacts before local execution and requires the execution ticket to bind the exact execution contract shape.
- Updated Ravenclaw to consume SCLite v0.2 and emit a public-safe lifecycle chain alongside the legacy proof trace: `IntentContract`, v0.2 `PolicyDecision`, `ExecutionContract`, `ExecutionTicket`, v0.2 `ExecutionReceipt`, `EvidenceContract`, and a hash-linked `ArtifactChainManifest` verified by SCLite.
- Integrated Ravenclaw with external SCLite as the single Security Contract Layer core dependency, removed the embedded local contract-core copy, synchronized public schemas/proof fixtures from SCLite, updated validation/CI install paths, and planned engine extraction around the new package boundary.
- Added a carrier readiness packet template so future adapter proposals must state scope UX, redaction, command authority, contracts, validation, rollback, and public/private boundaries before implementation.
- Added a carrier readiness checklist for future OpenClaw/MCP/A2A work, preserving scope, redaction, command authority, provenance, channel-leakage, and non-claim gates.
- Added a docs/contracts-only OpenClaw adapter-prep contract map that preserves SCL non-claims without implementing an adapter.
- Added a committed proof-of-value scorecard fixture and validator under `examples/proof-of-value-scorecard/`.
- Added a schema-backed proof-of-value scorecard (`scripts/build_proof_of_value_scorecard.py`) for public-safe governance/reviewability benchmark dimensions.
- Added `PROOF_OF_VALUE.md` to frame Ravenclaw public value around governance, reviewability, and benchmark dimensions without claiming live exploit performance.
- Added a `reviewer-report` markdown format for `scripts/build_public_snapshot_manifest.py`, turning snapshot manifest checks into a ready-to-read public review artifact.
- Added `REVIEWER_VALIDATION_GUIDE.md` as a public-safe reviewer path linking validation commands, manifest evidence, quality signals, and non-claims.
- Added a schema-backed Public Snapshot Manifest (`schemas/public_snapshot_manifest.v0.1.schema.json`) that maps validation surfaces to concrete files in assembled public snapshots and fails on missing paths.
- Added a schema-backed Public Validation Surface Index contract (`schemas/public_validation_surface_index.v0.1.schema.json`) and reference documentation so validation-surface claims, non-claims, boundaries, and path checks are machine-checked.
- Added `--fail-on` preflight exit-code support to the Scope Fidelity report CLI.
- Added a local Scope Fidelity report CLI for generating schema-validated reports from prepared/approved spec JSON.
- Added public-safe Scope Fidelity report fixtures and validation coverage for exact, mismatch, and ambiguous target binding.
- Added a schema-backed Scope Fidelity report for local target-binding/request-shape hygiene checks.
- Moved public contract schema validation helpers behind `engine/security_contract_layer.py` so fixture and receipt validation share the SCL boundary.
- Added a public-safe Replayable Truth Runtime proof fixture plus deterministic fixture validation and documentation.
- Added schema/reference documentation for `security_contract_validation_receipt` v0.1 and made `scripts/run_security_contract_validation.py` validate receipts before emitting them.
- Fixed public snapshot CI packaging by including `scripts/run_pytest_slice.py`, which the GitHub Actions pytest matrix invokes for every validation slice.
- Added `scripts/run_security_contract_validation.py` as a local/public-safe Security Contract validation runner that emits a `security_contract_validation_receipt` across fixture validation, demo-bundle smoke, temporary public snapshot assembly, snapshot-local fixture validation, residue audit, and optional focused pytest checks.
- Hardened the Ravenclaw Security Contract OpenClaw Skill with workspace workflow, risk-based validation, clean publish-tree, source-of-truth, and stop-condition guardrails.
- Added a workspace OpenClaw Skill for Ravenclaw Security Contract proof validation, demo-bundle review, snapshot residue audit, and publish-safety checks.
- Added the exact Security Contract proof fixture validation command to `VALIDATION.md` for public readers.
- Included public demo container/compose/bootstrap scaffolding in the assembled public snapshot so snapshot-local validation exercises advertised demo surfaces.
- Added public snapshot residue audit tooling and remediated discovered public residue blockers in snapshot-pruned source/test surfaces.
- Included Security Contract Layer proof fixtures and validator in the assembled public snapshot, with a snapshot smoke test that validates copied fixtures from inside the snapshot.
- Added a committed public-safe Security Contract Layer fixture bundle under `examples/security-contract-proof/` plus `scripts/validate_security_contract_fixtures.py` and focused fixture validation tests.
- Strengthened `engine/security_contract_layer.py` with explicit proof-trace constants, manifest metadata, public-safety invariant validation, and demo-bundle assertion before artifact writes.
- Added `engine/security_contract_layer.py` as the internal boundary module for public-safe proof-trace artifact builders, thinning `engine/public_demo_bundle.py` back toward demo orchestration while preserving generated artifact shapes.
- Added schema-backed public-safe `EvidenceBundle` v0.1 output to the demo proof trace, including `evidence_bundle.json`, reference docs, validation tests, and explicit safety/non-claim fields for dry-run contract proof.
- Extended the Security Contract Layer proof path with standalone `PolicyDecision` v0.1 and public-safe `ExecutionReceipt` v0.1 schemas/reference docs, focused schema validation tests, and explicit dry-run contract-proof evidence criteria in `evidence_summary.md`.
- Started the Ravenclaw Contract Proof Sprint by adding the `SECURITY_CONTRACT_LAYER.md` concept, `ApprovedExecutionSpec` v0.1 schema/reference docs, schema-vs-live-output validation tests, a `PolicyDecision` v0.1 compatibility wrapper, and sanitized public demo proof-trace artifacts (`policy_decision.json`, `prepared_execution_spec.redacted.json`, `approved_execution_spec.json`, `execution_receipt.json`, `evidence_summary.md`).
- Advanced Track D demo UX/container ergonomics further by adding `engine/public_demo_bundle.py`, `bin/demo-bundle`, smarter bootstrap install caching plus `doctor`/`bundle` modes, a generated `demo-output/` artifact path, compose `demo-bundle` service, and devcontainer attach-time demo readiness hints — all still grounded in the same real `RAVENCLAW_MODE=demo` contract.
- Advanced Track D again by adding a reusable public bootstrap surface (`scripts/bootstrap_public_demo.sh`), `.devcontainer/`, and `compose.demo.yaml`, so the public-safe demo path now has local, devcontainer, and compose entry surfaces built on the same real `RAVENCLAW_MODE=demo` contract.
- Advanced Track D from a wrapper-only demo entry into a real delivery-mode slice: added `engine/public_delivery.py`, introduced explicit `demo/local/external` runtime + adapter metadata, wired `run_pipeline.py` and `plan_campaign.py` to surface delivery truth, and made `RAVENCLAW_MODE=demo` force a public-safe path with local planner/auditor seams plus explicit mock dry-run execution.
- Entered Track D with a bounded one-command public demo entry slice: added `bin/demo`, centralized the official demo command construction in `engine/demo_entry.py`, and updated `DEMO.md` so the public-safe demo path matches the real `run_pipeline.py --objective ... --dry-run` CLI surface.
- Closed the current Wave 2 trusted-core hardening slice by bringing `engine/policy_gateway.py` to executor parity for hidden/out-of-scope host detection across argv/stdin, including header-style host values and stdin-fed chain steps while preserving the `file://` false-positive fix.
- Added explicit tool-registry planner invocation metadata so tools that need non-direct invocation shapes (currently `hakrawler` as `stdin_target`) can be modeled explicitly instead of only via planner-local exceptions.
- Stopped planner fallbacks from emitting fake `hakrawler` argv shapes (`-url/-depth/-plain`) that do not match the installed CLI, and replaced them with a bounded stdin-aware adapter shape (`-d 2 -u` + URL on stdin).
- Normalized planner fallback target construction using tool-registry target kinds so URL-only tools get URL-form targets, host/domain-only tools get host-form targets, and DNS fallback no longer reuses `dig` argv shape for `nslookup`.
- Added policy-gateway parity for the new narrow tool-target semantics checks so selected public-safe tools now reject URL-vs-host target mismatches during evaluation as well as execution, including stdin-fed URL tools like `hakrawler` and compiled chain-step validation.
- Added bounded action-contract validation for `stdin` on both top-level specs and `tool_chain` steps, so the new stdin-target path cannot silently carry non-string, NUL-containing, or unbounded payloads.
- Added auditor/operator truth surfacing for stdin-fed execution steps: prepared-spec redaction now summarizes `stdin` instead of passing it through raw, and compact auditor specs explicitly show bounded `stdin` metadata for affected steps.
- Added execution-truth/input provenance for stdin-fed targets so approved execution specs and downstream lineage now explicitly distinguish argv-delivered targets from stdin-delivered ones without changing the legacy argv-only `command_preview` contract.
- Updated operator-facing postprocess summaries to surface bounded stdin-fed input context alongside the legacy argv command preview, so UI-facing run summaries are no longer misleading for tools like `hakrawler`.
- Moved strict target-shape enforcement into explicit tool-registry metadata (`target_validation_mode`) so policy-gateway and executor now read the same registry-backed validation model instead of maintaining local hardcoded tool sets.
- Deduplicated stdin preview/summary helper logic inside `engine/execution_contracts.py`, reducing one more local drift point in the stdin-target truth surfaces without changing behavior.
- Added `scripts/run_pytest_slice.py` and switched GitHub Actions pytest validation to a slice matrix (`contracts_policy`, `auto_campaign`, `runtime_core`, `runtime_runner`, `logdash`, `misc_public`) so broad regression coverage stays stable without depending on one wall-time-heavy monolithic batch.
- Added a narrow executor-side tool-target semantics pass for selected public-safe tools, using registry target kinds plus current repo usage patterns to reject URL-vs-host mismatches (for example `gau` receiving a URL, `katana` receiving only a bare host, or `hakrawler` missing its stdin-fed URL target) without disturbing existing `file://` approved-spec flows.
- Extended the Wave 2 trusted-core slice again using real tool help surfaces for `gau`, `hakrawler`, `dnsx`, and `subfinder`, adding file/config/proxy/output restrictions where appropriate and expanding policy/executor adversarial tests around those misuse paths.
- Extended the Wave 2 trusted-core slice further by adding restricted-argument coverage for additional public-safe tools (`katana`, `nikto`, `whatweb`) and expanding executor/policy-core tests around proxy/log/config-style misuse patterns.
- Extended the Wave 2 trusted-core slice by adding `THREAT_MODEL.md`, linking it from the front-door docs, and tightening executor scope enforcement so out-of-scope hosts hidden inside header-style values or bare-domain tokens are rejected during execution-time checks.
- Started the first Wave 2 trusted-core hardening slice by shrinking the public runtime execution surface in `engine/policy_core.py`, blocking operator-shell/high-risk tooling from the default runtime path, adding first-pass per-tool restricted-argument checks, and extending executor/policy tests for the new public-safe boundary.
- Cleaned remaining active-version drift in `VERSION_ROADMAP.md`, `references/logdash-operator-truth-contracts.md`, and `logdash/README.md` so the repo distinguishes the current `0.10.0` public package signal from historical `1.0.0`-line hardening work more clearly.
- Started Wave 1 of the 2026-04-23 public-core/trust roadmap by tightening front-door public truth, adding an explicit `public core vs private overlay` boundary document, downgrading package release signaling from `1.0.0` to `0.10.0`, and replacing `engine/brain.py`'s placeholder posture with an honest adapter seam plus deterministic fallback behavior.
- Completed the final publication pass by adding `PUBLISHING.md`, extending the public snapshot assembly path to carry the new front-door/public-trust docs, and recording a pass-with-cautions publication verdict that recommends publishing from an assembled snapshot rather than directly from the live workspace.
- Completed Wave D of the priority public-repo elevation plan by improving public product shape and navigation, adding `AUDIENCE.md` and `DOCS_MAP.md`, and updating `README.md` to explain who the repo is for, who it is not for, and how different readers should traverse the documentation.
- Completed Wave C of the priority public-repo elevation plan by adding explicit public trust and validation surfaces through `QUALITY_SIGNALS.md` and `VALIDATION.md`, and by updating `README.md` and `PUBLIC_STATUS.md` so readers can find concrete CI, test, and contract evidence without inferring repo quality from tone alone.
- Completed Wave B of the priority public-repo elevation plan by defining an official public-safe local dry-run path, adding `INSTALL.md`, `ENVIRONMENT_SUPPORT.md`, and `DEMO.md`, and refreshing `README.md` to point readers to one honest supported setup/demo route instead of implying a broader public deployment story than the repo currently supports.
- Started the priority public-repo elevation plan by completing Wave A front-door documentation work: rewrote `README.md` as a clearer public entry surface and added `PUBLIC_STATUS.md`, `ARCHITECTURE_OVERVIEW.md`, and `WHY_RAVENCLAW.md` to separate maturity truth, short architecture orientation, and project thesis from the deeper operator/developer docs.
- Completed the final public snapshot review with a pass-with-warnings verdict, hardening the assembly path further to exclude `engine/context_summary.json`, `engine/public_targets_plan.json`, `logdash/logdash.out`, and `logdash/.venv` from the assembled public tree.
- Completed open-source/public-release prep Wave 5 by hardening the public-snapshot assembly path with noise pruning, safe placeholder examples, and explicit `auth-harness/` caution.
- Completed open-source/public-release prep Wave 4 by adding an applied public-snapshot assembly scaffold (`scripts/assemble_public_snapshot.sh`, `public-snapshot/`) without publishing or scrubbing the live workspace.
- Completed open-source/public-release prep Wave 3 by adding a concrete public snapshot plan and manifest draft covering keep/exclude/replace decisions.
- Completed open-source/public-release prep Wave 2 by adding a repository publication review matrix and public-snapshot checklist for mixed local/internal areas.
- Started open-source/public-release prep with a first wave covering publication-boundary guidance plus root-level repository hygiene files (`LICENSE`, `CODE_OF_CONDUCT.md`).
- Added a short post-`1.0.0` release checklist and cleaned up one stale pre-bump phrasing in the `1.0.0` release-note blurb.

## 1.0.0 / 2026-04-18

- Completed a bounded final `1.0.0` confidence pass revalidating control, recovery, ownership, smoke, and operator-truth-doc alignment before the version bump.
- Added a bounded `1.0.0` readiness verdict concluding that the planned hardening themes were materially covered and that no obvious mandatory Wave 5 blocker remained.
- Completed Hardening Wave 4 by adding a short operator-facing truth-contract reference and refreshing README guidance for control semantics, recovery truth, and source-label interpretation.
- Completed Hardening Wave 3 by clarifying operator-visible source ownership labels for queue, host-state, and runtime-plan fallback payloads, plus focused provenance regression coverage.
- Completed Hardening Wave 2 by adding direct restart/recovery regression coverage for stale PID cleanup, paused-state persistence, and stopped-state precedence in runtime-state refresh behavior.
- Completed Hardening Wave 1 by adding focused control-path regression coverage and explicit runtime lifecycle dependency hooks for operator-facing start/resume/pause/stop and activation behavior.
- Added a `1.0.0` release note blurb and updated packaging/docs release surfaces so the repo now reports the `1.0.0` milestone consistently.
- Closed the post-`0.9.0` cleanup stream after bounded Stages D-H and followed it with a separate `1.0.0` hardening track focused on control-path validation, restart predictability, operator-visible state ownership, and release-quality docs.
- Stage H completed: adopted shared selected-campaign projection helpers in planner/runtime APIs and aligned residual truth fixtures with the tightened context contract.
- Stage G completed: consolidated selected-campaign projection helpers and unified snapshot-aware source labeling across LogDash supplemental API surfaces.
- Completed post-`0.9.0` Stage F as a bounded shared services/API normalized-loader adoption arc across `logdash/services.py` and `logdash/api_supplemental.py`.
- Replaced high-traffic raw JSON readers for runtime state, runtime-plan meta, queue state, host state, owner approval actions, planner registry metadata, latest-run payloads, archive helper reads, and selected snapshot/delete-current fallback paths with shared normalized loaders.
- Tightened provenance labels to distinguish normalized state-backed sources such as `normalized_auto_campaign_state`, `normalized_runtime_plan_meta`, `normalized_host_state_file`, and `normalized_queue_state`, and added focused regression coverage for normalized-reader behavior and invalid JSON tolerance.
- Completed post-`0.9.0` Stage E as a bounded selective compatibility-reduction arc across planner/control-plane and runtime/config JSON readers.
- Added `logdash/planner_registry_loader.py` and replaced selected raw planner/runtime/config JSON parsing with shared normalized loaders, reducing silent fallback behavior in planner validation, planner info, pipeline config, feature-flag manifest, and agent-model loading paths.
- Surfaced additional provenance metadata including planner runtime-plan validation `source` and planner-info `blueprint_source`, while adding focused regression coverage for invalid JSON tolerance and normalized-reader behavior.
- Completed post-`0.9.0` Stage D as a bounded truth-surface tightening arc across Logdash services and runtime-trace payload assembly.
- Added explicit provenance/source metadata for normalized runtime-state and host-state reads, making file-backed, computed-fallback, snapshot-normalized, and legacy-runtime-vector truth surfaces easier to distinguish.
- Extracted shared runtime-trace normalization helpers and exposed `trace_sources` metadata so ladder/decision fallback precedence is operator-visible instead of being buried in local payload assembly.

## 0.9.0 / 2026-04-17

- Closed the `0.9.0` readiness audit loop across runner structure, planner→runtime→execution contracts, runtime artifact/state ownership, and Logdash/operator truth surfaces.
- Settled the release posture for `0.9.0` as a stabilization and truth-hardening milestone: the architecture is now treated as defensible, with remaining debt bounded to downstream cleanup, provenance tightening, and compatibility reduction rather than rescue refactoring.
- Updated core release framing in `README.md` and `VERSION_ROADMAP.md` so milestone language matches current runtime reality and avoids overstating single-surface cleanliness or complete legacy removal.
- Advanced Stage 4 runtime economics/explainability from partial backend support to a coherent operator-facing projection layer: runtime explainability summaries now flow through `finding-quality`, family/capability/host efficiency all expose explicit economics-style yield APIs, and Logdash dashboard/findings panels now render aligned short-form "why" context instead of only raw scores.
- Added explicit `/api/capability-yield` and `/api/host-yield` projections plus host-state `explain` summaries, closing a control-plane/API drift gap and making family/capability/host introspection use the same ranking model.
- Revalidated the new Stage 4 surfaces with focused Logdash + runtime economics regression coverage, keeping snapshot/legacy projection behavior green while expanding operator-visible explainability.
- Started Wave A2 as the next post-Stage-4 `0.9.0` structural slice and thinned additional runner-owned canonical helpers instead of starting a broad refactor.
- Extracted runtime-task normalization into `engine/runtime_task_normalization.py`, leaving the runner with a thin normalization facade while preserving existing facade tests.
- Confirmed `summarize_result(...)` already lives behind `engine/runtime_runner_result_summary.py` as a thin facade seam, then continued A2 by extracting post-run admission shaping into `engine/runtime_runner_post_run_admission.py` and the remaining post-run orchestration facade into `engine/runtime_runner_post_run_flow.py`.
- Revalidated the A2 tranche with focused runner-facade / helper / Logdash smoke coverage, keeping the bounded runner-thinning path green while reducing more business logic inside `engine/auto_campaign_runner.py`.
- Closed milestone confirmation through C1/C2: recorded a fresh green regression pass, confirmed docs/release-truth alignment, and added an explicit `0.9.0` release decision plus bounded residual backlog instead of reopening broad structural work.

## 0.8.119 / 2026-04-17

- Added `VERSION_ROADMAP.md` as the canonical release-planning guide from the current `0.8.x` line through `2.0.0`.
- Linked the version roadmap from `README.md` and `ARCHITECTURE.md` so milestone thresholds remain visible in both project overview and production-architecture context.

## 0.8.118 / 2026-04-17

- Revalidated the bounded Phase B3 runner-thinning series across Waves 47-66 with a full `pytest -q engine/tests` regression pass, confirming green engine coverage after the wrapper extraction tranche.
- Audited series documentation and confirmed complete closeout/report coverage for Waves 47-66 in `reports/` plus retained implementation plans for the tranche in `implementation-plans/`.
- Verified the production worktree is clean aside from a local untracked memory note, leaving the runtime ready for the next bounded extraction wave.

## 0.8.117 / 2026-04-12

- Completed Wave 66 as a bounded Phase B3 runner-thinning tranche, extracting runtime precheck-context wrapper assembly into `engine/runtime_runner_precheck_context_wrapper.py`.
- Preserved runner compatibility with a thin `_build_runtime_precheck_context_inputs(...)` wrapper in `engine/auto_campaign_runner.py` while keeping precheck-context wiring independently testable.
- Added direct regression coverage for the extracted precheck-context wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.116 / 2026-04-12

- Completed Wave 65 as a bounded Phase B3 runner-thinning tranche, extracting queue-coordinator wrapper assembly into `engine/runtime_runner_queue_coordinator_wrapper.py`.
- Preserved runner compatibility with a thin `_build_queue_coordinator(...)` wrapper in `engine/auto_campaign_runner.py` while keeping queue-coordinator wiring independently testable.
- Added direct regression coverage for the extracted queue-coordinator wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.115 / 2026-04-12

- Completed Wave 64 as a bounded Phase B3 runner-thinning tranche, extracting complete-run inputs wrapper assembly into `engine/runtime_runner_complete_run_inputs_wrapper.py`.
- Preserved runner compatibility with a thin `_build_complete_runtime_run_inputs(...)` wrapper in `engine/auto_campaign_runner.py` while keeping complete-run input wiring independently testable.
- Added direct regression coverage for the extracted complete-run-inputs wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.114 / 2026-04-12

- Completed Wave 63 as a bounded Phase B3 runner-thinning tranche, extracting execute-task inputs wrapper assembly into `engine/runtime_runner_execute_task_inputs_wrapper.py`.
- Preserved runner compatibility with a thin `_build_execute_runtime_task_inputs(...)` wrapper in `engine/auto_campaign_runner.py` while keeping execute-task input wiring independently testable.
- Added direct regression coverage for the extracted execute-task-inputs wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.113 / 2026-04-12

- Completed Wave 62 as a bounded Phase B3 runner-thinning tranche, extracting session-bundle inputs wrapper assembly into `engine/runtime_runner_session_bundle_inputs_wrapper.py`.
- Preserved runner compatibility with a thin `_build_runtime_session_bundle_inputs(...)` wrapper in `engine/auto_campaign_runner.py` while keeping session-bundle input wiring independently testable.
- Added direct regression coverage for the extracted session-bundle-inputs wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.112 / 2026-04-12

- Completed Wave 61 as a bounded Phase B3 runner-thinning tranche, extracting record/persist stage wrapper assembly into `engine/runtime_runner_record_persist_stage_wrapper.py`.
- Preserved runner compatibility with a thin `_run_record_and_persist_stage(...)` wrapper in `engine/auto_campaign_runner.py` while keeping record/persist stage wiring independently testable.
- Added direct regression coverage for the extracted record/persist stage wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.111 / 2026-04-12

- Completed Wave 60 as a bounded Phase B3 runner-thinning tranche, extracting execution-stage pass-through wrapper assembly into `engine/runtime_runner_execution_stage_passthrough_wrapper.py`.
- Preserved runner compatibility with a thin `_run_main_execution_stage(...)` wrapper in `engine/auto_campaign_runner.py` while keeping execution-stage pass-through wiring independently testable.
- Added direct regression coverage for the extracted execution-stage pass-through seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.110 / 2026-04-12

- Completed Wave 59 as a bounded Phase B3 runner-thinning tranche, extracting persist-callbacks pass-through wrapper assembly into `engine/runtime_runner_persist_callbacks_passthrough_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_persist_callbacks(...)` wrapper in `engine/auto_campaign_runner.py` while keeping persist-callback pass-through wiring independently testable.
- Added direct regression coverage for the extracted persist-callbacks pass-through seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.109 / 2026-04-12

- Completed Wave 58 as a bounded Phase B3 runner-thinning tranche, extracting planner-callback pass-through wrapper assembly into `engine/runtime_runner_planner_callbacks_passthrough_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_planner_callbacks(...)` wrapper in `engine/auto_campaign_runner.py` while keeping planner callback pass-through wiring independently testable.
- Added direct regression coverage for the extracted planner-callbacks pass-through seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.108 / 2026-04-12

- Completed Wave 57 as a bounded Phase B3 runner-thinning tranche, extracting state-aliases wrapper assembly into `engine/runtime_runner_state_aliases_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_state_aliases(...)` wrapper in `engine/auto_campaign_runner.py` while keeping state-alias wiring independently testable.
- Added direct regression coverage for the extracted state-aliases wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.107 / 2026-04-12

- Completed Wave 56 as a bounded Phase B3 runner-thinning tranche, extracting skip-summary flusher wrapper assembly into `engine/runtime_runner_skip_flusher_wrapper.py`.
- Preserved runner compatibility with a thin `_make_skip_summary_flusher(...)` wrapper in `engine/auto_campaign_runner.py` while keeping skip-summary flusher wiring independently testable.
- Added direct regression coverage for the extracted skip-summary flusher wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.106 / 2026-04-12

- Completed Wave 55 as a bounded Phase B3 runner-thinning tranche, extracting skip-summary builder wrapper assembly into `engine/runtime_runner_skip_summary_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_skip_summary_flushers(...)` wrapper in `engine/auto_campaign_runner.py` while keeping skip-summary builder wiring independently testable.
- Added direct regression coverage for the extracted skip-summary wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.105 / 2026-04-12

- Completed Wave 54 as a bounded Phase B3 runner-thinning tranche, extracting runtime-overrides wrapper assembly into `engine/runtime_runner_overrides_wrapper.py`.
- Preserved runner compatibility with a thin `_refresh_main_runtime_overrides(...)` wrapper in `engine/auto_campaign_runner.py` while keeping runtime override wiring independently testable.
- Added direct regression coverage for the extracted runtime-overrides wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.104 / 2026-04-12

- Completed Wave 53 as a bounded Phase B3 runner-thinning tranche, extracting runtime snapshot wrapper assembly into `engine/runtime_runner_snapshot_wrapper.py`.
- Preserved runner compatibility with a thin `_persist_main_runtime_snapshot(...)` wrapper in `engine/auto_campaign_runner.py` while keeping runtime snapshot wiring independently testable.
- Added direct regression coverage for the extracted runtime-snapshot wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.103 / 2026-04-12

- Completed Wave 52 as a bounded Phase B3 runner-thinning tranche, extracting prepare-callback wrapper assembly into `engine/runtime_runner_prepare_callbacks_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_prepare_callbacks(...)` wrapper in `engine/auto_campaign_runner.py` while keeping prepare-callback wiring independently testable.
- Added direct regression coverage for the extracted prepare-callback wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.102 / 2026-04-12

- Completed Wave 51 as a bounded Phase B3 runner-thinning tranche, extracting post-run actions wrapper assembly into `engine/runtime_runner_post_run_actions_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_post_run_actions_callback(...)` wrapper in `engine/auto_campaign_runner.py` while keeping post-run callback wiring independently testable.
- Added direct regression coverage for the extracted post-run-actions wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.101 / 2026-04-12

- Completed Wave 50 as a bounded Phase B3 runner-thinning tranche, extracting precheck-hook wrapper assembly into `engine/runtime_runner_precheck_hooks_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_precheck_hooks(...)` wrapper in `engine/auto_campaign_runner.py` while keeping precheck-hook pass-through wiring independently testable.
- Added direct regression coverage for the extracted precheck-hooks wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.100 / 2026-04-12

- Completed Wave 49 as a bounded Phase B3 runner-thinning tranche, extracting runtime-callback wrapper assembly into `engine/runtime_runner_runtime_callbacks_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_runtime_callbacks(...)` wrapper in `engine/auto_campaign_runner.py` while keeping runtime-callback pass-through wiring independently testable.
- Added direct regression coverage for the extracted runtime-callback wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.99 / 2026-04-12

- Completed Wave 48 as a bounded Phase B3 runner-thinning tranche, extracting session-setup wrapper wiring into `engine/runtime_runner_session_setup_wrapper.py`.
- Preserved runner compatibility with thin `_build_main_session_base_fields(...)`, `_build_main_session_alias_fields(...)`, and `_build_main_session_setup(...)` wrappers in `engine/auto_campaign_runner.py` while keeping session-setup pass-through wiring independently testable.
- Added direct regression coverage for the extracted session-setup wrapper cluster and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.98 / 2026-04-12

- Completed Wave 47 as a bounded Phase B3 runner-thinning tranche, extracting execute-task callback wrapper assembly into `engine/runtime_runner_execute_task_callback_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_execute_runtime_task_callback(...)` wrapper in `engine/auto_campaign_runner.py` while keeping task callback dependency stitching independently testable.
- Added direct regression coverage for the extracted execute-task wrapper seam and revalidated the touched runner plus adjacent completion/entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.97 / 2026-04-12

- Completed Wave 46 as a bounded Phase B3 runner-thinning tranche, extracting execute-pipeline completion handoff into `engine/runtime_runner_execute_completion_wrapper.py`.
- Preserved runner compatibility with a thin `_complete_execute_runtime_pipeline_result(...)` wrapper in `engine/auto_campaign_runner.py` while keeping completion handoff independently testable.
- Added direct regression coverage for the extracted completion-wrapper seam and revalidated the touched runner plus adjacent entry/execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.96 / 2026-04-12

- Completed Wave 45 as a bounded Phase B3 runner-thinning tranche, extracting top-level main-entry orchestration into `engine/runtime_runner_main_entry.py`.
- Preserved runner compatibility with a thin `main()` facade in `engine/auto_campaign_runner.py` while keeping high-level entry wiring independently testable.
- Added direct regression coverage for the extracted main-entry seam and revalidated the touched runner plus adjacent execution/bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.95 / 2026-04-12

- Completed Wave 44 as a bounded Phase B3 runner-thinning tranche, extracting the top-level execution-stage wrapper into `engine/runtime_runner_execution_stage_runner.py`.
- Preserved runner compatibility with a thin `_run_main_execution_stage(...)` wrapper in `engine/auto_campaign_runner.py` while keeping execution-stage orchestration independently testable.
- Added direct regression coverage for the extracted execution-stage wrapper seam and revalidated the touched runner plus adjacent bootstrap/planner/callback/session slices locally without behavior changes.

## 0.8.94 / 2026-04-12

- Completed Wave 43 as a bounded Phase B3 runner-thinning tranche, extracting runtime bootstrap loading into `engine/runtime_runner_bootstrap_loader.py`.
- Preserved runner compatibility with a thin `_load_runtime_session_bootstrap()` wrapper in `engine/auto_campaign_runner.py` while keeping startup-loading logic independently testable.
- Added direct regression coverage for the extracted bootstrap-loader seam and revalidated the touched runner plus adjacent callback/builder/session slices locally without behavior changes.

## 0.8.93 / 2026-04-12

- Completed Wave 42 as a bounded Phase B3 runner-thinning tranche, extracting planner callback wrapper assembly into `engine/runtime_runner_planner_callback_wrapper.py`.
- Preserved runner compatibility with a thin `_build_main_planner_callbacks(...)` wrapper in `engine/auto_campaign_runner.py` while keeping planner dependency stitching independently testable.
- Added direct regression coverage for the extracted planner-wrapper seam and revalidated the touched runner plus adjacent callback/builder/session slices locally without behavior changes.

## 0.8.92 / 2026-04-12

- Completed Wave 41 as a bounded Phase B3 runner-thinning tranche, extracting runtime session-state bootstrap/build helpers into `engine/runtime_runner_session_state_builders.py`.
- Preserved runner compatibility with thin `_build_runtime_session_state_from_bootstrap(...)` and `build_runtime_session_state()` wrappers in `engine/auto_campaign_runner.py` while keeping session-state construction independently testable.
- Added direct regression coverage for the extracted session-state builder seam and revalidated the touched runner plus adjacent callback/builder/session slices locally without behavior changes.

## 0.8.91 / 2026-04-12

- Completed Wave 40 as a bounded Phase B3 runner-thinning tranche, extracting post-run-actions callback assembly into `engine/runtime_runner_post_run_callback.py`.
- Preserved runner compatibility with a thin `_build_main_post_run_actions_callback(...)` wrapper in `engine/auto_campaign_runner.py` while keeping closure wiring independently testable.
- Added direct regression coverage for the extracted post-run callback seam and revalidated the touched runner plus adjacent alias/builder/callback/session slices locally without behavior changes.

## 0.8.90 / 2026-04-12

- Completed Wave 39 as a bounded Phase B3 runner-thinning tranche, extracting state-alias and skip-summary flusher helpers into `engine/runtime_runner_state_aliases.py`.
- Preserved runner compatibility with thin `_build_main_state_aliases(...)`, `_make_skip_summary_flusher(...)`, and `_build_main_skip_summary_flushers(...)` wrappers in `engine/auto_campaign_runner.py` while keeping alias/flusher seams independently testable.
- Added direct regression coverage for the extracted state-alias/flusher seam and revalidated the touched runner plus adjacent builder/callback/session slices locally without behavior changes.

## 0.8.89 / 2026-04-12

- Completed Wave 38 as a bounded Phase B3 runner-thinning tranche, extracting task-execution builder helpers into `engine/runtime_runner_task_execution_builders.py`.
- Preserved runner compatibility with thin `_build_post_run_action_inputs(...)`, `_build_execute_runtime_task_inputs(...)`, and `_run_record_and_persist_stage(...)` wrappers in `engine/auto_campaign_runner.py` while keeping execution-side builder seams injection-based and independently testable.
- Added direct regression coverage for the extracted task-execution builder seam and revalidated the touched runner, task-execution-builders, bundle-builders, execution-stage, persist-callback, runtime-callback, session-setup, and facade slices locally without behavior changes.

## 0.8.88 / 2026-04-12

- Completed Wave 37 as a bounded Phase B3 runner-thinning tranche, extracting compact runtime bundle builders into `engine/runtime_runner_bundle_builders.py`.
- Preserved runner compatibility with thin queue/precheck/deps/session-bundle wrapper helpers in `engine/auto_campaign_runner.py` while keeping builder seams injection-based and independently testable.
- Added direct regression coverage for the extracted builder seam and revalidated the touched runner, bundle-builders, execution-stage, persist-callback, runtime-callback, session-setup, and facade slices locally without behavior changes.

## 0.8.87 / 2026-04-12

- Completed Wave 36 as a bounded Phase B3 runner-thinning tranche, extracting execution-stage input assembly into `engine/runtime_runner_execution_stage.py`.
- Preserved runner compatibility with thin `_build_execute_runner_session_inputs(...)` and `_build_finalize_runner_exception_inputs(...)` wrappers in `engine/auto_campaign_runner.py` while keeping execution-stage dependency wiring injection-based and independently testable.
- Added direct regression coverage for the extracted execution-stage seam and revalidated the touched runner, execution-stage, persist-callback, runtime-callback, session-setup, and facade slices locally without behavior changes.

## 0.8.86 / 2026-04-12

- Completed Wave 35 as a bounded Phase B3 runner-thinning tranche, extracting persist callback and service assembly into `engine/runtime_runner_persist_callbacks.py`.
- Preserved runner compatibility with thin `_build_runtime_persist_services(...)`, `_build_record_and_persist_run_inputs(...)`, and `_build_main_persist_callbacks(...)` wrappers in `engine/auto_campaign_runner.py` while keeping persistence-stage dependency wiring injection-based and independently testable.
- Added direct regression coverage for the extracted persist seam and revalidated the touched runner, persist-callback, runtime-callback, session-setup, completion, prepare-callback, planner-callback, controls, follow-up policy, and queue slices locally without behavior changes.

## 0.8.85 / 2026-04-12

- Completed Wave 34 as a bounded Phase B3 runner-thinning tranche, extracting runtime callback assembly into `engine/runtime_runner_runtime_callbacks.py`.
- Preserved runner compatibility with thin `_persist_main_runtime_snapshot(...)`, `_refresh_main_runtime_overrides(...)`, `_build_main_runtime_callbacks(...)`, and `_build_main_precheck_hooks(...)` wrappers in `engine/auto_campaign_runner.py` while keeping snapshot persistence, override refresh, queue wiring, and precheck-hook dependencies injection-based and independently testable.
- Added direct regression coverage for the extracted runtime-callback seam and revalidated the touched runner, runtime-callbacks, session-setup, completion, prepare-callback, planner-callback, controls, follow-up policy, and queue slices locally without behavior changes.

## 0.8.84 / 2026-04-12

- Completed Wave 33 as a bounded Phase B3 runner-thinning tranche, extracting main session-setup assembly into `engine/runtime_runner_session_setup.py`.
- Preserved runner compatibility with thin `_build_main_session_base_fields(...)`, `_build_main_session_alias_fields(...)`, and `_build_main_session_setup(...)` wrappers in `engine/auto_campaign_runner.py` while keeping controls and queue-coordinator dependency seams injection-based and independently testable.
- Added direct regression coverage for the extracted session-setup seam and revalidated the touched runner, session-setup, completion, prepare-callback, planner-callback, controls, follow-up policy, and queue slices locally without behavior changes.

## 0.8.83 / 2026-04-12

- Completed Wave 32 as a bounded Phase B3 runner-thinning tranche, extracting runtime completion-callback assembly into `engine/runtime_runner_completion_callbacks.py`.
- Preserved runner compatibility with thin `_build_complete_runtime_run_inputs(...)`, `_complete_execute_runtime_pipeline_result(...)`, and `_build_main_execute_runtime_task_callback(...)` wrappers in `engine/auto_campaign_runner.py` while keeping pipeline/completion dependency seams injection-based and independently testable.
- Added direct regression coverage for the extracted completion seam and revalidated the touched runner, completion, prepare-callback, planner-callback, controls, follow-up policy, and queue slices locally without behavior changes.

## 0.8.82 / 2026-04-12

- Completed Wave 31 as a bounded Phase B3 runner-thinning tranche, extracting planner-callback assembly into `engine/runtime_runner_planner_callbacks.py`.
- Preserved runner compatibility with a thin `_build_main_planner_callbacks(...)` wrapper in `engine/auto_campaign_runner.py` while keeping planner dependency seams injection-based and independently testable.
- Added direct regression coverage for the extracted planner-callback seam and revalidated the touched runner, prepare-callback, controls, follow-up policy, and queue slices locally without behavior changes.

## 0.8.81 / 2026-04-12

- Completed Wave 30 as a bounded Phase B3 runner-thinning tranche, extracting main prepare-callback assembly into `engine/runtime_runner_prepare_callbacks.py`.
- Preserved runner compatibility with thin wrappers in `engine/auto_campaign_runner.py` while keeping injected queue/precheck/orchestrator seams patchable for existing facade coverage.
- Added direct regression coverage for the extracted prepare-callback seam and revalidated the touched runner, controls, follow-up policy, and queue slices locally without behavior changes.

## 0.8.80 / 2026-04-11

- Completed Wave 29 as a bounded Phase B3 runner-thinning tranche, extracting main runtime-controls normalization into `engine/runtime_runner_controls.py`.
- Preserved runner compatibility with a thin `_build_main_runtime_controls(...)` wrapper while moving `MainRuntimeControls` and `build_main_runtime_controls(...)` into the dedicated controls module.
- Added direct regression coverage for the extracted controls seam and revalidated the touched runner, follow-up policy, and queue slices locally without behavior changes.

## 0.8.79 / 2026-04-11

- Completed Wave 28 as a bounded audit of the Wave 26 follow-up policy extraction seam, confirming the extracted module remained behaviorally stable.
- Added direct regression coverage for `engine/runtime_followup_policy.py` so the extracted seam is validated independently of the runner wrapper.
- Revalidated the touched follow-up policy, runner facade, and queue slice locally without changing runtime behavior or public contracts.

## 0.8.78 / 2026-04-11

- Completed Wave 26 as a bounded micro-B3 structural tranche, extracting adaptive follow-up policy logic from `engine/auto_campaign_runner.py` into a dedicated `engine/runtime_followup_policy.py` module.
- Preserved the runner-facing `next_followup_family(...)` contract via a thin compatibility wrapper while keeping quality-aware steering and adaptive explainability behavior unchanged.
- Revalidated the touched follow-up/queue slice locally after correcting small extraction-compatibility issues, without changing runtime authority or public contracts.

## 0.8.77 / 2026-04-11

- Completed Wave 25 as a bounded audit of the archetype plus adaptive follow-up mini-arc, confirming canonical seams remained singular and operator truth stayed coherent.
- Removed a small duplication in `engine/auto_campaign_runner.py` by extracting a local helper for attaching adaptive follow-up explainability across bounded adaptive branches.
- Revalidated the touched follow-up/queue slice locally and closed the audit without changing runtime authority or public contracts.

## 0.8.76 / 2026-04-11

- Completed Wave 24 as a bounded operator-truth tranche for adaptive follow-up decisions, introducing a compact canonical explainability helper that unifies quality, synthesis, and archetype truth.
- Updated `engine/auto_campaign_runner.py` so bounded archetype-driven follow-up branches now attach the richer canonical adaptive follow-up explainability shape instead of only local archetype-only metadata.
- Added focused regression coverage for unified adaptive follow-up explainability and revalidated the touched follow-up/queue slice locally.

## 0.8.75 / 2026-04-11

- Completed Wave 23 as a bounded audit of the Phase A3 archetype mini-arc, confirming one canonical inference seam, coherent bounded consumers, and adequate explainability truth.
- Removed a small queue-scoring redundancy in `engine/runtime_queue_strategy.py` by reusing one canonical archetype inference result for both multiplier calculation and explainability fields.
- Revalidated the touched archetype queue/follow-up slice locally and closed the mini-arc audit without adding new behavioral authority.

## 0.8.74 / 2026-04-11

- Completed Wave 22 as a bounded Phase A3 explainability tranche, making canonical archetype influence more operator-visible without changing runtime authority.
- Added compact follow-up archetype explainability in `engine/runtime_archetype_inference.py` and attached bounded `followup_explainability` metadata in archetype-driven follow-up selection branches.
- Enriched queue-scored tasks with `archetype_primary` and `archetype_confidence` alongside existing archetype hints/multipliers, and revalidated the touched archetype queue/follow-up slice locally.

## 0.8.73 / 2026-04-11

- Completed Wave 21 as a bounded Phase A3 continuation, extending canonical runtime archetype inference into follow-up family selection without changing admission or scheduler authority.
- Updated `engine/auto_campaign_runner.py` so `next_followup_family(...)` now reads canonical archetype flags and applies narrow soft steering for auth-heavy/admin-like and static-edge targets.
- Added focused regression coverage for archetype-aware follow-up selection and revalidated the touched archetype queue/follow-up slice locally.

## 0.8.72 / 2026-04-11

- Completed Wave 20 as a bounded Phase A3 support tranche, introducing a canonical runtime archetype-inference helper instead of leaving archetype consumption embedded as queue-local logic.
- Added `engine/runtime_archetype_inference.py` with compact `infer_runtime_archetypes(...)`, deriving shared archetype fields such as primary archetype, top archetypes, confidence, and stable boolean flags from existing learning hints.
- Updated `engine/runtime_queue_strategy.py` so `_archetype_multiplier(...)` now consumes the canonical archetype inference seam while preserving existing bounded queue-scoring behavior.
- Added focused regression coverage for canonical archetype inference and queue consumption, then revalidated the touched queue/facade slice locally.

## 0.8.71 / 2026-04-11

- Completed Wave 19 as a bounded audit tranche over the Wave 14-18 synthesis mini-arc, verifying that canonical synthesis, admission, explainability, and aggregation seams remain coherent end-to-end.
- Confirmed that `recon_to_exploit_synthesis(...)` remains the canonical synthesis helper, `planner_runtime_admission_decision(...)` remains the canonical admission seam, and synthesis-skip reporting continues to derive operator truth from existing recorded examples rather than separate persistence.
- Applied a narrow cleanup in `engine/auto_campaign_precheck.py` to avoid unconditional duplicate admission-decision recomputation, keeping the extra recomputation only for the `planner_synthesis_skip` explainability enrichment path where it is actually needed.
- Revalidated the touched admission/reporting slice locally and documented the audit findings in the Wave 19 closeout report.

## 0.8.70 / 2026-04-11

- Completed Wave 18 of the post-T4 adaptive-intelligence roadmap as a bounded reporting tranche, adding compact aggregate truth for synthesis-aware admission skips without changing runtime behavior or persistent state shape.
- Extended `engine/runtime_admission_reporting.py` with a derived `synthesis_skip_summary(...)` helper that parses existing skip examples and summarizes synthesis skip action, stage, reason, and family breakdowns.
- Updated `execution_gate_summary_payload(...)` to include a compact `synthesis_skip` section so operator reporting can distinguish `pivot` versus `abandon` and `validation` versus `bounded_exploit_proof` at a glance.
- Added focused regression coverage for synthesis-skip aggregation and revalidated the touched admission/reporting slice locally.

## 0.8.69 / 2026-04-11

- Completed Wave 17 of the post-T4 adaptive-intelligence roadmap as a bounded explainability tranche, improving operator truth for synthesis-aware admission skips without changing runtime authority or widening the public execution-gate contract.
- Extended `engine/runtime_admission_policy.py` so canonical admission decisions carry compact synthesis explainability metadata, including recommended action, synthesis reason, late-stage target stage, and recon-like gate family relevance.
- Updated `engine/auto_campaign_precheck.py` and `engine/runtime_admission_reporting.py` so `planner_synthesis_skip` reporting examples and log details surface bounded synthesis context while leaving generic gate payload behavior unchanged.
- Added focused regression coverage for synthesis-aware admission reporting and precheck payload enrichment, then revalidated the touched admission/reporting slice locally.

## 0.8.68 / 2026-04-11

- Completed Wave 16 of the post-T4 adaptive-intelligence roadmap as a moderate, bounded structural-support tranche, verifying canonical admission parity and adding a minimal synthesis-aware admission hook without widening runtime authority or execution-gate payload contracts.
- Extended `engine/runtime_admission_policy.py` so `planner_runtime_admission_decision(...)` can consume optional planner feedback, derive a compact `recon_to_exploit_synthesis(...)` verdict, and lightly block only narrow recon-like late-stage admission cases through the existing canonical helper.
- Updated `engine/runtime_execution_gate.py` and `engine/auto_campaign_precheck.py` to pass optional planner feedback into the shared admission seam, preserving canonical behavior between execution gating and precheck rather than creating a second admission path.
- Added focused regression coverage for synthesis-aware admission parity in runtime execution gate and precheck slices, then revalidated the touched tests locally.

## 0.8.67 / 2026-04-11

- Completed Wave 15 of the post-T4 adaptive-intelligence roadmap as a bounded synthesis-quality evaluation tranche, extending replay and metrics so the new canonical recon-to-exploit synthesis seam can be judged by outcomes instead of assumption.
- Extended `engine/evaluation_replay.py` to project synthesis-aware fields such as recommended action, synthesis reason, alignment, positive outcome, and pivot-avoidance behavior.
- Extended `engine/evaluation_metrics.py` with bounded `synthesis_quality_metrics`, including alignment, positive-outcome, and pivot-avoidance rates.
- Added focused regression coverage for synthesis-aware replay projection and evaluation metrics, then revalidated the touched slice.

## 0.8.66 / 2026-04-11

- Completed Wave 14 of the post-T4 adaptive-intelligence roadmap as a bounded recon-to-exploit synthesis tranche, introducing a canonical helper that fuses adaptive-quality and stage/surface context into compact branch-action recommendations.
- Extended `engine/runtime_plan_control.py` with `recon_to_exploit_synthesis(...)`, producing bounded recommendations such as `confirm`, `deepen`, `pivot`, or `abandon` with compact explainability.
- Updated `engine/auto_campaign_runner.py` so follow-up family steering can consume the synthesis verdict as an additive preference, improving recon-to-exploit downshifts/progression without widening planner or runtime authority.
- Added focused regression coverage for synthesis output and bounded runtime consumption, then revalidated the touched slice.

## 0.8.65 / 2026-04-11

- Completed Wave 13 of the post-T4 adaptive-intelligence roadmap as a bounded branch-summary and registry-necessity tranche, using Wave 11-12 lifecycle and thread identity semantics to materialize a lightweight summary view instead of jumping directly to a heavy branch registry.
- Extended `engine/learning_store.py` with `summarize_branch_threads(...)`, aggregating branch-thread priors into compact per-thread summaries with productive/dead-end pressure and dominant lifecycle status.
- Extended `engine/evaluation_metrics.py` to expose bounded `branch_thread_summary` reporting so branch continuity is visible in evaluation/reporting without changing runtime scheduling authority.
- Added focused regression coverage for branch-thread summary aggregation and reporting exposure, then revalidated the touched slice.

## 0.8.64 / 2026-04-11

- Completed Wave 12 of the post-T4 adaptive-intelligence roadmap as a lightweight branch-thread identity tranche, adding deterministic `branch_thread_key` and `branch_thread_label` semantics without introducing a heavy registry or durable global branch IDs.
- Extended `engine/runtime_effective_decision.py` with canonical `branch_thread_identity(...)`, propagated thread identity into queued follow-up/precision artifacts, and surfaced `branch_thread_key` into planner preferences for downstream runtime continuity.
- Extended `engine/learning_store.py`, `engine/evaluation_replay.py`, and `engine/runtime_queue_strategy.py` so learning priors, replay/evaluation outputs, and queue explainability all share the same compact branch-thread identity semantics.
- Added focused regression coverage for thread identity derivation, replay projection, learning persistence, and queue explainability, then revalidated the touched adaptive branch slice.

## 0.8.63 / 2026-04-11

- Completed Wave 11 of the post-T4 adaptive-intelligence roadmap as a bounded branch-lifecycle tranche, adding a canonical branch lifecycle layer above existing graph-lite branch state without introducing a heavy branch engine or durable branch registry.
- Extended `engine/runtime_effective_decision.py` with `branch_lifecycle(...)`, attached lifecycle fields to branch metadata and queued follow-up/precision artifacts, and surfaced `branch_lifecycle_status` into planner preferences for downstream runtime truth.
- Extended `engine/learning_store.py`, `engine/evaluation_replay.py`, and `engine/runtime_queue_strategy.py` so branch persistence, replay/evaluation, and bounded queue history steering can consume canonical lifecycle status and reason, rather than relying only on lower-level branch-state/action/reason reconstruction.
- Added focused regression coverage for lifecycle derivation, replay projection, learning persistence backfill, and queue suppression behavior, then revalidated the touched adaptive branch slice.

## 0.8.62 / 2026-04-11

- Completed Wave 10 of the post-T4 adaptive-intelligence roadmap as a consolidation tranche, introducing a canonical adaptive-quality context instead of adding another isolated hot-path heuristic.
- Extended `engine/runtime_plan_control.py` with `adaptive_quality_context(...)`, which normalizes recent branch-quality, dead-end pressure, recon-conversion, and confirmation-efficiency signals into one shared runtime contract with derived booleans such as `dead_end_heavy`, `quality_structural`, and `quality_strong`.
- Updated `engine/runtime_runner_bootstrap.py` and `engine/auto_campaign_runner.py` to consume the canonical adaptive-quality helper for reconsult, regeneration, follow-up family steering, and follow-up admission behavior, reducing duplicated feedback unpacking while preserving bounded existing semantics.
- Added focused regression coverage for the canonical adaptive-quality helper and revalidated the touched planner-feedback, runner-bootstrap, and runner-facade seams.

## 0.8.61 / 2026-04-11

- Completed Wave 9 of the post-T4 adaptive-intelligence roadmap as a bounded quality-aware follow-up admission tranche, tuning post-run follow-up enqueue behavior with recent dead-end pressure and branch-quality signals without redesigning queue budgeting or scheduler contracts.
- Extended `engine/auto_campaign_runner.py` with `_quality_aware_followup_admission_hint(...)` and applied it in `handle_post_run_actions(...)`, so strong sterile pressure can suppress some exploit-ish follow-ups while strong recent quality can mark eligible exploit follow-ups as higher priority.
- Kept existing planner, qualification, and runtime guard logic primary by limiting the new behavior to small admission hints on top of the current effective-decision path, rather than replacing the follow-up eligibility model.
- Added targeted regression coverage for the new post-run admission tuning and revalidated the touched auto-campaign/runtime-control slice across runner facade, planner feedback, and runner bootstrap seams.

## 0.8.60 / 2026-04-11

- Completed Wave 8 of the post-T4 adaptive-intelligence roadmap as a bounded quality-aware follow-up steering tranche, consuming recent branch-quality and dead-end pressure signals in follow-up family selection without widening queue contracts or redesigning post-run scheduling.
- Extended `engine/auto_campaign_runner.py` with a compact `_quality_aware_followup_family(...)` helper and quality-aware nudges inside `next_followup_family(...)`, so high dead-end pressure can downshift fragile exploit escalation toward safer validation/discovery families while strong recent quality can preserve or support exploit-capable family choices.
- Kept planner/analysis explicit next-family hints authoritative, preserved progression-prior and stage/surface semantics, and limited the new behavior to bounded family steering rather than queue scoring or planner contract changes.
- Added targeted regression coverage for the new follow-up steering behavior and revalidated the touched auto-campaign/runtime-control slice across runner facade, planner feedback, and runner bootstrap seams.

## 0.8.59 / 2026-04-11

- Completed Wave 7 of the post-T4 adaptive-intelligence roadmap as a bounded evaluation-aware adaptation tranche, feeding compact branch-quality and dead-end pressure truth back into planner feedback and runtime adaptation heuristics without widening runtime contracts or adding new archive plumbing.
- Extended `engine/runtime_plan_control.py` so `summarize_planner_feedback(...)` now projects compact recent quality counters and rates, including branch candidate volume, branch quality rate, dead-end pressure, recon-to-exploit conversion, and signal-to-confirmation efficiency.
- Tuned `engine/runtime_runner_bootstrap.py` and regeneration heuristics so strong dead-end pressure now tempers overly eager structural reconsult/regeneration, while healthy branch-quality and recon-conversion signals can moderately support structural reconsult in a bounded, explainable way.
- Added targeted regression coverage for the new evaluation-aware planner feedback and adaptation tuning, then revalidated the touched runtime-control slice across plan control, runner bootstrap, effective decisioning, and runner facade seams.

## 0.8.58 / 2026-04-11

- Completed Wave 6 of the post-T4 adaptive-intelligence roadmap as a bounded branch-persistence tranche, making branch outcomes durable in learning and letting queue steering suppress historically sterile branch shapes without introducing a heavy branch engine.
- Extended `engine/learning_store.py` and learning-store normalization with additive `branch_priors` / `host_branch_priors`, optional branch outcome fields on `update_learning(...)`, and a compact retrieval helper `top_branch_hints(...)` for branch-state/action/reason history.
- Extended `engine/runtime_queue_strategy.py` with a bounded `branch_history_multiplier`, so host-specific dead-end branch history can lightly suppress stale proof paths or boost historically productive branch shapes while remaining explainable through surfaced branch-history metadata.
- Added targeted regression coverage for branch persistence and dead-end suppression, then revalidated the touched adaptive slice across learning-store, queue strategy, effective decisioning, runner bootstrap/facade, and evaluation metrics/replay surfaces.

## 0.8.57 / 2026-04-11

- Completed Wave 5 of the post-T4 adaptive-intelligence roadmap as a bounded intelligence-quality evaluation tranche, extending the existing replay/metrics stack instead of widening hot-path runtime behavior.
- Extended `engine/evaluation_replay.py` with compact intelligence-quality projection fields derived from already-carried runtime metadata, including branch candidate/quality state, dead-end branch detection, recon-like classification, recon-to-exploit conversion flags, and signal-to-confirmation tracking.
- Extended `engine/evaluation_metrics.py` with additive `intelligence_quality_metrics` covering branch quality rate, dead-end avoidance rate, recon-to-exploit conversion rate, and signal-to-confirmation efficiency, and bumped metrics schema output to `phase5-metrics-v2`.
- Updated `engine/evaluation_variants.py` and reporting/test coverage so offline comparison and archived evaluation summaries can measure the new intelligence-quality dimensions without requiring a broader pipeline-contract rewrite.

## 0.8.56 / 2026-04-11

- Completed Wave 4 of the post-T4 adaptive-intelligence roadmap as a bounded host-archetyping tranche, adding compact operational archetype priors without widening into a broad pipeline-contract or runtime-artifact rewrite.
- Extended `engine/learning_store.py` with additive archetype inference/storage (`infer_archetypes(...)`, `archetype_priors`, `host_archetype_priors`, `top_archetype_hints(...)`) so host/application context can be learned and queried alongside transition and progression priors.
- Added a bounded queue consumer in `engine/runtime_queue_strategy.py`, where learned archetype hints now contribute a small explainable multiplier and surfaced `archetype_hints` metadata during queue reprioritization.
- Added targeted regression coverage for archetype inference/storage and queue prioritization under archetype influence, then revalidated the touched adaptive-intelligence seams across learning-store persistence, effective decisioning, queue strategy, planner reconsult tiering, follow-up family steering, execution gating, and precheck admission behavior.

## 0.8.55 / 2026-04-11

- Completed Wave 3 of the post-T4 adaptive-intelligence roadmap as a bounded graph-lite tranche, adding explicit branch-state and recon-to-exploit synthesis semantics without widening into a heavy exploit-graph platform or runner-wide redesign.
- Extended `engine/runtime_effective_decision.py` with a compact local branch-synthesis helper that classifies next-step posture into additive branch metadata (`branch_state`, `branch_action`, `branch_reason`, `branch_evidence_score`, `branch_evidence_signals`) and propagates that metadata into queued follow-up and precision tasks.
- Added a bounded queue consumer in `engine/runtime_queue_strategy.py`, where branch-state metadata now contributes a small explainable multiplier and branch-reason trace field during queue reprioritization, allowing stronger branch candidates to outrank generic continuation when evidence supports it.
- Added targeted regression coverage for branch-state propagation and queue reprioritization behavior, then revalidated the touched adaptive-intelligence seams across learning-store persistence, effective decisioning, queue strategy, planner reconsult tiering, follow-up family steering, execution gating, and precheck admission behavior.

## 0.8.54 / 2026-04-11

- Completed Wave 2 of the post-T4 adaptive-intelligence roadmap as a bounded additive tranche focused on contextual progression memory instead of widening ownership into broad planner/runtime refactoring.
- Extended `engine/learning_store.py` and state normalization with additive contextual progression priors (`progression_priors`, `host_progression_priors`), plus bounded optional learning metadata for `next_family` and `reconsult_tier` and a compact retrieval helper `top_progression_hints(...)`.
- Integrated the primary Wave 2 runtime consumer in `engine/runtime_runner_bootstrap.py`, where `maybe_reconsult_planner(...)` now uses learned progression priors as a bounded, explainable nudge for existing planner reconsult tiers without replacing threshold-based safeguards.
- Added a small optional secondary consumer in `engine/auto_campaign_runner.py`, allowing `next_followup_family(...)` to use compact learned progression hints when available while preserving existing stage-ladder and family-mapping fallbacks.
- Revalidated the touched Wave 1 and Wave 2 seams with focused regression slices covering learning-store persistence, runtime effective decisioning, queue strategy reprioritization, planner reconsult tiering, follow-up family steering, execution gating, and precheck admission behavior.

## 0.8.53 / 2026-04-11

- Completed Wave 1 of the post-T4 adaptive-intelligence roadmap as a bounded additive tranche instead of a speculative broad refactor: repo-truth verification confirmed planner/runtime admission was already canonicalized through `engine/runtime_admission_policy.py`, so the wave focused on richer learning substrate work plus drift-catching admission verification.
- Extended `engine/learning_store.py` and normalization with additive sequence-aware transition memory (`transitions`, `host_transition_pairs`) while preserving compatibility for existing `update_learning(...)` / `summarize_learning(...)` paths and legacy summary buckets.
- Added the first two bounded runtime consumers of the new priors: follow-up guidance in `engine/runtime_effective_decision.py` now frontloads learned transition action hints with explainable planner-preference metadata, and `engine/runtime_queue_strategy.py` now applies a small bounded transition-prior multiplier plus explainability fields during queue reprioritization.
- Closed the remaining admission-seam verification work with targeted regression coverage confirming `auto_campaign_precheck.evaluate_runtime_task_admission(...)` preserves canonical reason-code behavior from the shared admission policy instead of drifting into wrapper-local semantics.
- Revalidated the touched Wave 1 seams with focused regression slices covering learning-store persistence, effective decision guidance, queue strategy reprioritization, runtime execution gate behavior, and auto-campaign precheck behavior.

## 0.8.52 / 2026-04-11

- Corrected Tier 4 scope to match repo truth instead of stale backlog assumptions: inspection confirmed the admission-policy unification and runtime-plan-service decomposition seams had already been completed earlier, so Tier 4 was retargeted at the next real unfinished bounded seam rather than duplicating prior work.
- Hardened Logdash API registration contracts by introducing explicit required-context validation for runtime, planner, and supplemental API wiring, so missing registration keys now fail immediately with a clearer contract error instead of surfacing later as ad hoc runtime regressions.
- Added focused regression coverage for missing Logdash API context keys and revalidated the touched selected-snapshot planner/runtime/supplemental API surfaces.

## 0.8.51 / 2026-04-11

- Completed the full Tier 3 tranche in three bounded waves after Tier 2 closeout: repo hygiene/release posture gained a short canonical runtime-artifact ownership reference linked from the main truth docs, `auto_campaign_runner.py` shed duplicate bootstrap-helper wrapper ownership in favor of the focused `runtime_runner_bootstrap` seam, and Logdash System Settings now reflects both draft preset matching and persisted normalized effective posture through `/api/pipeline-config/meta` so operator-visible posture better matches config truth.
- Added/updated focused regression coverage for the Tier 3 seams across the runner façade/bootstrap boundary, Logdash preset UI, pipeline-config meta posture reflection, and Logdash runtime selected-snapshot test scaffolding.

## 0.8.50 / 2026-04-11

- Completed the full Tier 2 tranche in three bounded waves after Tier 1 closeout: qualification/evidence semantics were refined with additive `qualification.disposition` and `finding_signal.evidence_class` truth, the evaluation/replay layer was expanded to expose and measure compact semantic outcome classes (`no_evidence`, `weak_evidence`, `blocked_evidence`, `stronger_evidence`) plus new governance/semantic-class metrics, and Logdash evaluation-summary projection was moved out of endpoint-local shaping into a shared service helper so the control plane stays a thinner reflection of canonical runtime/evaluation truth.
- Added targeted regression coverage for the Tier 2 seams across qualification, signal contract projection, replay, metrics, fixtures, variant comparison, Logdash evaluation projection, and Logdash smoke validation.

## 0.8.49 / 2026-04-10

- Closed a bounded Tier 1 runtime-truth seam in Logdash: selected-campaign snapshot filtering now treats `queues`, `telemetry`, `hosts`, and `economics` as campaign-scoped snapshot truth alongside `campaign`, `plan`, and `latest_run`, instead of only partially filtering mismatched snapshots.
- Routed additional snapshot-backed control-plane endpoints through the shared selected-snapshot path in `logdash/api_supplemental.py`, removing stale other-campaign snapshot leakage from `runtime-health`, `metrics`, `host-state`, `host-explain`, `family-yield`, `finding-quality`, and latest-trace fallback shaping.
- Added focused regression coverage for both helper-level and endpoint-level mismatch behavior, then revalidated the broader Logdash smoke surface so operator-visible runtime truth now stays aligned with the selected campaign when a stale snapshot file exists.
- Finished the same runtime-truth closeout seam for planner-facing Logdash APIs by routing `planner-info` and `planner/runtime-plan-view` through the shared selected-campaign snapshot filter, so stale snapshot plan/campaign metadata from another campaign no longer overrides the active runtime-plan truth.
- Closed the next Tier 1 execution-lineage auditability slice: runtime decision projection now preserves explicit flat action/reason compatibility aliases, and `/api/runtime-trace` now exposes canonical lineage join keys (`planner_contract_sha256`, `runtime_contract_sha256`, `experiment_intent_id`) plus fuller decision alias fields instead of dropping them from the operator trace surface.
- Hardened closeout validation fallout found during the full-suite pass: Logdash legacy log-row fallbacks now normalize sqlite rows safely, planner scope parsing no longer loses `Starting Domains` after out-of-scope blocks, static surfaces keep posture-oriented `tls_assessment` lineage in planner output, and the stale `reports/latest` archive target was restored so health-audit cleanliness stays green.
- Closed the final Tier 1 exploitability-tuning slice with a bounded proof-capture bias: evidence-bearing `report_artifact_capture` branches now prefer the `precision` lane over generic `followup`, which helps proof/report-ready work reach bounded artifact capture faster without weakening actor/precondition guards.

## 0.8.48 / 2026-04-07

- Closed the final planner→runtime enforcement wave on the canonical workspace: runtime admission/execution now applies bounded planner-governed enforcement for `activation_phase`, `activation_mode`, `conditional_gate`, `surface_role`, `expected_depth`, and bounded `target_cluster` semantics instead of treating them as planner-only hints.
- Added/expanded targeted regression coverage for the new planner/runtime gating seams in `engine/auto_campaign_precheck.py`, `engine/runtime_execution_gate.py`, and `engine/runtime_task_schema.py`, including compatibility normalization for semantic activation-phase strings such as `bounded_exploit_proof`.
- Finished the System Settings preset closeout by ensuring manual textarea/JSON edits flip the preset view to `custom` immediately, and kept the targeted preset/runtime validation slices green.
- Completed a bounded Logdash state-ownership cleanup: selected-campaign snapshot filtering/projection now flows through a shared helper in `logdash/services.py`, reducing split-brain risk across `campaign-info`, `runtime-state`, `queue-state`, and related control-plane endpoints.
- Stabilized the empty-shape behavior of `/api/runtime-trace` so Logdash gets a consistent response contract even when no latest trace artifact exists yet.
- Refreshed core repository truth docs (`README.md`, `ARCHITECTURE.md`, `STATE_FILES.md`, `engine/RUNTIME_MANIFEST.md`) so the documented runtime path, state ownership, path contracts, and control-plane boundaries match the real current Ravenclaw system.
- Performed a follow-on documentation/backlog remediation pass: historical implementation plans were marked as such where appropriate, Logdash/reference docs were updated to reflect the current helper/service/state layering, and contract references were refreshed to include planner-governed execution-shaping fields.

## 0.8.47 / 2026-04-02

- Refactored planner scope ingestion for real bug-bounty scopes: deterministic parsing now prefers authoritative in-scope asset rows over broad prose scraping, ignores incidental email-domain leakage, and preserves first-class `structured_scope.authoritative_assets` with exact URL/domain scope metadata instead of flattening everything immediately into broad host scope.
- Upgraded planner blueprint generation so canonical `experiment_intents` are now emitted from authoritative scope assets, preserve exact URL targets, and narrow broad host-only task families for exact-URL-only assets, improving scope fidelity for programs that mix domain scope with exact path-limited URLs.
- Hardened runtime-plan generation/validation: `runtime_plan_service.py` now rejects canonical experiment-intent broadening against exact-URL-only authoritative scope instead of silently falling back to legacy host synthesis, and Logdash validation now fails plans that include non-authoritative hosts or broaden exact scoped targets.
- Fixed the Campaign Setup operator surface in Logdash by removing the dead `Planner mode` control and replacing it with a real persisted `llm_interpret` toggle used by both `Run planner` and `Prepare all-in-one`, so UI behavior now matches the actual planner path.
- Added targeted regression coverage for parser scope fidelity, authoritative asset preservation, runtime-plan exact-scope enforcement, planner CLI/runtime-plan seams, and Campaign Setup UI/API wiring; the bounded validation slices for parser/runtime-plan/UI/CLI all passed green.
- Fixed `Owner actions -> Delete selected campaign` so it now performs a real destructive delete of the selected campaign registry entry, clears campaign-local runtime-plan artifacts and selection state, resets campaign-facing counters to defaults, and preserves global System Settings / pipeline config.
- Fixed bad `Scope targets / Prepared attacks` counts in Pipeline Monitoring and Campaign Setup by making campaign-facing count reads prefer current selected-campaign runtime-plan truth over stale unrelated snapshot sections, with added regression coverage for delete semantics and count precedence.
- Fixed runtime-plan meta `target_count` / `input_total` so they now reflect unique scoped targets instead of collapsing exact URL assets into unique hosts, which keeps UI/runtime truth aligned with exact-URL campaign scope.
- Improved exact-URL planner shaping in `blueprint.py` so URL assets use host/path semantics and allowed vectors (`xss`, `csrf`, `ssrf`) to produce better bounded task-family mixes instead of frequently flattening into generic `content_discovery` only.
- Fixed Campaign Setup `Prepare all-in-one` selection propagation: after `Run planner` creates/selects a new campaign, quick-prepare now carries that fresh campaign key through campaign list hydration, approval, and runtime-plan generation, which resolves the bug that made `LLM interpret` appear ineffective while the UI was actually continuing on the old deterministic campaign.
- Fixed another operator-facing truth gap after quick-prepare: `Pipeline Monitoring` / runtime-facing APIs now ignore stale `runtime_snapshot` campaign/plan/queue sections when they belong to a different campaign than the current selection, so a newly generated hybrid plan no longer looks missing just because an older snapshot file is still present.
- Improved hybrid planner quality shaping: identity hosts like `id.*` now classify as auth surfaces, generic URL-backed hosts are uplifted from flat `host` typing for better family seeding, exact URL shaping no longer over-broadcasts `auth_flow/client_input` on generic root URLs, and LLM prose attack vectors are normalized into canonical planner tags before downstream planner use.
- Added a further near-ideal planner-quality wave: target clustering is now more semantic (`identity_auth`, `commerce_store`, `infra_edge`, `consumer_web` where appropriate instead of overloading `general`), cluster pruning preserves stronger family bias for similar auth surfaces, and exact URL family selection now uses compact score-driven confidence/suppression logic with downstream-visible rationale rather than broad additive heuristics alone.
- Final planner polish landed: domain assets now use the same score/suppression discipline as URL assets, strong `identity_auth` domains suppress residual `recon`/`tls_assessment`, suppression rationale now includes compact score/threshold context, and score-driven family selection preserves proven cluster biases (`money`, `ai_chat`, `integration_api`) instead of over-trimming them under the new model.
- Hardened live runtime contract hygiene for BRAIN action specs: the BRAIN prompt now explicitly forbids shell-like args/tool-chain fragments, `contracts.py` now sanitizes obvious shell operators from action-spec args before validation, sanitization is logged, and the final contract validator still blocks any payload that remains non-hermetic.
- Added policy-aware auth/execution shaping for live runtime: active campaigns now resolve credentials from campaign-scoped settings during runtime, basic-auth-like flags are stripped when a campaign forbids basic auth, and credentialed crawler/enumeration steps are locally capped to safer aggression instead of repeatedly wasting runs on predictable auth/policy owner-gates.
- Repaired drift in that contract-hardening wave: restored the missing `contracts.py` helper surface for auth-mode sanitization and aggression remap, wired auth-mode sanitization back into the pre-validation `run_pipeline.py` path, added stronger regression coverage for tool-chain sanitization/basic-auth stripping/no-op preservation, and revalidated the affected runtime/control seams with targeted plus broader smoke slices.
- Centralized runtime aggression shaping into a canonical normalization path in `engine/run_pipeline.py`: global clamp, out-of-scope cap, and credentialed enumeration remap now flow through one normalization chain instead of mixed inline mutation plus later copy-based shaping, and a new fully mocked `execute_flow(...)` regression harness proves auth-mode sanitization and aggression remap survive the live control path.
- Repaired a live planner/runtime contract drift in the auto-campaign dispatch seam: `auto_campaign_runner.py` now fully forwards expanded planner/runtime payload fields (`planner_rationale`, `planning_ladder`, target-surface/progression rationale, semantic lineage), `run_pipeline.py` now accepts the expanded CLI contract, `pipeline_context.py` now preserves those fields in merged intent context, fresh smoke runs no longer crash on `planner_rationale_json`, and the operator-requested runtime/logdash transient artifacts were cleared for a clean next run.

## 0.8.46 / 2026-04-01

- Completed a bounded runtime decision-truth unification wave: canonical selected-action semantics now drive compatibility flag derivation in `engine/runtime_decision_contracts.py`, and hot-path consumers (`runtime_effective_decision.py`, `auto_campaign_downstream.py`, `runtime_decision_projection.py`) now read canonical selected-action truth first instead of treating `intent_flags` / `action_flags` as equal-rank runtime truth.
- Preserved backward-compatible alias surfaces while making them explicitly derived via `intent_flags_source` / `action_flags_source`, reducing split-truth risk without breaking existing downstream/reporting consumers.
- Added/updated focused regression coverage for the new seam, including `engine/tests/test_auto_campaign_downstream.py` and projection compatibility assertions in `engine/tests/test_runtime_decision_projection.py`.
- Restored a trustworthy green engine-test baseline during closeout by hardening curl execution normalization with `curl -q` in `engine/executor.py`, widening `ai_chat` planner family shaping to keep bounded `content_discovery` follow-on intent generation, and rewriting the approved curl-chain test to use deterministic local `file://` inputs rather than external HTTPS trust-store state.
- Validation for this closeout passed at three layers: targeted decision-truth seam tests, targeted executor/planner fix tests, and the broad `pytest -q engine/tests` baseline.

## 0.8.45 / 2026-03-29

- Improved Logdash settings ergonomics in the canonical workspace: `system_settings`, `campaign_setup`, and `owner_actions` now hydrate behind an explicit loading gate instead of briefly rendering misleading default control states before persisted config arrives.
- Added first-class System Settings runtime presets in Logdash (`exploratory-efficient`, `exploratory-max`, `confirmation-heavy`) with immediate UI reflection into the visible controls, automatic fallback to `custom` after manual edits, and targeted regression coverage for the preset dropdown/hooks.

## 0.8.44 / 2026-03-28

- Completed the next major roadmap wave on the canonical workspace: Phase 5 added evaluation/replay/benchmarking primitives (`evaluation_bundle`, `evaluation_replay`, `evaluation_metrics`, `evaluation_variants`, `evaluation_fixtures`) plus archive-side evaluation exports; Phase 6 centralized runtime path contracts in `engine/paths.py`, moved canonical generated artifacts under `reports/state/` and `reports/cache/`, preserved compatibility mirrors for legacy engine-local paths, and added repo/public-readiness scaffolding (`pyproject.toml`, `.editorconfig`, CI workflow, `SECURITY.md`, `CONTRIBUTING.md`); Phase 7 extended Logdash/runtime-truth surfaces with compact evaluation/runtime APIs and UI visibility into governance/evidence/exploit-ladder truth.
- Landed the post-audit hunting-power hardening wave (A–D): narrowed approved-spec executor trust boundaries to approved-safe tools, rebuilt the BRAIN prompt around semantic-first compact sections with a raised prompt budget, unfroze runtime adaptation under bounded aggressive mode, and retuned exploit conversion/follow-up behavior toward stronger confirm-job and boundary-context promotion without relaxing policy controls.
- Closed the follow-on mini-roadmap MR1–MR4 by normalizing runner config loading, making follow-up pacing profile-native instead of hard-coded, adding an early authz/workflow weak-signal boundary lane, and pushing normalized execution further toward semantic planning with deterministic realization by demoting explicit planner tool picks into preference hints when the compiler can resolve the final tool safely.
- Added the offensive-runtime follow-on artifact layer across W1–W5: bounded sibling-hypothesis fanout, vector-family motif expansion, persisted `branch-campaignlets`, persisted `exploit-motif-memory` fed back into BRAIN as `ExploitMotifs`, and canonical `proof-bundles` for proof-adjacent/report-adjacent branches. Reporting now writes these artifacts to archive outputs and runtime-state surfaces, and the late integration regressions around motif loading/report finalization were repaired before checkpointing.
- Performed a final polish/refactor pass before checkpointing by extracting the W3/W4/W5 artifact builders and runtime-state persistence into `engine/offensive_reporting_artifacts.py`, keeping `auto_campaign_reporting.py` focused on summary assembly while preserving green reporting/motif/prompt-budget regressions and full-suite validation.
- Follow-up repo hygiene after checkpointing: expanded `.gitignore` to cover the newly canonical `reports/state/*.json`, `reports/cache/*.json`, and local tmp proof/probe artifacts so runtime state no longer shows up as accidental untracked repo noise.
- Closed W5 formally after the main wave by adding dedicated proof-bundle regression coverage, tightening proof-bundle lineage/planner-stage derivation in `engine/offensive_reporting_artifacts.py`, and updating the W5 checklist/plan/audit plus the offensive-runtime mini-roadmap status to `completed`.
- Completed the initial post-W5 selective polish wave: reconciled the historical post-wave runtime audit against MR1-MR4/W5 closeout reality, completed a tiny Phase-4 compatibility cleanup in reporting by collapsing duplicate summary-vector lineage shaping into a single-pass helper, made host-health execution-gate cooldowns configurable through normalized runtime flags instead of a hard-coded hot-path value, and slightly widened bounded qualification sensitivity for workflow/state-transition boundary-context cases backed by actor/session prerequisites.
- Added a follow-on runtime polish slice after that closeout by removing the fixed deep/followup host-family budget cap from the execution-gate hot path and replacing it with hidden normalized runtime flag `deep_budget_cap_per_host_family`, including manifest/docs/verification/test coverage.
- Added another bounded runtime polish slice by removing the hard-coded precheck dedup-burst threshold/cooldown (`>=10`, `+300s`) and replacing them with hidden normalized runtime flags `precheck_burst_cooldown_threshold` and `precheck_burst_cooldown_sec`, again with manifest/docs/verification/test coverage.
- Added a further runtime polish slice by removing the hard-coded host-fail-streak precheck sleep/backoff constants and replacing them with hidden normalized runtime flags `host_fail_streak_backoff_step_sec` and `host_fail_streak_backoff_cap_sec`, with matching manifest/docs/verification/test coverage.
- Added the final worthwhile runtime polish slice in this chain by deduplicating transport cooldown handling between postprocess and health-policy code and replacing the remaining transport cooldown constants with hidden normalized runtime flags (`transport_observation_cooldown_sec`, `http_403_streak_threshold`, `http_403_cooldown_sec`, `code000_session_cooldown_sec`), again with manifest/docs/verification/test coverage.
- Upgraded planner quality and planner→runtime integration for real program scopes: fixed planner CLI scope generation, preserved wildcard asset ingestion, enriched target taxonomy and surface semantics, added priority/depth/surface-role/cluster metadata, added phase-aware/conditional family activation hints, propagated those planner execution fields into runtime plan entries and normalized runtime-task contracts, and taught runtime queue scoring to respect the new planner execution semantics instead of treating them as planner-only decoration.
- Continued planner-quality tuning in several bounded waves focused on first-campaign preparation quality: wildcard containment, support-family demotion, cluster-first primary/secondary host pruning, apex-host narrowing, sharper integration/API prioritization, and stricter `redirect_trust` discipline. The resulting planner output now behaves far more like a campaign planner than a broad smart-scanner wrapper while remaining aligned with runtime-executable semantics.
- Documentation, reference plans, and audit artifacts were refreshed to match the new runtime/evaluation/offensive-memory surfaces, and the repository validation baseline returned to green after the late fixes with the full `pytest -q` suite passing.

## 0.8.43 / 2026-03-27

- Recovered the interrupted Phase-1 runtime semantics WIP and drove it to green: repaired `runtime_decision_engine.py`, `runtime_effective_decision.py`, `runtime_queue_strategy.py`, and related contracts, restored backward-compatible queue reprioritization, and revalidated the affected runtime/logdash slices.
- Hardened planner determinism/testability by disabling planner LLM interpretation by default under `pytest` unless explicitly overridden, which made the full planner regression suite stable/CI-safe without changing the intended production path.
- Formalized the canonical runtime-task v2 contract and planner/runtime ownership model via new reference docs, then landed the first canonical planner output contract slice with `engine/planer/planner_intent_contract.py`, validated mirrored experiment-intent semantics, and introduced ladder-shaped planner state through `planning_ladder`.
- Extended ladder/rationale semantics end-to-end: runtime plan generation, queued followups/precision payloads, runtime decisioning, queue scoring, next-family selection, host-state learning, planner feedback, learning-store aggregation, regeneration/reconsult triggers, executor-facing runtime payloads, and sensitive-host gating now prefer ladder+rationale signals over family-only heuristics where richer context exists.
- Closed Phase 3 and Phase 4 semantics/lineage work: added canonical `engine/semantic_lineage.py`, immutable planner/runtime/lineage boundary hashes, compact `semantic_lineage_summary`, archive-side `semantic-lineage-index.json`, explicit lineage audit status/gate-readiness, and wider operator/reporting visibility across runtime state, reports, and runtime-health.
- Reduced compatibility/shim risk by centralizing lineage fallback logic in `ensure_semantic_lineage(...)` / `ensure_semantic_lineage_summary(...)`, replacing the wildcard `engine/planner_intent_contract.py` bridge with explicit re-exports, and standardizing operator surfaces on compact lineage summaries rather than raw lineage parsing where possible.
- Added/updated staged implementation plans and handoff docs for the completed waves (`phase1 runtime semantics repair`, `phase2 planner output contract`, `phase3 semantic closeout`, `phase4 lineage closeout`) so the next session can safely start from the optional hardening/cleanup stage instead of resuming broken WIP.
- Validation remained green through repeated staged sweeps; end-of-day broad regression baseline held at **186 passed** across planner, runtime, learning, control, reporting, executor, and Logdash slices.

## 0.8.42 / 2026-03-27

- Completed the P0→P2 system-settings rationalization wave across runtime, Logdash, API, and docs with staged mini-audits after each major step to preserve effectiveness while reducing operator confusion.
- Reworked runtime flag normalization around profile-driven operator controls instead of raw toggle sprawl: introduced `plan_adaptation_mode`, `planner_reconsult_mode`, `workflow_escalation_profile`, `confirm_jobs_profile`, `family_decay_mode`, `qualification_threshold`, and canonical `out_of_scope_aggression_cap`, while keeping expert/raw compatibility knobs behind the normalized config surface.
- Removed the dead `enable_contextual_reeval` operator control, retained bounded dual-action/runtime escalation internals as hidden compatibility flags, and unified out-of-scope aggression handling so runtime/policy now share one canonical ceiling while legacy aliases remain derived for compatibility.
- Normalized campaign settings more aggressively in runtime state schemas and fixed campaign-scoped target-load wiring end-to-end: `target_load_limit` is now carried through campaign settings, bootstrap/session construction, runtime runner logging, and curated loop execution instead of behaving like a misleading UI-only knob.
- Simplified Logdash operator surface: System Settings now centers on compact runtime profiles, collapses expert overrides by default, removes duplicated campaign-scoped credentials/budget controls, and Campaign Setup now owns campaign runtime limits (`max_runs`, `target_load_limit`, `time_budget_min`, `retry_policy`) alongside auth/request-decoration settings.
- Added `/api/pipeline-config/schema`, refreshed pipeline-flag docs, updated feature-flag verification to understand the rationalized surface (system core vs expert vs campaign-scoped vs hidden compatibility), and normalized `engine/pipeline_config.json` to the new canonical shape.
- Validation stayed green through staged audits: targeted runtime/profile/campaign-setting/session-flow slices passed, Logdash template syntax checks passed, live pages and save roundtrips for both `/api/pipeline-config` and `/api/campaign/settings` succeeded after restart, `engine/verify_feature_flags.py` is green again, and the live dashboard now serves the new `/api/pipeline-config/schema` route.
- Finished the follow-up UI/API polish pass before checkpointing: removed leftover campaign-scoped JS cruft from System Settings, added live autosave state badges to both System Settings and Campaign Setup, cleaned up duplicate/ambiguous DOM ownership in the advanced panels, improved Campaign Setup control metadata (`data-setting`) and planner button naming consistency, and expanded `/api/pipeline-config/meta` + `/api/pipeline-config/schema` so the frontend now has explicit schema/version/route/count metadata for safer future UI automation and refactors.

## 0.8.41 / 2026-03-26

- Completed a new runtime effectiveness wave focused on making Ravenclaw more opportunistic and predatory on promising in-scope hosts without relaxing scope discipline, owner approval, or execution gating.
- Upgraded runtime decision behavior so evidence-bearing weak/promotable signals can now continue through a bounded `evidence_bearing_followup_bridge` even when success is not strictly `partial`, and high-leverage candidate families (`authz`, `idor`, `logic`, `workflow`, `state_transition`, `input_tamper`) can enter earlier precision handling instead of dying in generic follow-up/no-op paths.
- Extended host/queue intelligence with an explicit exploitation layer: host state now tracks `exploitation_score` and `exploit_focus_family`, host `state_band` can enter `exploitation`, queue scoring is more host-centric on hot in-scope hosts, and planner feedback/regeneration reacts faster when exploitation-worthy hosts emerge.
- Tuned runtime utility/economics so action valuation is now family-aware and exploitation-aware, giving better weight to differential/state-transition/confirmatory work where those probes are most likely to increase finding yield.
- Switched queued follow-up/precision guidance from generic continuation to evidence-gap-first guidance, so persisted queue tasks now carry richer `recommended_action_types`, `followup_evidence_gap`, and planner preferences aimed at the most important missing proof rather than just “another step”.
- Diagnosed and fixed the Logdash Runtime Event Log rendering/API failure: `/api/logs` no longer crashes on `sqlite3.Row`, corrupted template tail duplication was removed, smoke coverage now includes `/api/logs`, and JS/CSS fallback/error states now show explicit panel errors instead of misleading empty states.
- Diagnosed and fixed a live queue-persistence edge case in the runtime runner: queued follow-up/precision work is no longer lost when it is preemptively dequeued from curated/main loop selection but fails to reach a real prepare/execute step. Queue tasks are now requeued to the front of their original lane, and targeted live validation confirmed persisted follow-up truth remains present in the final queue snapshot.
- Completed the first five stages of the cross-host mismatch / request-shape hygiene wave: execution contracts now carry canonical request-shape provenance (`arg_hosts_detected`, `execution_plan_hosts_detected`, `mismatched_hosts_detected`, `target_host_match_status`, `request_shape_hygiene_*`), `run_pipeline.py` now performs deterministic pre-auditor hygiene classification/logging, runtime truth/telemetry preserve contamination so mixed-host/policy-gated/owner-gated runs do not pollute future learning/economics, regression fixtures now cover execution-plan-only/non-host/same-host-variant edge cases, and planner/runtime prompt assembly now sanitizes host-bound hints/context/inherited runtime-task text to reduce mixed-host drift upstream.
- Completed the next roadmap topic after the hygiene wave: config/operator-surface alignment for the new effectiveness toggles. The governed config surface now explicitly exposes `auditor_prompt_token_budget`, `qualification_shadow_workflow_bridge`, `candidate_partial_followup_bridge`, `weak_signal_positive_bridge`, `evidence_bearing_followup_bridge`, `early_precision_for_high_leverage_families`, and `high_leverage_precision_families` across `feature_flags.py`, `feature_flags_manifest.json`, `pipeline_config.json`, System Settings, and `PIPELINE_FLAGS.md`, and `verify_feature_flags.py` is green again.
- Completed the next three effectiveness topics after operator-surface alignment: evidence-gap generation is now lane-driven and family-expanded (auth boundary, inventory growth, input validation, exposure/fingerprint), family decay now respects recent yield trend and ignores contamination instead of punishing density blindly, and queue/economics steering now uses bounded empirical family/capability priors with explainable exploration bonuses rather than opaque black-box bandits.
- Added a minimal safe dual-action runtime portfolio: primary action remains canonical, but a single bounded secondary action can now be attached in two allowlisted patterns (`confirm -> followup`, `followup -> precision`) when confidence/guards/workflow state justify it. Secondary action is explicit in decision/effective artifacts (`selected_secondary_action`, `secondary_selection_reason`, `effective_secondary_action`) and only materializes if the primary action applies and the secondary survives the same queue/family gates.
- Validation for this wave stayed green through staged mini-audits and fresh live validation: targeted runtime/logdash/queue suites passed, the broader runtime behavior suite finished at `118 passed`, the targeted queue-persistence regression slice passed at `72 passed` before a fresh live run confirmed `followup_count=1` persistence after `requeue_followup` + `curated_preempted_by_queue` events, the Stage 1/2 cross-host hygiene slices passed at `16 passed` and `18 passed`, the Stage 3 contamination propagation slices passed at `9 passed` and `88 passed`, the Stage 4/5 hygiene follow-up slices passed at `23 passed`, `41 passed`, `42 passed`, and `74 passed`, the stronger evidence-gap generation slices passed at `16 passed` and `92 passed`, the yield-trend-aware family-decay slices passed at `9 passed` and `19 passed`, the empirical steering slices passed at `10 passed` and `73 passed`, and the safe dual-action decision/effective and broader behavior slices both passed, while `verify_feature_flags.py` remained green with zero config/manifest/UI/doc drift.

## 0.8.40 / 2026-03-25

- Completed the live-runtime unblock/fix wave on the canonical workspace: fixed selected-campaign binding in the runner, restored `run_pipeline.py` compatibility with `--success-semantics-json`, normalized invalid capability / experiment-shape drift from planner+brain into valid runtime contract values, fixed tool-aware credentials parsing, improved auditor prompt construction around a canonical `PreparedExecutionSpec`, and corrected engine-status normalization so successful runs no longer degrade to `unknown`.
- Added/expanded targeted regression coverage for the runtime unblock wave across runner facade, execution contracts, auditor prompt/provenance, policy core, action compiler, run-pipeline contract enrichment, and status normalization.
- Completed the runtime behavior tuning wave through Stage F of the promotion plan: introduced a bounded shadow-mode workflow bridge so qualification remains canonical truth while guard-passing heuristic signals can now promote workflow/adaptation in `qualification_mode=shadow` without being falsely upgraded to `probable`/`confirmed`; added a bounded candidate-partial follow-up bridge so approved partial-success candidate signals can escalate into a traceable follow-up lane instead of dying at `no_action_selected`; improved default next-family progression so baseline families step into more useful low-noise bug-finding lanes (`recon -> historical_url_mining -> content_discovery -> input_tamper`, `tls_assessment -> content_discovery`) instead of defaulting back into sterile loops; made weak actionable signals downstream-usable through `signal_positive` without inflating them into `high_signal`; raised `max_followups_per_target` from `1` to `2` while preserving cooldown-based boundedness; and tuned adaptation/reconsult handling so weak actionable candidate signals can now become planner-reconsult-worthy with only light regeneration pressure.
- Added targeted Stage A–F coverage proving the new promotion bridges remain bounded, preserve canonical qualification truth, still refuse follow-up when the bridge toggle is disabled or the auditor blocks execution, keep next-family transitions explainable and low-noise, treat weak actionable signals as usable without promoting them to high-signal findings, preserve cooldown-based anti-spam behavior after the follow-up cap increase, and allow bounded adaptation signals without inflating global aggression.
- Executed the behavior-tuning wave as staged implementation checkpoints rather than one blind sweep: each stage (A through F) was followed by a focused behavior audit/regression checkpoint before the next stage was allowed to proceed, and the wave was split across commit checkpoints `f3d477d`, `e70ebbc`, `2397c13`, `a5aa1b4`, `27b164d`, and `7d19297` to keep rollback boundaries explicit.

## 0.8.39 / 2026-03-22

- Completed a large cleanup/refactor wave focused on `engine/auto_campaign_runner.py`, keeping behavior stable while aggressively reducing orchestration sprawl and contract drift in the live canonical workspace.
- Converted the major runner/session/pipeline payload builders from loose dict bundles to typed dataclasses, including runtime/session setup, runtime controls, bootstrap/state aliases, execute/complete/finalize inputs, runtime session bundle inputs, post-run action inputs, persist inputs, runtime task inputs, and run-pipeline request payloads.
- Reduced `auto_campaign_runner.py` technical debt materially: dead runtime toggle outputs were removed, multiple dead constants/imports were removed, `legacy/` was retired from the active workspace, and the stale duplicate `_build_queue_coordinator(...)` bug was discovered and fixed during the refactor.
- Tightened exception handling across the runner: immediate `except Exception: pass` sites were eliminated, several broad fallback handlers were narrowed to concrete exception classes, and broad `except Exception` count was reduced down to boundary-wrapper cases only.
- Cut down several high-noise hotspots without changing external behavior by extracting focused helpers around JSON signal inspection, result summarization, runtime callback wiring, skip-summary flushing, execute/completion stages, setup/build phases, and main-session/runtime persistence helpers.
- Simplified construction flow around `MainSessionSetup` by splitting base fields and alias-derived fields into explicit helper stages while preserving the final setup contract.
- Updated `implementation-plans/2026-03-22-runtime-audit-and-plan-refresh.md` to reflect the real state of the completed P5 work and added a closeout summary/recommendation for any follow-up session.
- Added/updated focused façade tests throughout `engine/tests/test_auto_campaign_runner_facade.py` to pin the new helper seams and typed builders as the refactor progressed.
- Final targeted regression at end of day: `97 passed` for the runner/runtime/logdash validation suite.

## 0.8.38 / 2026-03-19
- Completed the end-to-end capability architecture wave on the canonical `~/.openclaw/workspace` runtime, turning the earlier runtime-local capability work into a planner-to-operator control-plane architecture that now stays capability-aware across planning, execution, learning, and visibility layers.
- Fixed planner/runtime binding and schema drift first: planner hints are now campaign-bound instead of latest-mtime bound, target typing was normalized around canonical `target_type` with legacy compatibility, and planner-to-runtime contract tests were expanded.
- Upgraded planner outputs beyond family seeds/hints by adding explicit `planner_directives` (`constraints` / `preferences` / `unknowns`) and canonical `experiment_intents`, then taught runtime plan generation to consume those intents with a compatibility fallback for older blueprints.
- Propagated intent-level semantics into runtime execution: `runtime_task_execution.py`, `auto_campaign_runner.py`, and `run_pipeline.py` now thread experiment-intent IDs, capability candidates, recommended action types, planner constraints/preferences, and related context into BRAIN prompting, fallback behavior, preferred tool resolution, and raw execution lineage.
- Moved typed success/evidence semantics upstream and across the stack: explicit success semantics now cross the runtime subprocess boundary, `runtime_signal_eval.py` uses success/evidence contract hints instead of mostly family heuristics, and downstream analysis/postprocess/signal-contract layers preserve typed success-model metadata rather than flattening it away.
- Made learning/adaptation materially capability-primary: `learning_store.py` now records capability pairings, queue reprioritization uses capability-yield scoring and writes `capability_lane`, queued follow-up/confirm/precision work preserves capability and success metadata, and adaptation signaling can now trigger on stalled capability lanes instead of only host/periodic cues.
- Finished the operator-facing alignment: runtime snapshots now carry capability / capability-lane / experiment-intent / adaptation metadata, Logdash supplemental APIs expose capability-aware latest-run and yield telemetry including new `/api/capability-yield`, and dashboard/findings pages now render richer capability-aware queue state and finding explainability.
- Validation remained green through each staged slice and the final cleanup/polish pass, with the closing targeted UI/snapshot suite at `18 passed` and the broader end-to-end regression at `97 passed`.

## 0.8.37 / 2026-03-18
- Completed the full 2026-03-18 Ravenclaw pipeline coherence wave on the canonical workspace across P1/P2/P3/P4/P5/P6, keeping the work scoped to the live `~/.openclaw/workspace` runtime instead of the old debug tree.
- Closed approval/execution coherence gaps by hardening prepared/approved execution-spec flow, aligning request-decoration/runtime ownership semantics, and removing non-explicit post-auditor softening while preserving explicit `owner_override` as the only intentional bypass path.
- Finished tool-policy coherence (P3): runtime hot paths now use live tool-policy accessors/registry semantics instead of stale duplicated sources, and Logdash/operator-facing tool-policy semantics were brought back into alignment with engine behavior.
- Finished planner identity / provenance hardening (P4): planner reuse is keyed by stronger identity semantics (`operator_flags_hash`, `planner_semantics_hash`, `planner_identity_hash`), blueprint provenance now distinguishes deterministic vs hybrid planning honestly, registry reuse prefers planner identity with legacy source-hash fallback, and planner docs/state docs were updated accordingly.
- Finished success/signal/learning contract hardening (P5): introduced a canonical five-channel `signal_contract` (`execution_anomaly`, `finding_signal`, `success_outcome`, `workflow_promotion`, `adaptation_feedback`), added typed success evaluation for key task families, rewired routing/reconsult/learning consumers to explicit subchannels, and updated System Settings / manifests / reporting so operator-visible semantics match the new contract instead of relying on overloaded legacy `promising` / `high_signal` booleans.
- Finished semantic-loss enforcement (P6): added canonical `semantic_loss_policy` classification and deterministic policy responses, propagated that policy through compiler + prepared/approved execution specs + analysis/decision-quality, hard-blocked `required_replan|block` cases in runtime, and made degraded-semantic auditor rereview explicit via `semantic_loss_rereview_*` state plus operator-visible reporting/snapshot/API surfaces.
- Expanded targeted and broader regression coverage across planner identity, signal/routing contracts, runtime decision/effective queueing, semantic-loss enforcement, reporting, runtime snapshot state, and feature-flag consistency; the final targeted semantic-loss suite and broader runtime/reporting regression both finished green.

## 0.8.36 / 2026-03-15
- Performed a deep post-refactor cleanup of the canonical workspace after tracing live runtime/state dependencies from code and state-file documentation, then archived non-runtime clutter into `legacy/2026-03-15-deep-runtime-cleanup/` instead of deleting it.
- Preserved only active pipeline/runtime inputs and state in-place (current engine context/config files, scope, current `reports/*.state.json`, campaign registry, current live summaries, learning store, Logdash DB, and the runtime roots `tmp/engine-handoffs/` / `workspace-brain/outputs/`), while moving stale archives, reset snapshots, generated tmp inventories, quarantined leftovers, and old workspace-brain outputs into legacy.
- Consolidated the `debug` agent onto the canonical workspace by repointing its workspace to `~/.openclaw/workspace` while keeping its explicit no-fallback `gpt-5.4` model configuration.
- Retired the old `workspace-debug` tree as an active code/runtime workspace and archived its prior contents into `legacy/2026-03-15-workspace-debug-retired/`, leaving only a minimal retirement marker in the old directory.
- Post-cleanup audit remained clean for the active workspace (`broken_symlinks=0`, `tmp_sensitive=0`, `hardcoded_disallowed=0`, `naive_time_calls=0`), confirming the cleanup did not damage the live Ravenclaw runtime path.

## 0.8.35 / 2026-03-15
- Closed the post-audit creative execution gap after priorities 1–4, implementing the follow-on plan from `implementation-plans/2026-03-15-creative-execution-gap.md` and validating the new execution path on the real workspace.
- Brought policy-gate behavior into parity with the capability-first contract/compiler flow: `policy_gateway.py` now compiles/resolves the semantic action before enforcing tool allowlist, scope, and credential policy, so capability-resolvable actions no longer fail simply because `tool` was omitted by BRAIN.
- Shifted execution preparation to the compiled/final tool path in `run_pipeline.py`: final action specs are now built through `prepare_action_spec_for_execution(...)`, so curl/header/output normalization follows the resolved execution plan rather than raw `brain.tool`.
- Added bounded named recipe support and simple artifact handoff for chained execution: `capability_recipes.yaml` / `.py` now define deterministic named recipes, and `executor.py` now exposes per-step artifacts plus bounded placeholders like `prev_stdout_path` and `prev_stderr_path` for follow-up steps without enabling shell composition.
- Added explicit execution-mode control via pipeline flags (`normalized` vs `faithful`), so first-pass tool rewrites and curl instrumentation can be disabled intentionally when the operator wants higher-fidelity execution semantics.
- Added regression coverage for policy-gate capability-first parity, recipe lowering, faithful-vs-normalized execution prep, and executor handoff behavior; focused validation passed at `13 passed`, and full repository validation now passes at `160 passed`.

## 0.8.34 / 2026-03-15
- Completed the next logic-focused Ravenclaw improvement wave after the 2026-03-15 audit, implementing priorities 1–4 from `implementation-plans/2026-03-15-ravenclaw-priorities-1-4.md` and validating the result end-to-end on the real workspace.
- Added a capability-first recipe layer with `capability_recipes.yaml` / `capability_recipes.py`: task families can now resolve contextual planner profiles and deterministic tool candidates from capability metadata instead of relying only on hardcoded task-family tool ordering.
- Relaxed the semantic action contract so capability-resolvable actions no longer require an explicit `tool` up front; `contracts.py`, `action_compiler.py`, and `run_pipeline.py` now support optional tool omission with deterministic compiler resolution, richer planner hints, and profile-aware preferred tool selection.
- Promoted canonical runtime decision fields (`requested_action`, `requested_reason`, `effective_action`) across runtime decision/projection/effective-decision modules while preserving compatibility with legacy decision flags for current snapshot/Logdash consumers.
- Split persistence from adaptation/regeneration: `runtime_persist_services.py`, `runtime_run_completion.py`, `runtime_session_bootstrap.py`, `runtime_runner_deps.py`, and runner wiring now treat record/persist as one explicit stage and regeneration/adaptation as a second explicit stage.
- Expanded learning and utility modeling: `learning_store.py` now tracks families, hosts, capabilities, tools, action types, and host stages; `decision_quality.py` now scores novelty, reproducibility, false-positive risk, and artifact quality; `runtime_utility.py` now consumes those richer signals without breaking legacy inputs.
- Added and updated regression coverage for capability recipes, capability-first contracts/compiler behavior, runtime decision canonicalization, persist-vs-adaptation staging, direct learning-store behavior, and richer decision-quality/utility scoring; targeted gate passed at `36 passed`, and full repository validation now passes at `154 passed`.

## 0.8.33 / 2026-03-15
- Performed a post-refactor recovery/checkpoint pass on the real `~/.openclaw/workspace` after the Stage 3 + semantic execution waves, reconstructing continuity from repo checkpoints/daily notes and validating the still-unreleased maintenance/runtime changes against the live workspace rather than `workspace-debug`.
- Added registry-driven tool governance with `tool_registry.yaml`, `tool_registry.py`, and `tool_registry_audit.py`: execution-allowed tools are now separated from planner-visible profiles, planner tool exposure can be switched by profile, and whitelist/profile alignment is covered by tests so the default core surface stays tight while richer profiles remain opt-in.
- Hardened semantic action contracts and execution lowering across `action_schema.py`, `action_validators.py`, `action_compiler.py`, `contracts.py`, `policy_gateway.py`, `policy_core.py`, `executor.py`, and `run_pipeline.py`, including bounded `tool_chain` support, richer semantic probe metadata, auditor provenance/contract enrichment, and deterministic blocking of shell operators/placeholders leaking through tool-chain args.
- Added maintenance and safety scaffolding with `time_utils.py`, `json_state_io.py`, `health_audit.py`, and related runtime/logdash wiring; the workspace now has explicit audit coverage for hardcoded workspace paths, naive UTC calls, broken symlinks, and sensitive tmp leftovers, with quarantine/hygiene cleanup folded into the same wave.
- Extended Logdash/System Settings to expose the active planner tool level/profile and related runtime state so operator controls match the new registry model instead of assuming one flat tool surface.
- Expanded regression coverage for semantic action v2, executor plan execution, tool registry/profile resolution, health audit, JSON state IO, runtime adaptation/auditor provenance, and snapshot/logdash integration, and closed the remaining policy guard gap found during recovery; full repository validation now passes at `147 passed`.

## 0.8.32 / 2026-03-12
- Completed the post-alignment semantic pipeline wave across ANALYSIS, LIGHT/reporting, decision learning, utility scoring, and campaign state modeling.
- Added `analysis_contract.py` and threaded semantic analysis outputs through post-processing/reporting: runs now carry experiment-aware fields such as `expected_signal_observed`, `evidence_goal_met`, `hypothesis_support`, and `semantic_execution_fit`, while LIGHT/reporting surfaces those semantics instead of flattening everything to generic partial/success statuses.
- Revised success semantics in runtime planning: runtime tasks now carry `success_semantics` by family (e.g. differential/stateful signal vs surface expansion vs fingerprint/exposure), preparing the system to judge experiments by evidence goals rather than only command execution outcomes.
- Added decision-quality and campaign-learning foundations via `decision_quality.py`: per-run quality scorecards, information-gain signals, planner override value, semantic-loss penalties, and aggregated action-type yield / override success metrics now persist with runtime history.
- Added utility scoring via `runtime_utility.py` and integrated it into queue prioritization/economics so the runtime can weight actions not only by signal but also by net expected value, noise, and redundancy penalties.
- Introduced a first campaign state machine with `campaign_state_machine.py`: runs now persist `campaign_state.family_state` and `campaign_state.host_stage`, snapshots expose `campaign_stage`, and the pipeline now has explicit lifecycle modeling instead of relying only on implicit heuristics.
- Preserved compatibility and validation quality across the wave; full repository validation now passes at `127 passed`.

## 0.8.31 / 2026-03-12
- Completed the planner/brain/engine alignment wave after the runtime refactor: runtime plan entries now preserve richer planner rationale (`preferred_vector_families`, deprioritized families, ambiguity/conflict hints, target profile summaries, aggression profile hints, evidence goals), and `run_pipeline.py` now feeds target-aware planner context plus richer recent-runtime summaries into BRAIN.
- Expanded the BRAIN contract beyond plain `tool + args`: runtime now validates and persists reasoning fields such as `hypothesis`, `why_now`, `planner_alignment`, `planner_override_reason`, `expected_signal`, `evidence_goal`, and branch hints (`next_if_positive` / `next_if_negative`).
- Implemented planner feedback enrichment: runtime now summarizes planner alignment, override frequency, redundancy, partial/not-met outcomes, degraded hosts, and next-family hints for planner reconsult and runtime regeneration triggers.
- Implemented the semantic execution upgrade (Priority E) without introducing shell freedom: added `action_type`, `probe_recipe`, semantic validators, `action_compiler.py`, policy awareness for semantic actions, compiler telemetry, and runtime/logdash exposure for `action_type_count`, `semantic_loss_total`, and compiler lowering details.
- Extended semantic action support across the stack for `single_probe`, `differential_probe`, `confirmatory_probe`, `enumeration_probe`, `variant_probe`, `fingerprint_probe`, and bounded `state_transition_probe`, keeping backward compatibility with existing `tool + args` flows.
- Added coverage for enriched planner/runtime contracts, semantic action validation/compiler/policy behavior, planner feedback aggregation, runtime snapshot/logdash telemetry, and preserved full green validation at `121 passed`.

## 0.8.30 / 2026-03-12
- Completed the Stage 3 runtime-decision cleanup pass: downstream effective scheduling now lives in `runtime_effective_decision.py`, with canonical effective statuses (`noop`, `blocked`, `applied`, `partial`) and fixed counter/cooldown semantics for duplicate-suppressed confirm/follow-up actions.
- Reduced runner-owned decision glue by extracting `runtime_decision_projection.py`, `runtime_run_completion.py`, and `runtime_task_execution.py`; the main runner now delegates execution pipeline, projection, persistence/reconsult, and post-run application through dedicated modules.
- Extracted curated/main loop control into `runtime_loop_control.py`, introduced `runtime_runner_context.py`, `runtime_execution_deps.py`, `runtime_runner_deps.py`, `runtime_prepare_deps.py`, `runtime_precheck_context.py`, and `runtime_persist_services.py` for more explicit dependency wiring, and moved the finalize/flush tail plus session execution split into `runtime_runner_finalize.py` and `runtime_runner_main.py`.
- Introduced `RuntimeSessionState` and `runtime_session_flow.py`, so runner bootstrap/session state are now modeled more explicitly and `main()` delegates the primary runtime flow instead of holding the full control loop inline.
- Added semantic/runtime consistency coverage for effective decision behavior, runner context/finalize flows, loop control, task execution, session state/flow, and snapshot-to-Logdash integration; full repository validation now passes at `107 passed`.
- Created refactor checkpoints during the series: `013b064` (`Stage 3 effective decision contract and scheduling fixes`), `628692b` (`Refactor runtime runner loop control and context wiring`), `1188d41` (`Finalize runtime runner context and output tail extraction`), `77085c7` (`Reduce runtime callback sprawl and refresh refactor docs`), `866cd7d` (`Extract runtime prepare and persist service contexts`), `12b3cff` (`Introduce runtime session state for runner bootstrap`), `dfbedef` (`Split runtime runner session execution from main`), and `964dfc6` (`Polish runtime runner state aliasing and finalize checkpoint`).
- Finalized the operator-facing checkpoint for this refactor wave with tag `checkpoint-2026-03-12-runtime-stage3-complete`, marking Stage 3 plus the primary runner modularization pass as stable and ready to pause.

## 0.8.29 / 2026-03-11
- Closed the most important runtime decision-consistency gap: `auto_campaign_finalize.py` now receives live runtime toggles instead of hardcoded downstream defaults when building the canonical decision record.
- Extended `RuntimeDecisionRecord` with effective downstream scheduling fields so the runtime can distinguish decision intent from the action that was actually queued after caps/cooldowns/dedup checks.
- Updated `auto_campaign_runner.py` so post-run orchestration consumes the existing decision record intent instead of recomputing it, and run persistence now happens after effective retry/confirm/followup/precision scheduling is known.
- Reporting artifacts now expose both decision intent and effective downstream outcomes, including effective flags, blockers, and a compact scheduling summary in archived run details and summary vectors.
- Logdash now exposes decision intent vs effective downstream outcomes in `/api/finding-quality`, `/api/findings-table`, and the findings detail UI, including blockers/reasons and session-level intent/effective totals.
- Reduced queue/orchestration duplication by routing runner enqueue/dequeue operations through `QueueCoordinator` while keeping current queue semantics intact.
- Completed the next host-model hardening pass: `runtime_host_model.py` now returns explicit state transitions, delta scores, and regeneration hints; persistence annotates each run with host transition metadata before saving state.
- Host explainability was improved in Logdash: host state endpoints now expose transition context, and findings detail panels surface host band/transition/regeneration hints alongside decision explainability.
- Added/updated tests around finalize/runtime-decision behavior, queue coordination, host-model persistence, and Logdash API exposure; full repository validation now passes at `62 passed`.
- Continued Stage 3 execution-gate work: precheck now returns a structured gate contract with `allowed` / `reason_code` / `gate` payload, runner threads `execution_gate` into executed runs, and findings/report views now surface gate reason/blockers/state-band for operator review.
- Cleanup pass on runtime skip telemetry: execution-gate block reasons now share a consolidated summary flow, and live queue state persists dedup/DNS/cooldown/execution-gate skip counters for easier operator debugging and resume-state inspection.
- Began orchestration extraction from `auto_campaign_runner.py`: introduced `runtime_orchestrator.py` to own deduped curated-plan building, curated-queue preemption, queued-task unpacking, and prepared-task construction for curated/runtime execution paths.
- Continued that extraction by moving main-loop next-task resolution (queue selection vs brain proposal vs deterministic fallback) into `runtime_orchestrator.py`, reducing more inline selection logic in the runner.
- Started the next state-contract cleanup: `auto_campaign_state.py` now emits a canonical `.runtime_snapshot.json`, and Logdash runtime/queue loading can read queue + telemetry state from that snapshot with fallback to legacy files.
- Expanded snapshot adoption in Logdash so `campaign-info`, `runtime-health`, `metrics`, and `finding-quality` also consume snapshot fields with legacy fallbacks, reducing more scattered state assembly in the UI/API layer.
- Extended the snapshot contract further with runtime plan/meta, host summary/by-host state, and aggregate economics; `host-state`, `host-explain`, and `family-yield` now prefer snapshot data before falling back to older per-file state.
- Tightened planner/runtime projections around the same contract: `api_planner`, `api_runtime`, and campaign-setup UI projections now prefer snapshot-backed plan/campaign values where available, reducing additional legacy state stitching.
- Resumed runner/control-loop cleanup immediately after the snapshot pass: extracted planner-hint refresh, runtime-plan regeneration, and active-plan reconciliation helpers into `runtime_plan_control.py`, leaving `auto_campaign_runner.py` with less inline plan-control logic.
- Continued the same cleanup by extracting runtime override refresh into `runtime_override_control.py` and family-weight / queue reprioritization logic into `runtime_queue_strategy.py`.
- Added/updated control-loop coverage for the new plan-control/override/queue-strategy modules and reran the full repository suite successfully; validation now passes at `81 passed`.
- Created a local recovery checkpoint for this refactor state: commit `fcc8114` (`Checkpoint runtime snapshot and control-loop extraction`) and tag `checkpoint-2026-03-11-runtime-refactor`.

## 0.8.28 / 2026-03-10
- Performed a full architecture/documentation alignment pass for the active `~/.openclaw/workspace` runtime: updated `README.md`, added `ARCHITECTURE.md` and `STATE_FILES.md`, refreshed `logdash/README.md`, and rewrote `SOUL.md` so repository docs now better match the real governance-first planner/policy/execution/runtime/control-plane stack.
- Synchronized role guidance with the current runtime model by updating per-role system memory for BRAIN and AUDITOR, adding explicit runtime role memory for ANALYSIS and LIGHT, and aligning local role stubs so all primary runtime agents now reflect the same post-refactor governance model.
- Repaired multiple Logdash regressions introduced by earlier refactors: restored missing global `STATE`, restored page routes (`/`, `/findings`, `/campaign-setup`, `/owner-actions`, `/system-settings`), restored `/api/agents-status`, and brought the dashboard service back to a stable `127.0.0.1:9091` runtime.
- Removed the legacy `Runtime Logs` block from Pipeline Monitoring and cleaned up its frontend handlers, reducing dead UI surface and avoiding JS drift after the runtime/logging changes.
- Audited the full Logdash frontend↔backend contract and restored missing API surface required by templates, including campaign/runtime status, logs, metrics, host state, family yield, finding quality, findings table, owner approvals, planner campaign selection, and other live dashboard dependencies.
- Refactored Logdash from a monolithic `logdash/app.py` into a more modular control plane: introduced `pages.py`, `api_runtime.py`, `api_planner.py`, `api_supplemental.py`, `state.py`, and `services.py`, leaving `app.py` primarily as bootstrap/wiring.
- Added Logdash audit and maintenance documentation (`logdash/LOGDASH_AUDIT.md`, `logdash/LOGDASH_UI_PASS_2026-03-10.md`) so the current dashboard contract, post-refactor repairs, and UI cleanup decisions are traceable.
- Added smoke coverage for Logdash in `tests/test_logdash_smoke.py`, including page GET coverage and key API/status checks, then extended test coverage to POST flows such as planner selection, campaign settings, campaign control, and owner override.
- Restored planner/document workflow actions expected by Campaign Setup after the pipeline refactor by adding `/api/planner/run`, `/api/planner/scope-view`, `/api/planner/blueprint-view`, and `/api/planner/budgets-view`, wiring the planner run path back to `engine/plan_campaign.py`.
- Improved `campaign-info` to surface more truthful runtime-plan state (`planner_scope_targets`, `prepared_attacks`, `runtime_plan_ok`, `runtime_plan_error_preview`, revision/quality metadata), reducing semantic drift between dashboard readiness panels and the real runtime-plan state files.
- Performed a broad UI/UX reconciliation pass across Pipeline Monitoring, Findings, Campaign Setup, Owner Actions, and System Settings: renamed misleading labels where values are derived/placeholder-like, removed duplicated metrics, reordered workflow actions to match real operator flow, removed low-value escalation panels, and clarified copy so the dashboard language now better matches post-refactor pipeline/runtime reality.
- Added a new `/api/policy-gate-history` endpoint and reconnected the Policy Gate History panel so it no longer points at missing backend functionality.
- Completed a final visual polish pass on Logdash: improved spacing/padding/radii, softened badge hierarchy, introduced reusable empty states, improved button microcopy, and made zero-data/error states read as intentional UX rather than raw fallback placeholders.
- Simplified `System Settings` around the real runtime model: removed `parallelism` entirely from active UI/config handling, moved `target load limit` into advanced tuning, and clarified the split between execution limits, decision policy, and lower-level runtime tuning.
- Validation after the full 2026-03-10 refactor/polish pass: Logdash smoke tests pass and the full repository test suite remained green at `44 passed`.

## 0.8.27 / 2026-03-09
- Continued the auto-campaign modular extraction beyond helper cleanup: runner logic is now split across dedicated modules for downstream decisions, qualification/lifecycle, precheck-gating, post-result normalization, final qualification/logging, persistence/host-state bookkeeping, and shared health/aggression logic.
- Added targeted unit coverage for the newly extracted modules (`auto_campaign_downstream`, `auto_campaign_qualification`, `auto_campaign_precheck`, `auto_campaign_postprocess`, `auto_campaign_finalize`, `auto_campaign_persistence`), and kept the focused suite green while refactoring (`21 passed`).
- Reworked `auto_campaign_runner.py` into a clearer orchestration shape by introducing a shared `_execute_runtime_task(...)` path plus source-side preparation helpers for curated inputs vs queue/brain-driven runtime tasks, reducing the main control flow toward a more explicit `source -> prepare -> execute` model.
- Removed thin transitional wrappers after direct module call sites were stable, further shrinking runner-local duplication and making the remaining responsibility of the runner more obviously about task sourcing and control-flow coordination rather than embedded business logic.

## 0.8.26 / 2026-03-09
- Continued the auto-campaign runner refactor with a cleaner staged execution flow: shared helpers now cover runtime override refresh, dispatch/runtime invocation, precheck-gating, common post-result normalization, qualification/finalization, and post-run queue orchestration.
- Tightened downstream queue semantics so `confirm` takes precedence, `followup` remains the first exploratory escalation step, and `precision` is now queued as a second-step refinement after an ambiguous follow-up instead of competing in parallel with it.
- Removed runner cleanup artifacts and duplicated logic (including duplicated host-health checks, residual legacy task naming drift, duplicate aggression-hint assignment, and repeated curated/main-loop bookkeeping), leaving the file in a more testable state for further modular extraction.

## 0.8.25 / 2026-03-08
- Added operator-configurable custom request headers (`custom_headers_enabled` + `custom_headers`) to System Settings and executor runtime wiring.
- Executor now injects configured headers for supported web tools (`curl`, `ffuf`, `gobuster`, `feroxbuster`, `katana`, `httpx-pd`/`httpx`) so campaign-specific disclosure headers can be applied consistently without hand-editing commands.

## 0.8.24 / 2026-03-08
- Changed `content_discovery` first-pass behavior to prefer lighter crawl/URL-enumeration tools (`katana`, `gau`, `ffuf`) before heavier `feroxbuster` usage.
- Added runtime normalization so `feroxbuster` chosen by BRAIN for first-pass `content_discovery` is converted to `katana` when available, mirroring the earlier TLS first-pass enforcement pattern.

## 0.8.23 / 2026-03-08
- Installed ProjectDiscovery `httpx` as `httpx-pd` to avoid collision with the Python HTTPX CLI already present on the system.
- Repointed TLS first-pass/runtime normalization and recommended-tool paths to `httpx-pd`, restoring the originally intended fast TLS probe workflow without relying on the wrong binary name.

## 0.8.22 / 2026-03-08
- Adjusted TLS first-pass again after live debugging revealed `/usr/bin/httpx` is the Python HTTPX CLI rather than ProjectDiscovery's scanner. Runtime now uses a fast `curl` TLS/header probe for first-pass `tls_assessment` and reserves `testssl.sh` for deeper follow-up use.

## 0.8.21 / 2026-03-08
- Enforced `httpx` as the runtime-normalized first-pass tool for `tls_assessment` when BRAIN tries to pick `testssl.sh`, closing the remaining gap where prompt/fallback preference alone was not sufficient.

## 0.8.20 / 2026-03-08
- Changed `tls_assessment` first-pass behavior to prefer fast `httpx -tls-probe` style checks before `testssl.sh`, reducing slow/timeout-prone TLS tasks during live runtime operations.
- Kept `testssl.sh` available as a richer/deeper TLS tool but moved it behind lighter probes in runtime fallback/recommended-tool ordering.

## 0.8.19 / 2026-03-08
- Added sensitive-host warm-up gating in the runner so auth/webhook-style targets must first pass lower-noise families (`tls_assessment`, `recon`, `historical_url_mining`) before heavier lanes like `content_discovery`, `authz`, `auth_flow`, or `logic` are allowed.
- Added owner-approval-aware family deprioritization in queue scoring and execution gating so lanes repeatedly hitting `owner_approval_required` are actively suppressed instead of being retried as primary paths.

## 0.8.18 / 2026-03-08
- Added deterministic aggression caps by task family and sensitive host type (especially auth/webhook/integration-style hosts) in both runtime-plan generation and runner-side execution/follow-up paths.
- Reordered seeded families to be more low-noise-first on auth/webhook-sensitive hosts so TLS/recon/historical work is preferred before heavier boundary/content lanes.
- Added a simple owner-approval loop breaker so repeated `owner_approval_required` outcomes on the same host/family suppress further confirm/follow-up escalation in that lane until state changes.

## 0.8.17 / 2026-03-08
- Relaxed planner schema handling for malformed scope-token remnants: invalid domain-like candidates no longer hard-block blueprint generation when valid authoritative domains are present; they are now carried as warnings/interpretation artifacts instead.

## 0.8.16 / 2026-03-08
- Fixed System Settings/source-of-truth drift for new adaptation controls by registering the newer runtime flags in `engine/feature_flags.py`; this restores stable toggle behavior and prevents `undefined` values for the family decay controls in the UI.

## 0.8.15 / 2026-03-08
- Closed the most important last-mile `runtime_task` unification gaps before live testing: queue-path execution and run-info fields now read from the active normalized task rather than leaking back to stale legacy objects.
- Reduced the remaining task-object drift to naming/readability residue only, making the runner substantially safer to debug during upcoming manual real-run validation.

## 0.8.14 / 2026-03-08
- Continued the runtime-runner cleanup toward a single execution flow: introduced a shared `handle_post_run_actions()` helper and collapsed duplicated retry/confirm/followup/precision queue orchestration out of both runtime loops.
- Kept the runner compiling after centralization and updated `TODO.md` to reflect the remaining last-mile cleanup around residual legacy task-field access rather than the earlier larger duplication issues.

## 0.8.13 / 2026-03-08
- Cleaned up key runtime-runner duplication points: removed duplicate 403 streak handling and duplicate qualification/control-comparison logging in the curated loop.
- Moved runtime logic further toward a single normalized task object via `normalize_runtime_task()` and started using centralized post-run helpers (`compute_promising`, `post_run_decision`) instead of scattered overlapping heuristics.
- Tightened default runtime sensitivity after the recent adaptation expansion: planner reconsult now defaults to a less noisy cadence/threshold and qualification-driven promising/follow-up defaults are set to `probable` rather than `weak_signal`.
- Upgraded reconsult into tiered semantics (`light` vs `structural`) so runtime can adapt planner refresh intensity more coherently with current host-state shifts instead of treating all reconsults as equivalent.

## 0.8.12 / 2026-03-08
- Added top host-state and family-yield panels to the main Logdash dashboard so adaptation signals are visible without switching to Findings.
- Added per-host explainability via `/api/host-explain` and Findings UI "Explain" actions, exposing why a host is promising/degraded and which families/objectives are being favored for it.

## 0.8.11 / 2026-03-08
- Added family decay/cooldown controls so overrepresented task families naturally lose scoring weight over a recent run window instead of monopolizing adaptive planning.
- Added per-host family lane controls (`host_family_lane_boost`, `host_family_lane_suppress`) with System Settings UI support, enabling precise host-scoped family steering during active campaigns.

## 0.8.10 / 2026-03-08
- Extended runtime queue scoring to become family-yield-aware, so families with recent promising/probable/confirmed results receive an adaptive scoring boost instead of relying only on static heuristics.
- Added operator family-lane controls in System Settings (`family_lane_boost`, `family_lane_suppress`) so specific task families can be manually promoted or dampened during active campaigns.
- Added more explainable plan-diff semantics by surfacing a human-readable `diff_reason` (e.g. promising host shift, degraded host state, periodic refresh) alongside exact added/deprecated tasks.

## 0.8.9 / 2026-03-08
- Added family-yield telemetry endpoint and Findings UI panel so operators can see which task families are producing promising/probable/confirmed results versus noise.
- Improved host-state explainability in Findings UI by surfacing simple state rationale (promising/degraded/steady) instead of only raw scores.
- Added adaptation controls to System Settings (`dynamic_plan_adaptation`, `freeze_plan_revision`, `aggressive_adaptation`) and wired the runner to honor them when deciding whether/how often to regenerate plans.

## 0.8.8 / 2026-03-08
- Added material-change thresholding to runtime-plan regeneration so small diffs no longer churn plan revisions; non-material updates are logged as skipped instead of forcing active-plan turnover.
- Extended runtime-plan metadata with exact added/deprecated task examples and surfaced them in Findings UI for concrete operator-visible plan diffs.

## 0.8.7 / 2026-03-08
- Added auto-regeneration triggers in the auto-campaign runner based on host-state shifts and periodic campaign checkpoints; regenerated plans now flow through the new revision-aware safe-boundary reconcile path.
- Extended runtime-plan metadata with added/deprecated task counts and surfaced revision/diff/reason summaries in Logdash so dynamic plan changes are visible instead of opaque.
- Findings UI now shows runtime-plan revision/diff metadata, making deprecated/new plan changes operator-visible during active campaigns.

## 0.8.6 / 2026-03-08
- Added runtime plan versioning (`plan_revision`, `plan_hash`, regeneration reason) to runtime-plan metadata so runners can detect meaningful plan changes without blind file overwrite semantics.
- Added safe-boundary curated-plan reconcile in the auto-campaign runner: new plan revisions are detected between tasks, diffed, and applied only to the curated layer without interrupting in-flight work or wiping follow-up/precision execution state.
- Logged reconcile events with added/deprecated counts so dynamic plan adaptation remains auditable during active campaigns.

## 0.8.5 / 2026-03-08
- Exposed host-state snapshot in Logdash via `/api/host-state` and added Findings UI visibility for host promise/noise/evidence trends.
- Added richer Findings controls for candidate targets: promote, defer, and reject actions now map to lifecycle-backed review states instead of a promote-only list.
- Extended Findings runtime-plan preview to show task family, score, cost band, and recommended tools from the shared `runtime_task` object.
- Follow-up family selection can now be overridden by `analysis.next_family_hint`, allowing evidence-driven family pivots instead of relying only on static family mapping.

## 0.8.4 / 2026-03-08
- Runtime plan entries now carry a shared `runtime_task` object with family, priority score, cost band, recommended tools, evidence requirements, and follow-up policy to reduce duplicated reconstruction across planner/runtime layers.
- Added host-state snapshot persistence in `reports/.host_state.json` so runtime can track per-host promise/noise/evidence trends and feed queue reprioritization with campaign-state rather than only static catalog heuristics.
- Improved queue scoring with cost-awareness (`low|medium|high`), host-state multipliers, target score, and recommended task-family signal weighting.
- Added family-aware follow-up pivots (e.g. historical→content discovery, auth_flow→authz, authz→logic) instead of blindly reusing the previous family on follow-up jobs.
- Expanded runtime AUDITOR contract toward fully structured policy semantics by adding `risk_band` and `owner_gate` alongside `decision` + `reason_code`.
- Expanded ANALYSIS contract to distinguish `evidence_artifacts` from observations/signals and to return `next_family_hint` for evidence-driven family pivots.
- Added candidate-target lifecycle states (`pending`, `promoted`, `rejected`, `deferred`) so candidate scope review is auditable beyond a simple pending list.

## 0.8.3 / 2026-03-08
- Wired PLANER `task_family_seeds` directly into runtime-plan generation so curated tasks are now seeded from blueprint family intent instead of deriving everything again from generic objectives.
- Added deterministic host/task scoring to runtime plan generation and auto-campaign queue reprioritization, using target class + task family so higher-value hosts/families surface earlier with less token waste.
- Added Logdash API support for promoting `candidate_targets_from_llm` into authoritative scope, updating blueprint JSON/YAML and re-rendered campaign templates in one flow.
- Extended auto-campaign planner weighting to respect `recommended_task_families`, explicit task family tags, and per-entry `target_score`.

## 0.8.2 / 2026-03-08
- Refactored PLANER scope-to-blueprint flow to better separate authoritative deterministic scope from softer LLM interpretation: LLM-added domains now land in `candidate_targets_from_llm` instead of being silently merged into final in-scope targets.
- Hardened scope parsing with stricter domain validation and concatenated-TLD rejection to prevent malformed scope artifacts from entering blueprints.
- Expanded target taxonomy beyond `api/web/other` with richer classes (`auth`, `static`, `sandbox`, `integration`, `support`) and added per-target `task_family_seeds` so planner output now aligns with the more advanced runtime family-driven routing.
- Restructured `planner_hints` into a richer shape (`global_vectors`, `per_target_vectors`, `recommended_task_families`, `candidate_targets`, ambiguities/conflicts) and updated runtime loaders to consume the new form while remaining backward compatible.
- Added semantic blueprint validation checks for empty/flat taxonomy, invalid domain candidates, and LLM-used-without-hints cases.
- Unified final campaign rendering by generating richer `campaign.md` content directly from blueprint scope + task-family data instead of a near-empty overlay stub.

## 0.8.1 / 2026-03-08
- Refactored tool-policy source of truth: added `brain_allowed_commands` to `whitelist.yaml` so BRAIN prompt/contracts now derive from YAML instead of hardcoded Python subsets.
- Added whitelist documentation comments clarifying executor/runtime vs BRAIN planning tool boundaries and subset expectations.
- Tightened BRAIN tool contract path: `contracts.py` now validates against the BRAIN subset rather than the full executor allowlist, preventing meta/helper tools like `echo` from being considered valid planning outputs.
- Added BRAIN argument-shape guards in `contracts.py` (max args, shell-operator ban, placeholder ban) to reduce pseudo-shell plans while preserving in-scope creative payload selection.
- Reduced planner-hint prompt drift: `run_pipeline.py` now injects a trimmed planner-hints view (top vectors/ambiguities/conflicts) instead of the full blob.
- Expanded deterministic BRAIN fallback behavior to be task-family/history-aware rather than always collapsing to the same generic curl probes.
- Tightened runtime AUDITOR prompt in `engine/run_pipeline.py`: reframed AUDITOR as a deterministic policy gate, discouraged objective reinterpretation/creative reasoning, and nudged compact reason-code style outputs for lower token drift and more stable downstream handling.
- Extended runtime AUDITOR contract toward `reason_code` + compact `reason` detail, with normalization/fallback mapping in pipeline handling.
- Tightened ANALYSIS prompt to separate observations from security signals and added confidence/next-step structure to reduce overclaiming.
- Tightened LIGHT prompt/contract so LIGHT acts as formatter-only summary (`summary` + conservative `next_step`) without inventing new conclusions.
- Added prompt-quality telemetry surfaced in Logdash Runtime Health: invalid BRAIN tool attempts, BRAIN fallback count, ANALYSIS contract failures, LIGHT fallback count, and top AUDITOR reason-code distribution.
- Expanded active allowlists for bug-bounty workflow with userland-installed tools `arjun`, `testssl.sh`, `katana`, and `gau`; these were added to executor allowlist and BRAIN planning subset where they fit one-step action specs.
- Execution engine PATH now includes `~/.local/bin` so userland-installed tooling can be executed without system-wide package installs.
- Further expanded BRAIN soft-routing and deterministic fallback logic using task family + recent context/history, so recon can pivot into URL harvesting/crawling, parameter discovery, and TLS checks instead of collapsing into repetitive generic curl probes.
- Installed additional bug-bounty tooling with root privileges where needed: `feroxbuster`, `hakrawler`, `assetfinder`, `dnsgen`, `gitleaks`, and `trufflehog`.
- Promoted `feroxbuster`, `hakrawler`, `assetfinder`, and `dnsgen` into the active executor allowlist and BRAIN planning subset; kept `gitleaks` and `trufflehog` executor-only to avoid over-eager default planner use.
- Expanded family-driven tool routing so BRAIN can now prefer crawling/content-discovery/subdomain-enumeration tools by task family and recent-history signals instead of overusing generic HTTP probes.
- Added more explicit runtime-recognized task families in BRAIN routing/prompting: `subdomain_expansion`, `historical_url_mining`, `content_discovery`, `tls_assessment`, and `secret_hunt`.

## 0.8.0 / 2026-03-07
- Runtime planner reconsult now applies operationally (not only logs): added planner hints refresh + immediate queue reprioritization in `engine/auto_campaign_runner.py` with `contextual_reconsult_applied` telemetry.
- Expanded policy-gate/tooling model from hardcoded 6 tools to whitelist-driven runtime set: `policy_core.ALLOWED_TOOLS` now loads from `whitelist.yaml`, contracts consume the same source, and executor supports direct passthrough for whitelisted tools.
- Whitelist hygiene hardening: deduplicated/sorted command set, removed invalid shell-builtin entry (`export`) from active allowlist, moved `info/tailf` to optional, and validated zero missing binaries in active set.
- Added policy alignment consistency guard `engine/verify_policy_alignment.py` plus Git `pre-commit` hook to block commits when `whitelist.yaml`, policy-core, and contracts drift.
- Added recommended tools to active whitelist for Kali workflows (`httpx`, `nuclei`, `whatweb`, `dnsx`, `jq`, `xargs`, `bash`) and preserved runtime alignment checks.
- Global aggression override made effective in runner: `aggression_override` from campaign settings now overrides planned/queued per-task aggression (clamped), with runtime change events (`aggression_override_runtime`) for auditability.
- Clarified override semantics in runtime: aggression override now works independently from owner-override; owner-override still controls auditor/policy bypass path.
- Logdash runtime state reliability patch: added live state refresh based on PID/state files + `/proc` process fallback + recent orchestrator activity fallback, reducing false `idle` in Agentic Roles cards.
- Added state persistence primitives in logdash (`_write_runtime_state_file`, `_sync_pid_file`) and wired them into campaign control/settings/owner-override paths to keep `.auto_campaign.state.json` and `.auto_campaign.pid` synchronized.
- Re-enabled Campaign Setup planner workflow API surface in logdash: added missing endpoints (`/api/planner/run`, `/api/planner/selection`, `/api/planner/campaigns`, `/api/planner/approve`, `/api/planner/generate-runtime-plan`, `/api/planner/runtime-plan-view`, `/api/planner/scope-view`, `/api/campaign/validate-plan`, `/api/campaign/activate-from-blueprint`) plus clearer frontend error text for missing backend routes.
- Scope parsing reliability fixes: out-of-scope boundary handling now preserves later "Starting Domains" sections, parser emits `out_of_scope_targets`, and added diagnostics endpoint `/api/planner/scope-parse-preview` + boundary regression test (`engine/planer/tests/test_scope_parser_boundaries.py`).
- Owner Actions `Delete current plan` now performs full cleanup (runtime artifacts + selected campaign state) and removes selected planner registry entry so it disappears from Campaign Setup dropdown.
- Campaign Setup workflow UX updated: ordered step buttons (Quick Prepare first), corrected quick-prepare execution order, and simplified Document Viewer to 4 views (Scope preview, Blueprint preview, Runtime plan preview, Budget review).
- Success-criteria chain hardening: runtime plan entries now include `variant`, `success_criteria`, `acceptance_checks`, `evidence_required`; runner forwards `--success-criteria` into `run_pipeline`; BRAIN prompt/context include success criteria; pipeline now emits `success_criteria` evaluation (`met|partial|not_met` with evidence/gap) and persists this in run records.
- Success criteria v2 (dynamic): replaced single campaign-wide success text on all tasks with task-family-aware criteria (`task_success_criteria`) plus explicit `campaign_success_criteria`, `task_family`, `success_scope`, `acceptance_checks`, `evidence_required`; propagated end-to-end through runner -> pipeline -> analysis payloads.
- Queue continuity for criteria context: retry/follow-up jobs now inherit task/campaign success criteria fields and evidence/check requirements to avoid semantic drift in later stages.
- Follow-up governance update: added `followup_skipped_by_success_eval` runtime event and gated follow-up scheduling by task success evaluation (`partial` eligible; `met/not_met` skipped).
- Logdash control-plane fixes: campaign start/pause/stop now control real runner process lifecycle (spawn/SIGSTOP/SIGCONT/SIGTERM), with persistent `stopped` state handling and improved PID/state synchronization.
- Pipeline Monitoring data model/UI alignment: moved quality metrics into Finding Quality, added extended metrics bindings (total/critical/new/verified/distributions/lifecycle), restored Agentic Roles after JS parser fix, and normalized campaign/runtime counters (`prepared_attacks`, `target_count`) with clearer semantics.

## 0.7.9 / 2026-03-06
- Logdash System Settings/UI hardening: moved Transport & Scope Guards under Campaign Limits (single-row slider layout), restored and stabilized Bug Bounty Credentials controls (separate credential state model, independent save path via `/api/campaign/settings`, anti-clobber on periodic refresh), removed stale/unused settings controls, and fixed Agentic Roles runtime cards by wiring `/api/agents-status` to live log-derived states with role descriptions.
- Added finding-quality observability to Logdash: new `/api/finding-quality` endpoint, Pipeline Monitoring "Finding Quality" panel, Findings-page lifecycle breakdown, and color-coded confirm-rate indicator (lime/crimson/bright yellow thresholds).
- Security qualification hardening: added deterministic evidence contract + qualification engine (`engine/vuln_qualification.py`) with verdicts `none|weak_signal|probable|confirmed`.
- Added per-class proof protocols (`engine/proof_protocols.py`) and protocol-gated confirmation (`repro_pass` required for `confirmed`).
- Added evidence policy gate (`engine/evidence_policy.py`) to prevent false-confirmed findings when controls/guards are missing.
- Added probe/control comparison runner (`engine/auto_campaign_controls.py`) for safe curl GET-like checks; includes control-target derivation, hash-based delta check, and explicit skip reasons.
- Integrated qualification + control artifacts into auto-campaign run records (`qualification`, `control_comparison`) and live tail events (`qualification_verdict`, `control_comparison`).
- Added confirmation-job queueing path for `probable` findings (toggle-driven), enabling second-step verification workflows.
- Added qualification benchmark scaffold (`engine/qualification_benchmark.py`) with starter dataset (`reports/qualification/benchmark_cases.json`) and quality metrics output (precision/recall/FPR).
- Refactor follow-up: moved state/reporting responsibilities into dedicated modules (`auto_campaign_state.py`, `auto_campaign_reporting.py`), removed dead pseudo-parallelism remnants (`parallelism` no-op loop), and kept runner closer to orchestrator role.
- Test coverage expanded for qualification/protocol/evidence/control modules; suite passing.
- Prompt-tuning control: added `prompt_token_budget` runtime flag (0-1250) and System Settings slider in logdash; pipeline now applies budget-aware prompt truncation for BRAIN/AUDITOR/ANALYSIS/LIGHT calls.

## 0.7.8 / 2026-03-05
- Logdash: unified badge system (states + FA icons), military palette refresh, glow/pulse tuning, and LED color mapping updates.
- Pipeline Monitoring: rebalanced layout (Campaign Context/Live Pipeline/Runtime Health), moved/renamed fields, pagination moved to footers, runtime logs + queue backlog panels, policy gate history with pagination.
- Runtime/health: new API endpoints for runtime state, health, queue state, runtime log tail, blueprint/budgets view; plan status now validated from .runtime_plan.meta.json.
- Campaign Setup: readiness block redesign, document viewer separated + blueprint/budgets buttons; quick prepare workflow button; credentials UI for bug bounty headers (bug_bounty_username/test_account_email) persisted to reports/.campaign.settings.json.
- Owner Actions: added clear logs + owner approval queue UI (approve/delete all stub).
- Agentic Roles: model names now sourced from ~/.openclaw/openclaw.json; status/LED mapping improved (run_state fallback).
- Metrics: avg confidence derived from blueprint.json (llm_confidence/aggression.confidence) instead of fixed 0.5.

## 0.7.7 / 2026-02-28 (late)
- Findings UI/UX: rebuilt the Workbench (severity/status/classification badges), removed the `Timestamp` column, improved the `Detail Panel` layout, and restored full-width `findings intelligence log` rendering.
- Fixed Findings pagination and capped page size at 10 records (table + log feed), with correct Next/Prev behavior and empty-page handling.
- Made Findings scoring more realistic: the frontend now uses only backend `confidence/cvss` values (removed 0.82/7.8 fallbacks), added record enrichment from `engine_stdout_preview` (`__RC_METRICS__`, `Potential finding`), and improved score differentiation.
- Fixed severity mapping: `failed/error` are no longer artificially mapped to `high`; added separate classification badges and more consistent coloring rules.
- Campaign continuity hardening: added durable findings storage in `reports/findings-history.jsonl` (append-only) and history reads via `/api/findings-table`, so entries no longer disappear after stop/start.
- Added campaign setting `resume_on_restart` (env `AUTO_RESUME`) and propagated `AUTO_CAMPAIGN_KEY` during start/resume.
- Auto-campaign: added persist/restore for `followup_queue` and `precision_queue` (`reports/.auto_campaign.queues.json`) to preserve triage across restarts.
- Pipeline robustness: hardened JSON contract parsing in `run_pipeline.py` (handling mixed output and "extra data"), removing `auditor JSON contract failure` style stalls.
- Scope/artifact cleanup: removed hardcoded Airbnb/HotelTonight references from the active flow, disabled resume by default in auto-campaign (with override support), reset `auto-campaign-latest.json`, and purged legacy artifacts.
- Planner vectors cleanup: removed automatic `robots.txt` and `/.well-known/security.txt` scans from runtime plans.

## 0.7.6 / 2026-02-28
- Added an adaptive aggression ladder: base levels 1/2/3 with selective follow-up escalation to 5/6/8 depending on signal strength and owner override.
- Fixed critical runtime regressions causing hangs/stop-flow issues: missing helpers (`parse_rc_metrics`, `adaptive_aggression`) and incomplete task hydration from `precision_queue`.
- Improved pipeline resilience to transport failures (`code=000`): retry <= 1, host cooldown after streaks, per-host session cap, and exclusion of `code=000` from the precision lane.
- Added new System Settings controls (Limits & Execution Boundaries): `code=000 streak threshold`, `code=000 session cap`, `code=000 cooldown`, and a `Skip deep on autodiscover hosts` toggle.
- Cleaned up the `auto_campaign` flow: target-plan dedup before the loop, per-host dedup burst throttling, heartbeat telemetry, startup self-checks, and centralized run persistence.
- Expanded planner creativity: archetype-driven vectors (payments/identity/api/edge), WebSocket and Mobile API parity lanes, plus business-logic/idempotency/tampering matrices.
- Added end-to-end `force_new_blueprint` mode (CLI + API + UI toggle), enabling full blueprint regeneration even when the scope hash matches.
- Separated Findings from the runtime log tail: added a new `api/findings/logs` endpoint with a host-centric, human-friendly vulnerability-signal feed.
- Fixed Findings refresh and data sources: restored the refresh loop, corrected API wiring, improved low/mid signal handling, and restored `FINDINGS_BASELINE_PATH`.
- Added a detector for signals in responses captured with `-o output_file` (signal pack 1-10): error traces, secret leaks, authz hints, business-logic anomalies, WAF/CDN fingerprints, and redirect/content-type/header/debug markers.
- Improved operator messages: human-friendly translation of `__RC_METRICS__` for success/failure cases (including `code=000`, `403`, `4xx/5xx`, `200/3xx` with IP/latency/size/redirects).
- Fixed Campaign Setup UI stability: durable credentials-policy toggles (immediate save, per-campaign local cache, correct selected-campaign-key persistence, and removed forced `credentials_required=ON`).
- Expanded flow monitoring and auditing: live throughput/heartbeat/queue signals plus iterative modernization recommendations.

## 0.7.5 / 2026-02-28
- Dashboard/log rendering: standardized operator messages (`Status - reason`), removed duplicate patterns like `Failed - Failed`, restored the `reason_code` badge, and added hierarchical keyword coloring in `DETAILS`.
- UI Agentic Roles: rebuilt the status badge model around work states (planning/gating/running/paused/off/idle), synchronized badge and LED colors, and corrected state mapping (`off/disabled` => red, `idle` => gray).
- Pipeline monitoring: fixed resets after `STOP` (progress/time elapsed dropping to zero), fixed the `Time elapsed` timer after `PAUSE/RESUME` (preserving `session_started_at`), and trimmed `Current target` to 20 characters.
- Runtime log UX: merged `REASON+MESSAGE+CMD` into a single `DETAILS` column, enabled dynamic rendering without empty fields, restored badge styles for `deterministic_scope_gate`/`engine_success`, and improved spacing/cell centering.
- Execution diagnostics: globally humanized `curl` codes (`rc=6/7/22/28/35/47/56`) and HTTP metrics (`code=403/4xx/5xx`) into operator-friendly descriptions.
- Transport telemetry: added `curl --write-out` metrics (`http_code`, `remote_ip`, `dns/connect/tls/ttfb/total`, `size`, `redirects`) for every probe.
- Agent stability: fixed the LIGHT path for non-JSON output (compact prompt + fallback to the ANALYSIS contract), reducing pipeline degradation from fallback logic.
- Flow optimization: aggregated `precheck` spam into `precheck_dedup_summary`, added a DNS gate before dispatch (`vector_skip_dns`), and introduced plan-time DNS filtering during runtime-plan generation.
- Runtime plan quality: rebuilt the generator to produce less predictable multi-vector tasks and added target-aware prioritization (api/sandbox/developer/high-value first).
- Churn reduction: follow-ups now happen only on strong security signals, with per-target TTL, lower `max_followups_per_target`, higher `contextual_reconsult` thresholds, and stricter `promising` heuristics.
- Policy/aggression: aligned the constraint hierarchy (including support for `mandatory aggression constraint of 1`) and set safer caps/aggression defaults in the generator.
- Campaign start robustness: fixed `START` when `plan_not_found` occurs (automatic runtime-plan regeneration), plus validation and campaign-state handling stabilizations.
- Slider tuning: lowered overly high maxima, added backend clamps, and synchronized UI bounds (`/api/slider-bounds`) for system/campaign panel consistency.

## 0.7.4 / 2026-02-27
- Fixed delayed campaign starts: removed heavy `planner_preflight` from the `START` path and introduced fast-start on an existing, validated runtime plan.
- Added race-condition protection for `START` (lock + auto-heal for stale locks), button debouncing, and protection against launching parallel workers multiple times.
- Expanded observability: fuller dashboard action logs, `CFG/SETTINGS` status, a dedicated `CMD:` line, and full-length log entries (without backend truncation at 240 characters).
- Fixed critical runtime/telemetry bugs: `current_index` NameError, broken indentation in the `curated_plan` loop, and invalid `subprocess.run(..., retries=...)` usage in the pipeline logger.
- Improved error diagnostics: replaced `No output` with concrete causes (policy block/timeout/status/reason/stderr), plus an explanation for `curl -o` (no stdout is expected).
- Fixed `ExecutionEngine`: correct host extraction (ignoring header/email tokens) and automatic creation of output directories for `-o/--output`.
- Improved PLANER and quick-setup: filtered Out-of-Scope values during scope parsing, fixed plan validation against the selected blueprint, and removed the `unique_part` regression.
- Changed the campaign-name format to a short, direct form: `CLIENT-V{version}-{HASH8}`.
- Added `Out-of-scope aggression cap` and `Allowed aggression constraint` sliders in Owner Actions, plus a `DELETE SELECTED CAMPAIGN` button (cleanup of the selected campaign and its artifacts).
- Added a `Plan entries` metric in Campaign Setup, removed the `Parallel Level` slider, and improved `Quick Prepare + Activate` feedback.
- Added runtime-log pagination in Findings (20 entries/page) and a severity-only filter (low/mid/high/critical).

---

Each larger change or milestone receives a version according to its scope. Further history will be appended in future releases or manual owner decisions.

## 0.7.3 / 2026-02-27
- Fixed `Credentials Policy` behavior (more stable toggles + consistent backend validation).
- Added global log-clearing actions on log-based views (Pipeline Monitoring / Findings / Owner Actions).
- Completed the runtime flow for `retry_policy`, `time_budget_min`, and `parallelism` (UI -> API -> env -> `auto_campaign`).
- Refined runtime `retry_policy` handling (strict/balanced/aggressive) and dedup semantics for `retry_*`.
- Limited Findings to the selected campaign; when nothing is selected, values display as `-`.
- Expanded `Recent Classifications` with per-campaign progress and ETA (`steps left`).
- Delivered a UX fix series covering slider/toggle consistency, tooltip coverage, Font Awesome icons, log rendering, and empty-state views.

## 0.7.2 / 2026-02-27
- Standardized section headers across all subpages into the "Font Awesome + name" format (consistent with Operation Snapshot).
- Increased the global scale of Font Awesome icons in menus and section headers.
- Pipeline monitoring: enlarged Start/Pause/Stop action-tile icons and improved pagination visibility (10/30/50).
- Agentic roles: made the main icons even larger, more centralized, and higher contrast.

## 0.7.1 / 2026-02-27
- Pipeline monitoring: standardized action controls as equivalent action tiles (large FA icons + label), with dynamic START/RESUME depending on pause state.
- Added log pagination in pipeline monitoring with per-page options 10/30/50.
- Agentic roles: increased the visual dominance of FA icons and improved status iconography and colored LEDs.
- Findings/Campaign Setup/System Settings/Owner Actions: expanded FA iconography and improved block readability plus input/select styling.
- Restored autosave-first behavior in System Settings (without manual Save), keeping reset/revert.
- Owner Actions: a single wide override toggle with warning styling and blinking while override is active.

## 0.7.0 / 2026-02-27
- UX pass 3: refined Pipeline Monitoring (status badges, equal-weight start/pause/stop action tiles, FA icons, improved readability).
- Agentic Roles: restored/improved state LEDs, status iconography, stronger contrast, and ORCHESTRATOR priority.
- Findings: added FA icons to sections and rows, improved Recent Classifications aesthetics, and stabilized runtime event-log loading and fallbacks.
- Campaign Setup: restored Quick Prepare + Activate, added Blueprint/Runtime Plan preview plus Show credentials, and improved control grouping and styling.
- Owner Actions: one wide override-toggle button (with blinking warning state) and a fixed-width mode indicator (RESEARCH/OVERRIDE).
- System Settings: removed manual Save, restored autosave, and improved tooltip/component/icon consistency.

## 0.6.9 / 2026-02-27
- UX pass 2: restored autosave in settings (removed the Save button) and left only reset/revert actions.
- Fixed tooltips after the redesign: one consistent custom tooltip layer (without double native bubbles), expanded descriptions, and wiring into Campaign Setup and Owner Actions.
- Improved component color readability (cards, key-value rows, toggles, role cards, log rows).
- Pipeline monitoring: added status LEDs and clearer states in Agentic Roles tiles.
- Findings: improved resilience of log-tail rendering/loading (error fallbacks, more stable refresh).

## 0.6.8 / 2026-02-27
- Completed a full IA/UX redesign of the dashboard while preserving RAVENCLAW branding and fixed top navigation.
- Rebuilt Pipeline Monitoring into a mission-control layout (snapshot, campaign context, live pipeline state, runtime health, simplified logs) with ORCHESTRATOR prioritized.
- Expanded Findings into an operational view (overview, severity/category distribution, workbench table, detail panel, distinction between raw signals and promoted findings).
- Reorganized Campaign Setup into logical blocks (prepared/activation, planner input/workflow, readiness/validation, limits/boundaries, credentials policy, checklist + preview).
- Grouped System Settings into sections A/B/C/D/E, added Global Safeguards, a save/reset/revert action bar, an unsaved indicator, and profile/last-applied/checksum metadata.
- Rebuilt Owner Actions into a privileged zone (override banner, campaign controls, privileged controls, aggression control, audit trail).
- Standardized the component design system (cards, key-value rows, toggles, sliders, badges, spacing/rhythm) while keeping the dark mission-control feel.

## 0.6.7 / 2026-02-27
- Installed tooling packages for WiFi/LAN/infrastructure testing (including aircrack-ng, hcxdumptool/hcxtools, wifite, hydra, masscan, amass, subfinder, and other dependencies).
- Hardened the executor runtime against missing `/usr/sbin` in PATH (added `/usr/sbin:/sbin` to the command-execution environment), fixing detection of some network tools.
- Confirmed preflight + verifier activation after the system changes.

## 0.6.6 / 2026-02-27
- Standardized dashboard versioning: the `vX.Y.Z` badge is now sourced dynamically from the highest semver in CHANGELOG (`/api/version`, context processor).
- Expanded governance preflight with a changelog guard (forcing updates after a threshold number of key commits).
- Added a runtime learning mechanism (`engine/learning_store.py`): remembers effectiveness of attack families and hosts, then feeds a `learning summary` into the BRAIN prompt.
- Added system flags `experimental_payloads` and `enable_tooltips` (feature flags + dashboard controls + verifier).
- `run_pipeline.py`: experimental payloads mode is enabled conditionally only on high-signal recent context (without constantly burdening PLANER).
- `logdash`: added `api/findings-table` with demo-entry controls and improved findings-preview presentation.
- `api/slider-bounds`: budget-aware higher slider limits for power users (including follow-ups >= 10).
- Expanded the whitelist with WiFi/LAN/infrastructure commands (tier1/2/3) for broader utility.

## 0.6.5 / 2026-02-27
- Fixed `auth-harness/scripts/run_targets.py` (unterminated string literal in the truncation payload).
- Performed legacy cleanup: moved unused scripts into `engine/legacy/` and archived the obsolete monitor/systemd unit (`raven-claw-monitor.service`).
- Centralized runtime paths (`engine/paths.py`) and data contracts (`engine/contracts.py`).
- Added `policy_gateway.py` (standardized policy/scope/credentials gating) plus adaptive high-signal gating for ANALYSIS/LIGHT.
- Expanded campaign deduplication: key is now `host + attack_family + payload_signature` (without blocking different payloads from the same family).
- Dashboard: modernized ON/OFF switch UI, added pipeline-config persistence through the API, scope-file preview, and dynamic sliders with scale/budget-aware limits.
- Findings: added a tabular findings view (consistent style) and an `api/findings-table` endpoint with optional demo entries.
- Introduced governance feature flags: `engine/feature_flags.py`, a flag manifest, and a UI consistency checker (`verify_feature_flags.py`).
- Added deploy preflight `engine/preflight_checks.sh` (flag consistency + changelog freshness + py_compile).
- Added dynamic dashboard versioning from `CHANGELOG.md` (`app_version` badge + `/api/version`).

## 0.6.4 / 2026-02-25
- Removed the `Override` button from the main dashboard (override control now lives only in `Owner actions`).
- Improved `Owner Override` status presentation in `Active Campaign` (correct mapping + default OFF when no state file exists).
- Revised agent LEDs/statuses: a consistent state map (`active/warn/error/idle`) with green/yellow/red/gray colors.
- Added Font Awesome icons for agent statuses (`agentic roles`) and colored status labels according to module state.

## 0.6.3 / 2026-02-25
- Added the missing dashboard menu subpages: `/findings`, `/system-settings`, `/owner-actions`.
- Unified navigation 1:1 across all pages (Pipeline monitoring, Findings, Campaign Setup, System settings, Owner actions, Research mode).
- Findings: added a telemetry view for confidence/CVSS + campaign snapshot.
- System settings: added a system-state toggle/preview panel (without exposing low-level details).
- Owner actions: added quick privileged actions (owner override, pause/resume/stop) in a consistent UI.

## 0.6.2 / 2026-02-25
- Added full credential policy support to PLANER and the blueprint: the parser detects auth signals (`credentials_policy`), and the blueprint schema validates the new field.
- Extended the hybrid LLM interpreter with `credentials_policy` (required/allowed auth types + owner approval) and reconciliation with the deterministic parser.
- Added per-campaign credential configuration in the dashboard (`/campaign-setup`): `credentials_required`, allowed types (`auth/cookie/basic`), and `credentials_owner_approved`.
- The runtime-plan generator now writes `owner_approved_auth` onto vectors according to the campaign credential policy.
- `run_pipeline.py` policy gating now enforces the credential policy (blocking auth/cookie/basic outside policy and without owner approval).

## 0.6.1 / 2026-02-25
- Integrated the runtime BRAIN with the hybrid PLANER: `run_pipeline.py` now loads `planner_hints` from the latest blueprint and passes them into the BRAIN prompt as priority context (vectors/ambiguities/conflicts/aggression profile).
- Extended pipeline output with `planner_hints` for full runtime-decision auditability.
- Fixed a logdash crash after aggression-policy integration: `engine/aggression_policy.py` now works even without `PyYAML` (fallback parser), removing the dashboard-venv service restart loop.
- Minor UX cleanup: removed plan validation from the main dashboard and closed the full setup flow on `/campaign-setup`.

## 0.6.0 / 2026-02-25
- Added `Quick` mode in Campaign Setup: a single `Quick Prepare + Activate` button performs the sequence PLANER -> approve blueprint -> generate runtime plan -> validate -> activate.
- Kept `Advanced` mode (manual step-by-step buttons) for full operator control.
- Added a `Doc Viewer` under campaign settings (log-panel style): preview buttons for `Blueprint JSON` and `Runtime Plan JSON` with panel rendering.
- Added API endpoints: `/api/campaign/setup/quick`, `/api/planner/blueprint-view`, `/api/planner/runtime-plan-view`.

## 0.5.9 / 2026-02-25
- Added a hybrid-interpretation quality view in `/campaign-setup`: `LLM used`, `LLM confidence`, `Interpretation conflicts`, `Ambiguities`.
- `api/planner-info` now returns `planner_hints` metadata from the blueprint (llm_used/confidence/conflicts/ambiguities/suggested vectors).
- Removed the `Validate plan` button from the main dashboard (`/`), leaving validation only in campaign settings (`/campaign-setup`).

## 0.5.8 / 2026-02-25
- Introduced the hybrid PLANER (stage 1+2): added `engine/planer/llm_interpreter.py` with one-shot LLM scope interpretation (strict JSON contract) and a safe fallback to the deterministic parser.
- Added an LLM + deterministic reconciliation layer (`reconcile_with_deterministic`) with conflict control (`llm_added_domains`, confidence, ambiguities, suggested vectors).
- PLANER now stores LLM interpretation metadata in `operator_input.llm_interpretation` and propagates it into the blueprint.
- Extended the blueprint with `planner_hints` (suggested vectors, ambiguities, llm_used/confidence/conflicts); the schema now requires `planner_hints`.
- The aggression profile is now combined from the deterministic baseline plus LLM guidance (clamped to policy).

## 0.5.7 / 2026-02-25
- Added a manual aggression slider in `/campaign-setup` (save/clear override per selected campaign).
- Added an owner gate for aggression outside the recommended range (`owner_approval_required_for_aggression_out_of_recommended_range`).
- Extended `campaign settings` with `aggression_override` and integrated override handling into runtime-plan generation.
- Dashboard API (`/api/campaign-info`) now returns `aggression_effective` and the recommended range for the active campaign.
- Moved campaign settings (Max runs, Target limit, Runtime plan status, Validation notes) onto `/campaign-setup`; removed their visible section from the main dashboard.
- Restored the `/campaign-setup` menu 1:1 with the main dashboard (Pipeline, Findings, Campaign Setup, System settings, Owner actions, Research mode).

## 0.5.6 / 2026-02-25
- Added a shared aggression-policy module `engine/aggression_policy.py` (single source of truth: min/max/default + clamp).
- Migrated `policy.yaml` to the full aggression scale (`max_level: 10`) and wired aggression clamping into `run_pipeline.py`.
- Integrated aggression with PLANER: the blueprint now includes `aggression_profile` (recommended min/default/max + rationale), validated by schema.
- Runtime-plan generation (`/api/planner/generate-runtime-plan`) now uses `aggression_profile` instead of fixed 4/5 values.
- Auto-campaign clamps aggression from plans and follow-ups to policy, eliminating drift between planning and execution.

## 0.5.5 / 2026-02-25
- Performed a "fresh test reset": archived current campaign artifacts into `reports/archive/reset-20260225T153912Z` and cleared runtime/historical data (state, registry, dashboard logs, context).
- Shortened and clarified campaign names in the dashboard (abbreviations/acronyms like BB/CMP/PRG).
- In Active Campaign, the campaign name is now taken from the selected campaign; removed the visible `Selected campaign` row.
- Removed the Orchestrator ON/OFF button from the main dashboard.
- Added the `/campaign-setup` subpage (same style) for campaign selection and planning/activation operations.
- Added metrics/status endpoints: `/api/metrics` (avg confidence + highest CVSS) and `/api/agents-status` (module statuses).
- Added `logdash/agents_config.json` for configurable agent names/models used by the UI.

## 0.5.4 / 2026-02-25
- Rebuilt the logdash dashboard into a new "agentic security panel" layout based on the provided HTML template.
- Wired the existing APIs (`/api/campaign-info`, `/api/planner-*`, `/api/logs`, `/api/campaign/control`) into the new UI without losing campaign control.
- Added clear alert/log coloring: green (OK), yellow (warning/in-progress), red (error/blocked).
- Preserved the full operator workflow: start/pause/resume/stop, owner override, orchestrator toggle, planner run/approve, runtime-plan validate/generate, activate campaign, save settings, and log pagination.

## 0.5.3 / 2026-02-25
- Added an automatic campaign fixer (`engine/fix_campaign.py`) to repair scope issues (including concatenated domains like `...comauth-...`).
- Applied autofix to the active `campaign.md` (creating backup `campaign.md.autofix.bak`), splitting the invalid entry into correct domains.
- Tightened detection of domain-concatenation errors in the campaign validator (fewer false positives).

## 0.5.2 / 2026-02-25
- Added a campaign validator (`engine/campaign_validator.py`) and a hard block on pipeline/auto-campaign start when `campaign.md` is invalid.
- Added a status-normalization module (`engine/status_utils.py`) and wired it into `run_pipeline.py` and `auto_campaign.py` (more consistent statuses and auditor decisions).
- Added `correlation_id` and standardized status fields in `run_pipeline.py` output.
- Added a compatibility wrapper `engine/pipeline.py` pointing to the canonical entrypoint (`engine/run_pipeline.py`) for legacy references.
- Added campaign-validator tests (`engine/planer/tests/test_campaign_validator.py`).

## 0.5.1 / 2026-02-24 (late)
- Rebuilt the dashboard into a 3-column layout (Campaign Details / PLANER / States) with retro status coloring and stable 2s auto-refresh.
- Fixed UI state resets: Owner Override, selected-campaign dropdown, and scope input are now persisted on the backend.
- Added a blueprint workflow: `Approve blueprint`, `Generate runtime plan from blueprint`, `Activate selected campaign` (automatic replacement of active `campaign.md` with `.bak` backup).
- Added a runtime-plan validator (endpoint + UI): detects wildcards, unparsable hosts, out-of-scope hosts, and empty plans.
- Campaign start is blocked on invalid runtime plans and reports validation/regeneration details.
- The runtime-plan generator now filters wildcard and out-of-scope hosts and reports `skipped_out_of_scope`.
- Added per-session progress (`session_executed/session_max_runs`) plus campaign-length metrics: `prepared_attacks (runtime)` + `planner_scope_targets`.
- Fixed campaign stop (idempotent) and added service logs for start/pause/resume/stop into logdash.
- Auto-campaign: owner override now works dynamically during an active campaign (reading runtime state on subsequent iterations).
- Auto-campaign: added controlled follow-up requeue for promising findings (per-target limits, dedup, `retry_1` log).
- Planer: campaign names are generated dynamically from scope text (`CLIENT/PROGRAM + VERSION + UNIQUE + HASH`).
- Added a terminal monitor `ravenclaw-monitor.sh` with `--once`, `--json`, threshold alerts, and event-bus queue source support + logs.db fallback.
- Added `README.md` as a research manifesto describing the philosophy and spirit of RAVEN-CLAW.

## 0.5.0 / 2026-02-24
- Introduced the deterministic PLANER module: immutable blueprint generation (JSON/YAML), interpretation log (source/rule/decision/confidence/trace_id), 3 strategy variants, and a campaign-version registry.
- Added PLANER tests (determinism, schema conformance, interpretation logging, multi-variant, existing-plan reuse) plus deployment documentation.
- Added the `planer` agent and initially configured the `chutes/Qwen/Qwen3.5-397B-A17B-TEE` model.
- Added the `orchestrator` agent and initially configured the `github-copilot/gpt-5.1-mini` model plus SOUL/IDENTITY/USER profiles for the supervisory FSM role.
- Logdash dashboard: added campaign controls (start/pause-resume/stop), owner override ON/OFF toggle, PLANER panel, PLANER execution from UI, and pipeline-module statuses.
- Logdash dashboard: added Orchestrator ON/OFF toggle, PLANER preflight on campaign start (when Orchestrator=ON), and scope TXT integration.
- Logdash dashboard: added editable campaign parameters `max_runs` and `target_load_limit` with persistence and env propagation (`AUTO_MAX_RUNS`, `AUTO_TARGET_LOAD_LIMIT`).
- Logdash dashboard: improved log ordering (sort by `id DESC`), added a dropdown of prepared PLANER campaigns, and cleaned up layout/retro styling.
- Pipeline: fixed owner override (covers reject/deny/blocked), LIGHT fallback on contract failure, and timezone-safe UTC timestamps.
- Completely removed the legacy "auxiliary orchestrator" and related artifacts/references (code and documentation consistency).

## 0.4.5 / 2026-02-23+
- Audit integrations, durable memory flush, full logging of maintenance actions, and critical-context tracing.
- Pending: an expanded changelog with future milestones and versioning across code/agents.

## 0.4.0 / 2026-02-23
- Automatic logging of pipeline start/stop/shutdown/crash statuses into the logdash dashboard (full-width column, `service` type).
- Hardening: isolated systemd, file-ownership control, automatic repair, and log cleanup.
- Compatibility with the `.stop` file for graceful pipeline shutdown (exit 10), plus automatic watchdog stop after manual termination.
- Full coverage of SOUL.md operational policy and the main owner-in-the-loop constraints.

## 0.3.0 / 2026-02-22
- Expanded logdash dashboard: separate logs.db database, REST/Flask frontend (port 9091), pagination, filtering, and wide `service` entries.
- Deployed logdash as a systemd user-service, with the first README-service.md/logdash docs.
- Automatic deduplication of targets/tasks via `engine/target_state.py`, with support for resuming interrupted sessions.
- Advanced parsing and output to JSON and Markdown reports.
- Integrated archival of reports and memory/accepted/rejected/summaries.db.

## 0.2.0 / 2026-02-21
- Integrated multi-agent orchestration: BRAIN, AUDITOR, ENGINE, ANALYSIS, LIGHT.
- Added role separation and workspace separation.
- Implemented SOUL.md policy, with message tagging and enforced agent ordering.
- Added durable memory (MEMORY.md + memory/yyyy-mm-dd.md), with auto-append.
- Added baseline `campaign.md`, `policy.yaml`, and `whitelist.yaml`.
- Introduced early vector deduplication and completed-task checkpoints.

## 0.1.0 / 2026-02-20
- First working prototype of the RAVENCLAW system, single-agent (BRAIN/ENGINE) with a simple scope policy.
- Manual pipeline execution, logging only to local `.log` files.
