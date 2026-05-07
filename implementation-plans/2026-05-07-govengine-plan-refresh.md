# GovEngine Plan Refresh — Stage 0/1 Only

Date: 2026-05-07
Status: proposed correction checkpoint; do not continue into extraction until operator approval.
Base: Ravenclaw public `main` at `7519b6a`.
Related report: `reports/govengine-plan-validation-2026-05-07.md`.

## Purpose

Refresh the GovEngine extraction plan after SCLite v0.2 lifecycle hardening and Ravenclaw's runtime ExecutionTicket gate.

This is not a broad extraction wave. It defines the safe first implementation boundary.

## Updated premise

SCLite is now the lifecycle/integrity source of truth:

```text
intent_contract -> policy_decision -> execution_contract -> execution_ticket -> execution_receipt -> evidence_contract -> artifact_chain_manifest
```

Ravenclaw now both emits this chain and uses an ExecutionTicket gate in the local approved-spec runtime path. Therefore GovEngine must treat lifecycle/ticket semantics as core governed-execution contracts, not only docs/demo artifacts.

## Stage 0 — Validation and ownership correction

Tasks:

1. Keep `reports/govengine-plan-validation-2026-05-07.md` as the current validation addendum.
2. Record ownership decisions:
   - SCLite owns schemas/hash/semantic lifecycle verification.
   - GovEngine should own reusable governed-execution lifecycle mapping and ticket gate semantics.
   - Ravenclaw owns branded profile/defaults/demo/public snapshot/Logdash.
3. Before moving executor/pipeline code, fix or explicitly resolve the ticket approval status mismatch:
   - SCLite/Ravenclaw adapter emits `approved_for_dry_run` for approved dry-run tickets.
   - Current executor gate accepts only `approve`.
4. Add focused coverage proving adapter-produced tickets are accepted by the execution gate.
5. Update validation gates to include `sclite verify-lifecycle`.

Gate:

- no code movement claimed without ownership decision;
- current base and SCLite pin cited;
- ticket status compatibility either fixed or explicitly blocked;
- local validation receipt remains green.

## Stage 1 — Context and ports before movement

Goal: make a minimal package-in-place GovEngine seam without moving broad runtime logic.

Add:

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
- `GovPolicyConfig`
- `GovToolRegistryProvider`
- `GovSCLiteLifecycleVerifier`

First routing targets:

1. SCLite/root/profile handling in `engine/security_contract_layer.py` and `engine/scl_ravenclaw_adapter.py`.
2. Temporary snapshot/public validation path handling in `engine/scl_validation_runner.py`.
3. `engine/pipeline_context.py` path/config handling.

Explicit non-goals for Stage 1:

- do not move `engine/executor.py` wholesale;
- do not move policy modules wholesale;
- do not move Logdash;
- do not create MCP/OpenClaw/A2A adapters;
- do not create the external GovEngine repo yet;
- do not duplicate Ravenclaw logic into a second implementation.

## Required validation for Stage 1 implementation

```bash
python scripts/run_security_contract_validation.py --include-pytest --format markdown
for slice in contracts_policy auto_campaign runtime_core runtime_runner logdash misc_public; do \
  PYTHONDONTWRITEBYTECODE=1 python scripts/run_pytest_slice.py "$slice"; \
done
sclite verify-lifecycle examples/contract-lifecycle-v0.2/artifact_chain_manifest.json
```

Focused tests to add:

- import `govengine` from editable install or direct checkout;
- `GovEngineContext` can be constructed without `RAVENCLAW_WORKSPACE`;
- Ravenclaw compatibility profile maps existing workspace paths explicitly;
- adapter-generated ExecutionTicket passes the runtime execution-ticket gate after status normalization.

## Approval checkpoint

Stop here for operator review before implementing Stage 1.

If approved, next wave should be:

1. fix/cover ticket status compatibility;
2. add minimal `govengine/` scaffolding;
3. route one SCLite/path seam through context;
4. run full validation;
5. stop again before moving policy/executor modules.
