# GovEngine Plan Validation — 2026-05-07

Status: validation/addendum only; no extraction code movement.
Branch: `ravenclaw/govengine-plan-refresh` local worktree.
Validated public base: Ravenclaw `main` at `7519b6a docs: document lifecycle semantic verification`.
SCLite code pin in Ravenclaw: `43dae49b44602da76611fb42cd0b10aac3b3ae3f` (`feat: harden SCLite v0.2 lifecycle verification`).
Latest SCLite docs main observed: `06d1076 docs: align integration guide with lifecycle verifier`.

## Actions status

Observed before validation:

- SCLite `main` `06d1076`: GitHub Actions `CI` passed.
- Ravenclaw `main` `7519b6a`: GitHub Actions `pytest` passed.

## Current-state deltas since the original 2026-05-06 plan

The original plan remains directionally correct, but it was written before three important changes landed:

1. SCLite v0.2 lifecycle verification now checks semantic bindings, not only hash-chain integrity:
   - canonical lifecycle role order;
   - policy -> intent;
   - execution contract -> intent/policy;
   - ticket -> execution contract;
   - receipt -> ticket;
   - evidence -> receipt;
   - manifest path containment.
2. Ravenclaw now has a runtime execution-ticket gate on the local approved-spec path.
3. Ravenclaw docs and validation surfaces now describe `verify-lifecycle` and semantic lifecycle verification.

Static scan of current public base (`engine/`, `logdash/`, `scripts/`, `bin/`):

- files scanned: 359
- source/script lines: 57,287
- entrypoint-like files: 38
- files with direct root/path assumptions: 195
- files with direct file/subprocess/state I/O signatures: 93

The coupling risk is therefore not smaller after SCLite v0.2; it is more explicit. That supports the plan's Stage 1 emphasis on context/ports before movement.

## Verdict on original plan

Recommended: keep the staged direction, but tighten Stage 0/1 before any extraction.

What still holds:

- Dependency direction must remain `Ravenclaw -> GovEngine -> SCLite`.
- LLM/provider/session/persona integration stays in Ravenclaw.
- Logdash stays in Ravenclaw.
- Protocol/carrier adapters are not the next milestone.
- Do not copy engine code into a second repo while leaving live Ravenclaw logic behind.
- First implementation wave should be package-in-place, not an external repo split.

What must change:

- GovEngine's SCLite seam must be v0.2 lifecycle-first, not legacy v0.1 proof-trace-first.
- ExecutionTicket semantics are now runtime-critical and must be treated as a core GovEngine contract, not only a public proof artifact.
- Stage 1 must include an explicit ticket/status compatibility review before moving executor or pipeline code.
- Plan gates must include `sclite verify-lifecycle` / semantic verification, not only `validate-chain` or older Security Contract receipt language.
- The original audit baseline `1651b74` is stale; any movement should cite current `7519b6a` or newer.

## Important pre-extraction risk found

There is a likely status-language mismatch that should be handled before or during the first code movement wave:

- SCLite v0.2 schema/fixture uses approval statuses such as `approved_for_dry_run`.
- Ravenclaw adapter currently maps an approved dry-run ticket to `approved_for_dry_run`.
- `engine/executor.py` local execution-ticket gate currently accepts only `approval.status == "approve"`.
- Existing tests cover the executor gate with a synthetic `approve` ticket and cover lifecycle generation, but they do not appear to assert that the adapter-produced ticket is accepted by the local execution gate.

This is not a GovEngine extraction blocker by itself, but it is a Stage 0/1 correction item because GovEngine should not freeze a mismatched ticket semantic into its public API.

Recommended correction before moving executor/pipeline logic:

- Normalize ticket approval semantics in one place.
- Accept schema-valid positive statuses (`approved_for_dry_run`, and possibly `approved`) in the execution-ticket gate.
- Add a focused test proving `build_lifecycle_artifacts_v02(...)` output is accepted by `ExecutionEngine.execute_approved_spec(..., require_execution_ticket=True)`.

## Corrected Stage 0 scope

Stage 0 should now produce/update these ownership decisions:

| Area | Ownership decision |
| --- | --- |
| SCLite v0.2 artifact schemas/verification | SCLite owns source of truth; GovEngine consumes dependency. |
| Generic lifecycle mapping from governed execution data to SCLite v0.2 | GovEngine target ownership, behind `govengine.sclite_adapter`. |
| Ravenclaw-branded lifecycle labels/defaults/demo/public bundle | Ravenclaw owns profile/adapters. |
| ExecutionTicket runtime gate semantics | GovEngine target ownership; Ravenclaw wrapper must preserve behavior. |
| Public snapshot/demo validation orchestration | Ravenclaw owns; GovEngine may expose reusable validators only if generic. |
| Logdash | Ravenclaw owns; consumes GovEngine APIs later. |

Stage 0 gate additions:

- cite current `main` baseline;
- verify SCLite pin and lifecycle verifier behavior;
- add a test/finding for adapter-ticket -> executor-gate compatibility before moving executor;
- update validation gate list to include semantic lifecycle verification.

## Corrected Stage 1 scope

Stage 1 remains "context and ports before movement", but should be narrower and more explicit:

Add package-in-place scaffolding only:

```text
govengine/
  __init__.py
  context.py
  paths.py
  state_store.py
  execution_backend.py
  roles.py
  sclite_contracts.py
```

Initial interfaces:

- `GovEngineContext`
- `GovEnginePaths`
- `GovStateStore`
- `GovExecutionBackend` / `CommandRunner`
- `GovRoleAdapters`
- `GovPolicyConfig` / config provider
- `GovToolRegistryProvider`
- `GovSCLiteLifecycleVerifier` or equivalent protocol wrapper around SCLite verification results

First modules to route through context should be revised:

1. `engine/security_contract_layer.py` and `engine/scl_ravenclaw_adapter.py` root/profile handling, but without moving public-demo orchestration.
2. `engine/scl_validation_runner.py` path handling for temporary snapshot/public validation execution.
3. `engine/pipeline_context.py` path/config handling, before `runtime_plan_service.py`, because the pipeline now prepares execution tickets before local execution.

Do **not** move `engine/executor.py` in Stage 1. First fix/cover the ticket semantics mismatch and make context/ports importable.

Stage 1 validation gate:

```bash
python scripts/run_security_contract_validation.py --include-pytest --format markdown
for slice in contracts_policy auto_campaign runtime_core runtime_runner logdash misc_public; do \
  PYTHONDONTWRITEBYTECODE=1 python scripts/run_pytest_slice.py "$slice"; \
done
sclite verify-lifecycle examples/contract-lifecycle-v0.2/artifact_chain_manifest.json
```

Also add focused tests for:

- `import govengine` from editable install or direct repo checkout;
- GovEngine context does not require `RAVENCLAW_WORKSPACE`;
- adapter-produced execution ticket is accepted by the execution-ticket gate after semantic normalization.

## Stop point recommendation

Do not start broad extraction yet.

Recommended next operator-approved wave:

1. Create/keep a GovEngine branch from current public `main`.
2. Patch the ticket status/gate compatibility issue with focused tests.
3. Add the minimal `govengine/` context+ports package-in-place scaffolding.
4. Route only SCLite/root validation seam through explicit context.
5. Run full validation gates.
6. Stop and review before moving policy/executor modules.
