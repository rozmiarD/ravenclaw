# Admission Policy GovEngine Map

2026-05-20 update: Ravenclaw now has a GovEngine 0.5 admission-policy
projection helper at `engine/govengine_admission_projection.py`. The helper
validates redacted Ravenclaw runtime admission and execution-gate decisions
against `govengine.admission` without moving Ravenclaw security policy
semantics into GovEngine.

## Boundary

Ravenclaw remains the owner of:

- security-specific admission policy and signal meaning;
- host/target scope interpretation;
- depth, cooldown, budget, warmup, and owner-approval semantics;
- audit storage and retention;
- Logdash/operator workflow;
- concrete execution and live-authority decisions.

GovEngine receives only:

- `GovAdmissionDecision` records with redacted `subject_ref` values;
- `GovPolicyDecision` records for neutral allow/deny/defer-style policy shape;
- `GovApprovalRequest` records when Ravenclaw needs to surface approval state;
- `GovAuditRecord` records for public-safe audit linkage.

Raw Ravenclaw hosts and targets are hashed before entering GovEngine. Detail
fields that contain host names are redacted. The adapter does not authorize
execution, enqueue work, write audit storage, or run approval workflows.

## Validation

Focused coverage lives in
`engine/tests/test_govengine_admission_projection.py` and validates:

- planner admission decisions project into `GovAdmissionDecision`;
- host execution gates redact raw host details;
- policy, approval, and audit records validate through GovEngine;
- raw host/target values do not appear in projected payloads.
