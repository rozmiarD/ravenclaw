# GovEngine Wrapper Audit

Ravenclaw consumes GovEngine as the published package `govengine>=0.2.0,<0.3`.
This file records which `engine/` modules are compatibility wrappers over
GovEngine and which host-side seams remain Ravenclaw-owned.

## Classification

| Module | Upstream surface | Status | Rationale |
| --- | --- | --- | --- |
| `engine/action_schema.py` | `govengine.action_schema` | removed | Ravenclaw active callers and tests import action schema constants from GovEngine directly. |
| `engine/action_validators.py` | `govengine.action_validators` | removed | Ravenclaw active callers and tests import validators from GovEngine directly. |
| `engine/action_compiler.py` | `govengine.action_compiler` | removed | Ravenclaw active callers and tests import the compiler from GovEngine directly. |
| `engine/capability_recipes.py` | `govengine.capability_recipes` | removed | Ravenclaw active callers and tests import capability helpers from GovEngine directly. |
| `engine/tool_registry.py` | `govengine.tool_registry` | keep thin alias | Preserves registry imports and monkeypatch compatibility for existing tests. |
| `engine/semantic_loss_policy.py` | `govengine.semantic_loss_policy` | removed | Ravenclaw active callers and tests import semantic-loss helpers from GovEngine directly. |
| `engine/policy_core.py` | `govengine.policy.core` | keep thin alias | Preserves runtime policy helper imports. |
| `engine/policy_gateway.py` | `govengine.policy.gateway` | keep thin alias | Preserves policy decision imports and v0 compatibility helpers. |
| `engine/execution_contracts.py` | `govengine.contracts.execution` | keep thin alias | Preserves execution contract helper imports. |
| `engine/signal_contract.py` | `govengine.contracts.signal` | keep thin alias | Preserves signal contract imports. |
| `engine/analysis_contract.py` | `govengine.contracts.analysis` | keep thin alias | Preserves analysis contract imports. |
| `engine/evidence_policy.py` | `govengine.contracts.evidence_policy` | keep thin alias | Preserves confirmation-evidence policy imports. |
| `engine/scl_ravenclaw_adapter.py` | `govengine.sclite_adapter` | keep thin alias | Preserves the Ravenclaw-to-SCLite adapter import while GovEngine owns the reusable adapter seam. |
| `engine/govengine_boundary_profile.py` | `govengine.kernel_boundary_report` | keep required host check | Ravenclaw validates the published 0.2 boundary report and profile non-claims during public install validation. |
| `engine/govengine_security_profile.py` | `govengine.security_profile` | keep host entrypoint; fallback is legacy diagnostic only | Public validation requires the upstream facade; the fallback remains for clearer diagnostics in unsupported local environments. |
| `engine/govengine_control_gate_adapter.py` | `govengine.core`, `govengine.execution.gate`, `govengine.sclite_contracts`, `govengine.signing`, `govengine.state_index` | keep host adapter | Ravenclaw owns host runner/profile selection while GovEngine owns reusable gate objects. |
| `engine/govengine_trust_demo.py` | `govengine.signing` demo ports | keep host demo helper; no local signing fallback | Public validation expects GovEngine demo ports from the published package; Ravenclaw only projects the demo trust result into public-safe artifacts. |

## Removal Candidates

Compatibility wrappers are migrational, not a target architecture. Once active
Ravenclaw callers and tests have migrated to `govengine.*` imports, the
historical `engine.*` alias should be deleted unless a concrete host-owned
adapter need remains. Retired in cleanup passes: `action_schema`,
`action_compiler`, `action_validators`, `capability_recipes`, and
`semantic_loss_policy`.

## Validation Rule

For the 0.2 package chain, public install validation must fail if
`govengine_boundary_profile.status` is not `passed`. `unavailable` is no longer
an acceptable readiness state when Ravenclaw requires `govengine>=0.2.0,<0.3`.
