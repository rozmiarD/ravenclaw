# Ravenclaw Consumer Cleanup Review — 2026-05-12

## Status

Post-`govengine==0.1.5` consumer review. This note is historical; later cleanup after `govengine==0.2.0` retired pure compatibility aliases once active Ravenclaw callers/tests migrated to direct GovEngine imports. The standing recommendation remains to keep Ravenclaw as the reference runtime/control plane and avoid broad extraction. Only true host-side projection/adapter logic should remain in Ravenclaw.

## Reviewed seams

- `engine/govengine_security_profile.py`
- `govengine.sclite_adapter` direct imports, after retiring the former `engine/scl_ravenclaw_adapter.py` alias
- `engine/security_contract_layer.py`
- `engine/govengine_control_gate_adapter.py`
- `scripts/validate_public_install.py`
- `scripts/run_demo_scenario.py`
- GovEngine seam tests under `engine/tests/test_govengine_*`

## Findings

### Keep in Ravenclaw

These remain host/runtime-owned and should not be moved into GovEngine now:

- Logdash and operator-control UX;
- public demo and reviewer scenario orchestration;
- public snapshot assembly and residue audit;
- live/local subprocess execution ownership;
- campaign runtime state, queues, and recovery semantics;
- OpenClaw/MCP/A2A carrier readiness documentation;
- host-side redaction/output decisions for public artifacts.

### Historical compatibility posture

- `engine/scl_ravenclaw_adapter.py` was originally kept as a compatibility alias to GovEngine's SCLite adapter while public imports/tests still referenced the Ravenclaw path. It has since been retired; active code imports `govengine.sclite_adapter` directly.
- `engine/govengine_security_profile.py` should remain as a defensive compatibility entrypoint. The current package floor expects `govengine.security_profile`, but the wrapper keeps older local environments from failing hard and makes Ravenclaw's expected optional profile explicit.
- `engine/govengine_control_gate_adapter.py` remains appropriate because it assembles Ravenclaw host artifacts/context into GovEngine gate inputs without moving host policy/state ownership into GovEngine.
- `engine/govengine_trust_demo.py` remains Ravenclaw-owned host projection glue: it exercises GovEngine signer/verifier ports in public demo artifacts while keeping PKI, CA, KMS, and key-store ownership out of GovEngine and Ravenclaw.

### New bounded cleanup completed

- `engine/ooda_receipts.py` adds a Ravenclaw-owned projection layer for compact OODA control-decision summaries.
- `engine/security_contract_layer.py` now projects those summaries into v0.1/v0.2 public receipts/evidence when runtime data supplies OODA decisions.
- This keeps GovEngine responsible for the OODA decision contract and Ravenclaw responsible for public artifact projection/redaction.
- Demo lifecycle tickets now carry deterministic signing/trust metadata bound to the execution-contract digest, explicitly labelled as fixture/demo evidence rather than production identity proof.

## Non-actions

Do not extract these now:

- full runtime runner;
- Logdash;
- public snapshot publishing machinery;
- private/operator state handling;
- OpenClaw adapter implementation;
- live subprocess backend ownership.

## Next cleanup candidates

Only revisit extraction if one of these becomes true:

1. a Ravenclaw wrapper duplicates stable GovEngine logic rather than adapting host context;
2. a public validation seam requires the same code in Ravenclaw and GovEngine;
3. OpenClaw readiness tests reveal a reusable carrier-neutral helper that belongs in GovEngine;
4. OODA/evidence projection needs a neutral summary helper in GovEngine and can be released cleanly.

Until then, broad extraction would add churn without improving the boundary.
