# OpenClaw Carrier Readiness Packet — 2026-05-12

## Status

Historical/superseded readiness record. Its legacy fixture references document
the evidence available on 2026-05-12; they are not current public validation
surfaces. The active readiness record is
`references/openclaw-adapter-readiness-packet-2026-05-20.md`.

Readiness review only. Recommendation: **do not start adapter implementation yet**; keep OpenClaw at docs/contracts-only prep until the remaining blockers below are closed.

This packet does not authorize live target execution, OpenClaw plugin/Skill implementation, MCP/A2A work, production-readiness claims, or live vulnerability discovery.

## Packet metadata

- Packet ID: `openclaw-readiness-2026-05-12`
- Date: 2026-05-12
- Author/operator: Ravenclaw maintainer/operator workflow
- Reviewer checklist owner: maintainer/operator
- Target carrier: OpenClaw Skill/plugin candidate
- Proposed mode: docs/contracts-only readiness review

## Explicit non-goals

This proposal does not:

- implement an OpenClaw adapter;
- bypass Ravenclaw policy/auditor/execution-engine authority;
- let chat/model prose become executable command authority;
- expose private operator state, memory, credentials, raw logs, private paths, or unredacted runtime artifacts;
- claim production deployment readiness;
- claim live vulnerability discovery from dry-run/local artifacts;
- change carrier order from OpenClaw first, MCP later, A2A last/example-first.

## Readiness conclusion

OpenClaw is the correct first carrier candidate, but implementation should wait. The public contract path is credible enough for a readiness packet, not enough for a safe adapter branch.

Ready today:

- public proof trace exists and is validated locally;
- Ravenclaw demo scenario records Ravenclaw -> GovEngine -> SCLite package-chain truth;
- GovEngine neutral core surfaces are distinct from optional legacy security-profile helper compatibility;
- SCLite validates v0.2 lifecycle chains and semantic lifecycle links;
- compact OODA control decisions can now be projected into receipt/evidence artifacts without raw telemetry.

Blockers before implementation:

- no OpenClaw-specific redaction policy has been tested against direct, group, attachment, and embedded-output surfaces;
- no approval UX exists for showing prepared-vs-approved execution specs inside OpenClaw;
- no carrier-specific tests assert that OpenClaw cannot widen command authority;
- no rollback/stop control has been demonstrated from OpenClaw back into Ravenclaw runtime state;
- no public/private output matrix exists for OpenClaw channels.

## Scope UX

Required before implementation:

- scope must come from explicit operator-provided scope artifacts or Ravenclaw policy context;
- OpenClaw must display/refer to authorized scope before action proposal;
- out-of-scope requests must return structured refusal/review state, not prose-only warnings;
- generated artifacts must preserve scope facts and target-in-scope truth.

Evidence today:

- `examples/security-contract-proof/input_scope.json`
- `schemas/policy_decision.v0.1.schema.json`
- `examples/contract-lifecycle-v0.2/`
- `references/openclaw-adapter-contract-map.md`

Blocker: OpenClaw-specific scope UI/UX is not implemented or tested.

## Secrets and redaction

Required before implementation:

- redact stdin, cookies, auth headers, bearer tokens, private paths, memory, local logs, raw stdout/stderr, request/response bodies, and private target identifiers;
- treat group chats and shared channels as high-leakage contexts by default;
- require deterministic redaction before any message, file, embed, or attachment leaves Ravenclaw.

Evidence today:

- `engine/ooda_receipts.py`
- `references/ooda-receipt-evidence-notes.md`
- `schemas/evidence_bundle.v0.1.schema.json`
- `examples/security-contract-proof/evidence_bundle.json`

Blocker: no OpenClaw channel-output redaction test matrix exists.

## Command authority boundary

Required before implementation:

- OpenClaw may carry requests and display decisions, but must not construct shell commands directly;
- Ravenclaw policy/auditor and execution-engine-approved specs remain the authority boundary;
- only approved execution specs can reach execution-engine construction;
- model/chat text cannot bypass prepared/approved spec separation.

Evidence today:

- `references/approved-execution-spec-v0.1.md`
- `references/execution-receipt-v0.1.md`
- `engine/executor.py`
- `engine/tests/test_govengine_control_gate_adapter.py`
- `engine/tests/test_govengine_ooda_adapter.py`

Blocker: no OpenClaw adapter negative tests exist yet.

## Contracts consumed and emitted

| Artifact | Consumed | Emitted | Schema/reference | Readiness |
| --- | --- | --- | --- | --- |
| Scope/input | yes | no | `examples/security-contract-proof/input_scope.json` | public proof ready; OpenClaw UX missing |
| `PolicyDecision` | yes | maybe later | `schemas/policy_decision.v0.1.schema.json` | preserve structured fields |
| `PreparedExecutionSpec` / redacted prepared spec | yes | maybe later | `govengine.contracts.execution` | must display as proposal, not approval |
| `ApprovedExecutionSpec` | yes | no | `schemas/approved_execution_spec.v0.1.schema.json` | execution boundary |
| `ExecutionReceipt` | yes | maybe later | `schemas/execution_receipt.v0.1.schema.json` | dry-run/live truth required |
| `EvidenceBundle` | yes | maybe later | `schemas/evidence_bundle.v0.1.schema.json` | governance/evidence separation required |
| OODA control decisions | yes | maybe later | `references/ooda-receipt-evidence-notes.md` | compact projection now available |
| Validation receipt | yes | no | `schemas/security_contract_validation_receipt.v0.1.schema.json` | public-safe validation pointer |
| Public snapshot manifest | yes | no | `schemas/public_snapshot_manifest.v0.1.schema.json` | publication/snapshot review pointer |

## Validation commands before any implementation branch

```bash
python scripts/validate_public_install.py --dev
python scripts/run_security_contract_validation.py --include-pytest
python scripts/list_public_validation_surfaces.py --format json --check
./scripts/bootstrap_public_demo.sh scenario
```

Before publication of adapter-related work:

```bash
python scripts/run_security_contract_validation.py --include-pytest --include-github-actions-matrix
```

Required future OpenClaw-specific tests:

- scope display/refusal behavior;
- prepared-vs-approved spec separation;
- no direct shell command construction from chat/model prose;
- deterministic redaction across direct/group/file/embed outputs;
- dry-run/live truth labeling;
- stop-loss/owner-review propagation;
- compact OODA control-decision rendering without raw telemetry.

## Rollback and stop conditions

Pause or roll back adapter work if any of these appear:

- scope ambiguity;
- missing policy decision;
- missing approved execution spec;
- command authority ambiguity;
- raw logs/private state in OpenClaw output;
- dry-run/live truth ambiguity;
- channel leakage risk;
- validation failure;
- attempt to pivot into MCP/A2A first;
- live execution authority expansion without explicit approval.

## Decision

OpenClaw remains the first future carrier candidate. The next action is **not implementation**; it is to add OpenClaw-specific redaction/output tests and an approval UX sketch. MCP and A2A remain deferred.
