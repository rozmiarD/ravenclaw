# GovEngine Wrapper Audit

Ravenclaw consumes GovEngine as the package `govengine>=0.11.0a0,<0.12` alongside `sclite-core>=0.8.0a0,<0.9`.
This file records which `engine/` modules are compatibility wrappers over
GovEngine and which host-side seams remain Ravenclaw-owned.

## Classification

| Module | Upstream surface | Status | Rationale |
| --- | --- | --- | --- |
| `engine/action_schema.py` | `govengine.action_schema` | removed; contained consumption | Active runtime callers consume this optional helper through `engine/govengine_security_helpers.py`; focused tests may import upstream directly. |
| `engine/action_validators.py` | `govengine.action_validators` | removed; contained consumption | Active runtime callers consume this optional helper through the checked Ravenclaw seam; focused tests may import upstream directly. |
| `engine/action_compiler.py` | `govengine.action_compiler` | removed; contained consumption | Active runtime callers consume this optional helper through the checked Ravenclaw seam; focused tests may import upstream directly. |
| `engine/capability_recipes.py` | `govengine.capability_recipes` | removed; contained consumption | Active runtime callers consume this optional helper through the checked Ravenclaw seam; focused tests may import upstream directly. |
| `engine/tool_registry.py` | `govengine.tool_registry` | removed; contained consumption | Active runtime/Logdash callers consume this optional stateful helper through the checked Ravenclaw seam; ownership remains a later migration decision. |
| `engine/semantic_loss_policy.py` | `govengine.semantic_loss_policy` | removed; contained consumption | Active runtime callers consume this optional helper through the checked Ravenclaw seam; focused tests may import upstream directly. |
| `engine/policy_core.py` | `govengine.policy.core` | removed; contained consumption | Active runtime callers consume this optional policy helper through the checked Ravenclaw seam; ownership remains a later migration decision. |
| `engine/policy_gateway.py` | `govengine.policy.gateway` | removed; contained consumption | Active runtime callers consume this optional policy helper through the checked Ravenclaw seam; ownership remains a later migration decision. |
| `engine/execution_contracts.py` | `govengine.contracts.execution` | removed | Ravenclaw active callers and tests import execution contract helpers from GovEngine directly. |
| `engine/signal_contract.py` | `govengine.contracts.signal` | removed; contained consumption | Active runtime callers consume this optional contract helper through the checked Ravenclaw seam; whether it should become neutral is not decided by this routing change. |
| `engine/analysis_contract.py` | `govengine.contracts.analysis` | removed; contained consumption | Active runtime callers consume this optional contract helper through the checked Ravenclaw seam; whether it should become neutral is not decided by this routing change. |
| `engine/evidence_policy.py` | `govengine.contracts.evidence_policy` | removed; contained consumption | Active runtime callers consume this optional contract helper through the checked Ravenclaw seam; whether it should become neutral is not decided by this routing change. |
| `engine/scl_ravenclaw_adapter.py` | `govengine.sclite_adapter` | removed | Ravenclaw uses `engine/security_contract_layer.py` as the host-owned current lifecycle projection over GovEngine/SCLite primitives; active runtime and demo callers do not publish directly through the neutral-kernel dependency. |
| `engine/govengine_boundary_profile.py` | `govengine.kernel_boundary_report` | keep required host check; no unavailable fallback | Ravenclaw validates the GovEngine boundary report and profile non-claims during public install validation. |
| `engine/govengine_state_control_projection.py` | `govengine.runtime_shell` | keep host adapter | Ravenclaw owns projection from Logdash/runtime state into GovEngine `GovControlAction`, `GovQueueSnapshot`, and `GovRuntimeSnapshot` shapes while keeping UI, storage, process control, and campaign semantics host-owned. |
| `engine/govengine_planning_projection.py` | `govengine.planning` | keep host adapter | Ravenclaw owns projection from planner/runtime task semantics into redacted GovEngine task and plan-intent contracts while keeping security planning semantics host-owned. |
| `engine/govengine_admission_projection.py` | `govengine.admission` | keep host adapter | Ravenclaw owns projection from runtime admission/execution-gate decisions into redacted GovEngine admission, policy, approval, and audit records while keeping security policy semantics, approval workflow, and audit storage host-owned. |
| `engine/govengine_runner_supervision_projection.py` | `govengine.execution.supervision` | keep host adapter | Ravenclaw owns projection from approved-spec runner boundaries into GovEngine supervision plans, leases, and receipts while keeping concrete tool adapters and live backend authority host-owned. |
| `engine/govengine_review_projection.py` | `govengine.review` | keep host adapter | Ravenclaw owns projection from receipt-bounded evidence review into GovEngine requirement, claim, qualification, and review-result shapes while keeping finding taxonomy and SCLite review-bundle verdicts outside GovEngine. |
| `engine/govengine_security_profile.py` | `govengine.security_profile` | removed | Public validation and tests import the published GovEngine facade directly; no Ravenclaw host logic remained. |
| `engine/govengine_control_gate_adapter.py` | `govengine.core`, `govengine.execution.gate`, `govengine.sclite_contracts`, `govengine.signing`, `govengine.state_index` | keep host adapter; no missing-GovEngine fallback | Ravenclaw owns host runner/profile selection while GovEngine owns reusable gate and signing objects. |
| `engine/govengine_trust_demo.py` | `govengine.signing` demo ports | keep host demo helper; no local signing fallback | Public validation expects GovEngine demo ports from the published package; Ravenclaw only projects the demo trust result into public-safe artifacts. |

## Removal Candidates

Compatibility wrappers are migrational, not a target architecture. Once active
Ravenclaw callers and tests have migrated to `govengine.*` imports, the
historical `engine.*` alias should be deleted unless a concrete host-owned
adapter need remains. Retired in cleanup passes: `action_schema`,
`action_compiler`, `action_validators`, `analysis_contract`,
`capability_recipes`, `evidence_policy`, `execution_contracts`,
`govengine_security_profile`, `policy_core`, `policy_gateway`, `scl_ravenclaw_adapter`,
`semantic_loss_policy`, `signal_contract`, and `tool_registry`.

## Validation Rule

For the active package chain, public install validation must fail if
`govengine_boundary_profile.status` is not `passed`. The boundary-profile module
imports `govengine.kernel_boundary_report` directly, so a missing report is an
import/validation failure rather than a tolerated readiness state.

In addition, `scripts/validate_govengine_helper_boundary.py` must derive the
optional module allowlist from GovEngine's public `security_profile_helpers`
registry and reject active runtime/Logdash imports of any registered optional
module outside `engine/govengine_security_helpers.py`. This containment is a
migration checkpoint, not evidence that those helper responsibilities belong
permanently in GovEngine.
