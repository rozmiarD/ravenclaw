# Runner Supervision GovEngine Map

2026-05-20 update: Ravenclaw now has a GovEngine 0.6 runner-supervision
projection helper at `engine/govengine_runner_supervision_projection.py`. The
helper validates approved-spec runner boundaries against
`govengine.execution.supervision` without moving concrete tool adapters or live
backend authority into GovEngine.

## Boundary

Ravenclaw remains the owner of:

- concrete tool adapters and subprocess behavior;
- scope/operator authorization interpretation;
- local-lab or future controlled-live runtime modes;
- artifact storage and runner work directories;
- Logdash/operator workflow;
- campaign and security-runtime semantics.

GovEngine receives only:

- approved-spec `GovRunnerRequest` records;
- `GovSupervisionPlan` records with timeout/cwd/env/stdin policy shape;
- storage-neutral `GovRunnerLease` records;
- `GovRunnerReceipt` records that bind attempted runner steps to the request.

Raw intent is not accepted as a runner source. Dry-run remains the default.
Live backend requests are blocked unless a future host-provided plan explicitly
enables them with bounded policies and separate negative tests.

## Validation

Focused coverage lives in
`engine/tests/test_govengine_runner_supervision_projection.py` and validates:

- approved execution specs project into runner request/supervision/lease/receipt
  records;
- live backend requests are blocked by default;
- receipts must match the supervised request steps;
- supervision metadata rejects raw prompt claims.
