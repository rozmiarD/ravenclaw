# THREAT_MODEL.md

## Purpose

This document defines the public threat model for Ravenclaw's trusted core.
It is intentionally practical: Ravenclaw is only credible if its safety story depends on small, explicit trust anchors rather than every upstream planner/model layer behaving perfectly.

## Current trusted core

The public trusted core should be read as these layers:

- policy and scope boundary logic owned by `engine/security_policy_core.py` and `engine/security_policy_gateway.py`, using neutral `govengine.scope_ports`;
- execution-contract shaping consumed from `govengine.contracts.execution` and related schema/reference surfaces;
- execution-time enforcement in `engine/executor.py`;
- dry-run/public-safe demo and proof fixtures under `examples/`;
- reusable governed-runtime helpers consumed from the published `govengine>=0.14.0,<0.15` range;
- contract lifecycle schemas, validators, and hash-chain verification consumed from `sclite-core>=1.0.3,<1.1`.

These layers must remain defensible even when:

- planner output is wrong or overconfident;
- model-generated reasoning is noisy;
- docs are ahead of implementation in some area;
- a caller attempts to smuggle private/runtime data into public artifacts;
- an adapter/carrier is introduced later and sends malformed or over-broad input.

## Primary public risks

### 1. Overclaiming autonomy

Risk: readers infer that Ravenclaw is a ready autonomous offensive platform.

Control posture:

- public docs frame Ravenclaw as a governed reference runtime/control plane;
- public validation is local/dry-run/public-safe;
- live target execution and protocol adapters are explicit non-claims.

### 2. Prompt-only governance

Risk: safety depends on prompts or role descriptions rather than code-level gates.

Control posture:

- BRAIN/planner surfaces propose intent/action shapes;
- AUDITOR/policy gates approve, reject, or require owner review;
- EXECUTION ENGINE owns final executable command construction;
- GovEngine and SCLite surfaces make key contract boundaries reusable and testable.

### 3. Private residue leakage

Risk: logs, pending queues, memory, target playbooks, command transcripts, credentials, session material, or Logdash runtime databases leak into public snapshots.

Control posture:

- public publication uses `scripts/assemble_public_snapshot.sh`, not the operator-home workspace;
- `scripts/audit_public_snapshot_residue.py` checks prepared trees for blockers;
- public fixtures use synthetic/example-only artifacts;
- validation receipts include explicit non-claims around raw live evidence and command transcript publication.

### 4. Dependency / package drift

Risk: Ravenclaw docs or validation assume local Git URL pins or unpublished helper packages.

Control posture:

- public Ravenclaw consumes the package ranges: `govengine>=0.14.0,<0.15` and `sclite-core>=1.0.3,<1.1`;
- install validation checks package importability and `pip check`;
- publication workflow requires clean install validation when dependency metadata changes.

### 5. Adapter authority creep

Risk: future OpenClaw/MCP/A2A carriers accidentally expand authority or bypass Ravenclaw's governance path.

Control posture:

- adapters are deferred until package/contract boundaries remain stable;
- carrier readiness docs treat adapters as transport/presentation layers, not policy authorities;
- OODA decisions and runner receipts are recorded as governance-control evidence without publishing raw output.

## What this threat model does not prove

This document does **not** prove:

- legal authorization for any target;
- production deployment safety;
- that every private operator integration is public-ready;
- that Ravenclaw detects every malicious input or every dependency compromise;
- that public fixtures are live vulnerability evidence.

## Reviewer checklist

A public reviewer should be able to verify:

1. The safe quickstart remains local and dry-run oriented.
2. Public proof fixtures validate without credentials or live target access.
3. Public snapshots exclude private/operator-home areas.
4. The dependency chain resolves from PyPI.
5. Execution authority is not delegated to planner/model text.
6. Non-claims are stated near validation and proof surfaces.

If any of those checks fail, Ravenclaw's public posture should be downgraded until the gap is fixed.
