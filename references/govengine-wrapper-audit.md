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
| `engine/tool_registry.py` | `govengine.tool_registry` | removed | Ravenclaw active callers and tests import tool-registry helpers from GovEngine directly; mutable state tests monkeypatch the GovEngine module itself. |
| `engine/semantic_loss_policy.py` | `govengine.semantic_loss_policy` | removed | Ravenclaw active callers and tests import semantic-loss helpers from GovEngine directly. |
| `engine/policy_core.py` | `govengine.policy.core` | removed | Ravenclaw active callers and tests import runtime policy helpers from GovEngine directly. |
| `engine/policy_gateway.py` | `govengine.policy.gateway` | removed | Ravenclaw active callers and tests import policy gateway helpers from GovEngine directly. |
| `engine/execution_contracts.py` | `govengine.contracts.execution` | removed | Ravenclaw active callers and tests import execution contract helpers from GovEngine directly. |
| `engine/signal_contract.py` | `govengine.contracts.signal` | removed | Ravenclaw active callers and tests import signal contract helpers from GovEngine directly. |
| `engine/analysis_contract.py` | `govengine.contracts.analysis` | removed | Ravenclaw active callers and tests import analysis contract helpers from GovEngine directly. |
| `engine/evidence_policy.py` | `govengine.contracts.evidence_policy` | removed | Ravenclaw active callers and tests import confirmation-evidence helpers from GovEngine directly. |
| `engine/scl_ravenclaw_adapter.py` | `govengine.sclite_adapter` | removed | Ravenclaw active callers and tests import the SCLite adapter seam from GovEngine directly. |
| `engine/govengine_boundary_profile.py` | `govengine.kernel_boundary_report` | keep required host check; no unavailable fallback | Ravenclaw validates the published 0.2 boundary report and profile non-claims during public install validation. |
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

For the 0.2 package chain, public install validation must fail if
`govengine_boundary_profile.status` is not `passed`. The boundary-profile module
imports `govengine.kernel_boundary_report` directly, so a missing report is an
import/validation failure rather than a tolerated readiness state.
