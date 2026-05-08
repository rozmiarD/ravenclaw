# Contributing

## Philosophy
RAVENCLAW changes are most useful when they improve one or more of these:
- governance correctness
- runtime safety and control integrity
- evidence quality and reproducibility
- operator visibility and recoverability
- policy/runtime consistency

## Before changing code

Read `REPO_WORKFLOW.md` before any commit, branch cleanup, or public push. It is the canonical Git identity/worktree/branch procedure.

Read, in order:
1. `README.md`
2. `ARCHITECTURE.md`
3. `STATE_FILES.md`
4. relevant implementation plan(s) in `implementation-plans/`

## Change rules
- prefer bounded, test-backed slices
- avoid introducing new hardcoded workstation paths
- keep runtime truth and UI projections aligned
- if a file/path moves, update docs, tests, and links in the same wave
- do not weaken policy or owner-approval semantics for convenience

## Tests
At minimum, run targeted tests for touched areas.
For wider refactors or path/contract changes, run the full suite:

```bash
pytest -q
```

## Documentation expectations
Update docs when you change:
- shared state file locations
- runtime/reporting artifacts
- module ownership/contracts
- setup/bootstrap instructions
- path assumptions or environment variables

## Pull request guidance
A good change summary should include:
- what changed
- why it changed
- governance/runtime impact
- affected state files or docs
- validation performed
