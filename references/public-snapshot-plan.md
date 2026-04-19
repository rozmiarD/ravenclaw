# Public snapshot plan

This document defines the bounded plan for assembling a future public Ravenclaw repository snapshot.
It is intentionally concrete: what to keep, what to exclude, and what to replace with prepared examples.

## 1. Public snapshot keep-list
The default public snapshot should keep these categories:

### Core code
- `engine/`
- `logdash/`
- `tests/`
- selected top-level helper scripts that are generic and safe to publish

### Core docs and project metadata
- `README.md`
- `ARCHITECTURE.md`
- `STATE_FILES.md`
- `VERSION_ROADMAP.md`
- `OPEN_SOURCE_1_0_PLAN.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `CODE_OF_CONDUCT.md`
- selected docs under `references/`

### Safe config and policy surfaces
- `policy.yaml`
- `whitelist.yaml`
- `proxy.yaml`
- `budgets.yaml`
- `campaign.md`
only after confirming they do not contain environment-specific or private values

## 2. Public snapshot exclude-list
The default public snapshot should exclude these categories entirely unless a later explicit decision says otherwise:

### Local/private runtime residue
- `memory/`
- `logs/`
- `pending/`
- `tmp/`
- `state/`
- `workspace-brain/`

### Mixed runtime/control-plane artifacts
- most of `reports/`
- all `reports/.*.json` runtime/control-plane state files
- `reports/state/`
- `reports/cache/`
- `reports/archive/`
- generated latest/summary artifacts and local learning stores

### Workspace/operator-specific guidance
- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `TOOLS.md`
- `WORKFLOW.md`
- `HEARTBEAT.md`
- `MEMORY.md`
- `NEXT_SESSION.md`
- similar local bootstrap or operator-persona files

## 3. Replace-with-example plan
Some artifact classes are worth showing publicly, but not by publishing the live/local copies.

### `reports/campaign_registry/`
Preferred treatment:
- **replace with one intentionally prepared example campaign registry entry**
- sanitize campaign names, templates, target references, and any environment-specific metadata
- keep just enough structure to illustrate planner versioning and blueprint history

### runtime/state artifacts
Preferred treatment:
- **replace with dedicated examples under a future `examples/` or `samples/` path**
- use small redacted JSON/YAML examples showing schema shape, not live local state
- do not publish real `.auto_campaign.*`, host-state, owner-approval, or runtime snapshot files

### reports and audits
Preferred treatment:
- publish only intentionally selected public-facing writeups, if any
- do not treat internal closeout/audit history as default public repo content

## 4. Assembly rule
The public release should be built as a deliberate snapshot from this working tree, not by assuming the whole repository is public-ready as-is.

## 5. Recommended next execution step
A later public-release prep wave should implement this plan by:
1. creating an explicit public keep/exclude manifest
2. preparing one sanitized example campaign-registry sample
3. preparing a small examples/samples area for runtime/state artifact illustration
4. confirming no local/private residue remains in the assembled public snapshot
