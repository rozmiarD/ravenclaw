# Repository Workflow

This is the canonical Git workflow for Ravenclaw public repository operations.

## Identity rule

All GitHub commits/tags pushed from this operator workspace must use:

```text
0x505badc0de <32790662+rozmiarD@users.noreply.github.com>
```

Before any commit or push, verify the effective repo-local identity:

```bash
git config --get user.name
git config --get user.email
```

If either value differs, fix it before committing:

```bash
git config user.name '0x505badc0de'
git config user.email '32790662+rozmiarD@users.noreply.github.com'
```

Do not rewrite already-published history only to fix authorship unless the operator explicitly approves a force-push/history rewrite.

## Public push model

Default public repo shape: one clean `main` branch.

For Ravenclaw public pushes:

1. Start from current `origin/main` in a clean publish tree.
2. Apply only the bounded public delta.
3. Validate at the right depth for the change.
4. Run publication/residue checks before pushing.
5. Confirm git identity is `0x505badc0de <32790662+rozmiarD@users.noreply.github.com>`.
6. Push to `main` without force unless explicitly approved.
7. Delete temporary remote branches after merge/push unless the operator asked to keep them.

## Branch hygiene

- Temporary branches are allowed locally for bounded work.
- Remote helper branches are temporary unless explicitly kept for PR/review.
- After `main` is updated, prune merged branches.
- Do not delete an unmerged branch blindly; inspect unique commits/files first.
- If a branch is superseded by a newer public main/package split, delete it locally after documenting the reason.

## Documentation/source-of-truth model

- `REPO_WORKFLOW.md` — Git/worktree/branch/identity rules.
- `PUBLISHING.md` — Ravenclaw public snapshot/publish checklist.
- `README.md` — public front-door truth.
- `PUBLIC_STATUS.md` — public maturity/status truth.
- `VALIDATION.md` — public validation commands and non-claims.
- `QUALITY_SIGNALS.md` — public trust signals.

When files overlap, keep the specific source of truth authoritative and make other files point to it instead of duplicating divergent rules.
