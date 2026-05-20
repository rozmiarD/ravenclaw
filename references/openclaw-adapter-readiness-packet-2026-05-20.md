# OpenClaw Adapter Readiness Packet — 2026-05-20

## Status

Readiness packet only. Recommendation: **do not start adapter implementation
yet**. Ravenclaw now has enough GovEngine/SCLite package-boundary coverage to
define the OpenClaw gates precisely, but not enough carrier-specific UX,
redaction, or rollback tests to implement a safe OpenClaw Skill/plugin.

This packet does not authorize live target execution, OpenClaw Skill/plugin
implementation, MCP/A2A work, production-readiness claims, or live vulnerability
discovery.

## Packet metadata

- Packet ID: `openclaw-readiness-2026-05-20`
- Date: 2026-05-20
- Author/operator: Ravenclaw maintainer/operator workflow
- Reviewer checklist owner: maintainer/operator
- Target carrier: OpenClaw Skill/plugin candidate
- Proposed mode: docs/contracts-only readiness review

## Current evidence

Ready today:

- Ravenclaw public `main` consumes `govengine>=0.7.0,<0.8` and
  `sclite-core>=0.5.1,<0.6`;
- GovEngine surfaces validated by Ravenclaw include runtime shell, planning,
  admission, runner supervision, and evidence review;
- Ravenclaw has host projection helpers for state/control, planning,
  admission, runner supervision, and evidence review;
- SCLite remains the lifecycle/review-bundle validation authority;
- public install validation checks the GovEngine surface registry,
  `govengine.security_profile`, GovEngine boundary report, and Ravenclaw
  security-profile manifest;
- the structural Security Contract validation profile passes without live
  target execution.

Still blocked before implementation:

- no OpenClaw-specific scope display/refusal UX is tested;
- no OpenClaw channel redaction matrix exists for direct chat, group chat,
  files, embeds, or attachments;
- no negative tests prove an OpenClaw carrier cannot widen command authority;
- no OpenClaw rollback/stop control has been demonstrated back into Ravenclaw
  runtime state;
- no public/private output matrix exists for OpenClaw channels.

## Explicit non-goals

This proposal does not:

- implement an OpenClaw adapter;
- bypass Ravenclaw policy/auditor/execution-engine authority;
- let chat/model prose become executable command authority;
- expose private operator state, memory, credentials, raw logs, private paths,
  or unredacted runtime artifacts;
- claim production deployment readiness;
- claim live vulnerability discovery from dry-run/local artifacts;
- change carrier order from OpenClaw first, MCP later, A2A last/example-first.

## Scope UX

Required before implementation:

- scope must come from explicit operator-provided scope artifacts or Ravenclaw
  policy context;
- OpenClaw must display or reference authorized scope before action proposal;
- out-of-scope requests must return structured refusal/review state, not
  prose-only warnings;
- generated artifacts must preserve scope facts and target-in-scope truth.

Evidence today:

- `examples/security-contract-proof/input_scope.json`
- `schemas/policy_decision.v0.1.schema.json`
- `references/openclaw-adapter-contract-map.md`
- `engine/govengine_admission_projection.py`

Blocker: OpenClaw-specific scope UI/UX is not implemented or tested.

## Secrets and redaction

Required before implementation:

- redact stdin, cookies, auth headers, bearer tokens, private paths, memory,
  local logs, raw stdout/stderr, request/response bodies, and private target
  identifiers;
- treat group chats and shared channels as high-leakage contexts by default;
- require deterministic redaction before any message, file, embed, or attachment
  leaves Ravenclaw.

Evidence today:

- `engine/ooda_receipts.py`
- `engine/govengine_review_projection.py`
- `references/ooda-receipt-evidence-notes.md`
- `schemas/evidence_bundle.v0.1.schema.json`
- `examples/security-contract-proof/evidence_bundle.json`

Blocker: no OpenClaw channel-output redaction test matrix exists.

## Command authority boundary

Required before implementation:

- OpenClaw may carry requests and display decisions, but must not construct shell
  commands directly;
- Ravenclaw policy/auditor and execution-engine-approved specs remain the
  authority boundary;
- only approved execution specs can reach execution-engine construction;
- model/chat text cannot bypass prepared/approved spec separation;
- GovEngine runner-supervision contracts must be preserved before any host
  runner action.

Evidence today:

- `references/approved-execution-spec-v0.1.md`
- `references/execution-receipt-v0.1.md`
- `engine/executor.py`
- `engine/govengine_runner_supervision_projection.py`
- `engine/tests/test_govengine_control_gate_adapter.py`
- `engine/tests/test_govengine_runner_supervision_projection.py`

Blocker: no OpenClaw adapter negative tests exist yet.

## Contracts consumed and emitted

| Artifact | Consumed | Emitted | Schema/reference | Readiness |
| --- | --- | --- | --- | --- |
| Scope/input | yes | no | `examples/security-contract-proof/input_scope.json` | public proof ready; OpenClaw UX missing |
| `PolicyDecision` | yes | maybe later | `schemas/policy_decision.v0.1.schema.json` | preserve structured fields |
| Prepared/redacted execution spec | yes | maybe later | `govengine.contracts.execution` | must display as proposal, not approval |
| Approved execution spec | yes | no | `schemas/approved_execution_spec.v0.1.schema.json` | execution boundary |
| Runner supervision plan/lease/receipt | yes | maybe later | `govengine.execution.supervision` | no live backend by default |
| Execution receipt | yes | maybe later | `schemas/execution_receipt.v0.1.schema.json` | dry-run/live truth required |
| Evidence qualification/review result | yes | maybe later | `govengine.review` | dry-run evidence must not become live-vulnerability proof |
| Evidence bundle | yes | maybe later | `schemas/evidence_bundle.v0.1.schema.json` | governance/evidence separation required |
| SCLite review bundle | yes | no | `sclite review` / review-bundle docs | SCLite owns verdict authority |
| Validation receipt | yes | no | `schemas/security_contract_validation_receipt.v0.1.schema.json` | public-safe validation pointer |
| Public snapshot manifest | yes | no | `schemas/public_snapshot_manifest.v0.1.schema.json` | publication/snapshot review pointer |

## Validation commands before any implementation branch

```bash
python scripts/validate_public_install.py --dev
python -m pytest -q engine/tests/test_ravenclaw_security_profile.py
python -m pytest -q engine/tests/test_govengine_runner_supervision_projection.py engine/tests/test_govengine_review_projection.py
python scripts/run_security_contract_validation.py --structural-only --include-pytest
```

Required future OpenClaw-specific tests:

- scope display/refusal behavior;
- prepared-vs-approved spec separation;
- no direct shell command construction from chat/model prose;
- deterministic redaction across direct/group/file/embed outputs;
- dry-run/live truth labeling;
- stop-loss/owner-review propagation;
- compact GovEngine/Ravenclaw review rendering without raw telemetry.

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

OpenClaw remains the first future carrier candidate. The next action is still
not implementation. The next useful implementation-prep slice is an
OpenClaw-specific redaction/output test matrix and approval UX sketch, backed
by Ravenclaw security-profile manifest validation.
