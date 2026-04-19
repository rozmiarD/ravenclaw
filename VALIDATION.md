# VALIDATION.md

This file tells a public reader how to validate the current Ravenclaw repository without assuming a full live operator environment.

## Fast public validation path

After following `INSTALL.md`, run:

```bash
pytest -q
```

This is the primary repo-wide validation command exposed publicly today.

## What this validates

Running the suite exercises public-visible correctness signals across areas such as:
- planner and runtime contracts
- policy and approval behavior
- execution contract shaping
- Logdash control and state projection behavior
- runtime recovery truth
- evaluation and replay semantics

## Focused validation reads

If you want to inspect representative trust anchors before or after running tests, start here:
- `.github/workflows/pytest.yml`
- `tests/test_logdash_smoke.py`
- `tests/test_logdash_operator_truth_contracts.py`
- `engine/tests/test_execution_contracts.py`
- `engine/tests/test_runtime_plan_service_contracts.py`
- `references/runtime-task-contract-v2.md`
- `references/logdash-operator-truth-contracts.md`

## Demo plus validation

A useful public review path is:
1. follow `DEMO.md`
2. run `pytest -q`
3. inspect `QUALITY_SIGNALS.md`

That gives a reader:
- a safe demo path
- a repo-wide automated validation path
- a short explanation of what the proof surfaces do and do not mean

## What not to assume

Passing tests does **not** mean:
- every live deployment path is public-ready
- every subsystem is frozen
- the repo already has polished packaging or production ergonomics

Validation should be read together with `PUBLIC_STATUS.md`, not as a substitute for it.

## Current truth

Ravenclaw is already testable and inspectable in public form.
The remaining gap is less about whether verification exists, and more about making those verification surfaces easier for public readers to discover and interpret.