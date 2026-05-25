# GovEngine Wrapper Audit

Ravenclaw consumes GovEngine as the package `govengine>=0.11.0a0,<0.12` alongside `sclite-core>=0.8.0a0,<0.9`.
This file records which `engine/` modules are compatibility wrappers over
GovEngine and which host-side seams remain Ravenclaw-owned.

## Classification

| Module | Upstream surface | Status | Rationale |
| --- | --- | --- | --- |
| `engine/security_action_schema.py` | `govengine.action_schema` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns active security action vocabulary while GovEngine keeps the published optional compatibility facade. |
| `engine/security_action_validators.py` | `govengine.action_validators` | host-owned active replacement; upstream compatibility retained | Ravenclaw validates active security action contracts against its local capability/tool catalog. |
| `engine/security_action_compiler.py` | `govengine.action_compiler` | host-owned active replacement; upstream compatibility retained | Ravenclaw compiles security action specs through local tool/recipe/policy semantics. |
| `engine/security_capability_recipes.py` | `govengine.capability_recipes` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns the active security capability recipe book and profile expansion rules. |
| `engine/security_tool_registry.py` | `govengine.tool_registry` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns active tool catalog state, planner-visible profile selection, and local registry persistence. |
| `engine/security_semantic_loss_policy.py` | `govengine.semantic_loss_policy` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns active semantic-loss policy for security action lowering. |
| `engine/security_policy_core.py` | `govengine.policy.core` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns active security tool/pattern/auth policy over its whitelist and tool registry. |
| `engine/security_policy_gateway.py` | `govengine.policy.gateway` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns executed security scope/policy decisions and obtains scope truth from `engine/campaign_utils.py`. |
| `engine/execution_contracts.py` | `govengine.contracts.execution` | removed | Ravenclaw active callers and tests import execution contract helpers from GovEngine directly. |
| `engine/security_signal_contract.py` | `govengine.contracts.signal` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns active finding/workflow/adaptation signal semantics; these are not neutral receipt-bounded review. |
| `engine/security_analysis_contract.py` | `govengine.contracts.analysis` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns active security action/success/semantic-loss analysis interpretation. |
| `engine/security_evidence_policy.py` | `govengine.contracts.evidence_policy` | host-owned active replacement; upstream compatibility retained | Ravenclaw owns confirmation policy over false-positive guards, control comparison, and reproduction evidence. |
| `engine/scl_ravenclaw_adapter.py` | `govengine.sclite_adapter` | removed | Ravenclaw uses `engine/security_contract_layer.py` as the host-owned current lifecycle projection over GovEngine/SCLite primitives; active runtime and demo callers do not publish directly through the neutral-kernel dependency. |
| `engine/govengine_boundary_profile.py` | `govengine.kernel_boundary_report` | keep required host check; no unavailable fallback | Ravenclaw validates the GovEngine boundary report and profile non-claims during public install validation. |
| `engine/govengine_state_control_projection.py` | `govengine.runtime_shell` | keep host adapter | Ravenclaw owns projection from Logdash/runtime state into GovEngine `GovControlAction`, `GovQueueSnapshot`, and `GovRuntimeSnapshot` shapes while keeping UI, storage, process control, and campaign semantics host-owned. |
| `engine/govengine_planning_projection.py` | `govengine.planning` | keep host adapter | Ravenclaw owns projection from planner/runtime task semantics into redacted GovEngine task and plan-intent contracts while keeping security planning semantics host-owned. |
| `engine/govengine_admission_projection.py` | `govengine.admission` | keep host adapter | Ravenclaw owns projection from runtime admission/execution-gate decisions into redacted GovEngine admission, policy, approval, and audit records while keeping security policy semantics, approval workflow, and audit storage host-owned. |
| `engine/govengine_runner_supervision_projection.py` | `govengine.execution.supervision` | keep host adapter | Ravenclaw owns projection from approved-spec runner boundaries into GovEngine supervision plans, leases, and receipts while keeping concrete tool adapters and live backend authority host-owned. |
| `engine/govengine_review_projection.py` | `govengine.review` | keep host adapter | Ravenclaw owns projection from receipt-bounded evidence review into GovEngine requirement, claim, qualification, and review-result shapes while keeping finding taxonomy and SCLite review-bundle verdicts outside GovEngine. |
| `engine/govengine_security_profile.py` | `govengine.security_profile` | removed | Public validation and tests no longer import or require the retired optional GovEngine facade; Ravenclaw owns the active security-profile manifest. |
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

In addition, `scripts/validate_govengine_helper_boundary.py` must use
Ravenclaw's static retired-helper denylist and reject active runtime/Logdash
imports of those optional legacy modules outside
`engine/govengine_security_helpers.py`. It must also reject reintroduction of
host-owned action/tooling, policy/scope, or review-security
modules, including `govengine.policy.core`, `govengine.tool_registry`,
`govengine.policy.gateway`, `govengine.contracts.signal`,
`govengine.contracts.analysis`, and `govengine.contracts.evidence_policy`, into
that seam after Ravenclaw moved active security behavior to local
`engine/security_*` modules. Neutral `govengine.review` remains a distinct
projection contract.
