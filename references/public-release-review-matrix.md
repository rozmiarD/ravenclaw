# Public release review matrix

This is the bounded review artifact for deciding what should happen to major mixed-content areas before any public repository snapshot is assembled.

## Decision labels
- **public-candidate**: likely safe to publish after normal review
- **review-required**: may be publishable in part, but requires deliberate inspection
- **exclude-from-public-snapshot**: should not be carried into the default public snapshot
- **replace-with-example**: public repo should use a sample, stub, or redacted example instead of the live/local artifact set

## Matrix

### `engine/`, `logdash/`, `tests/`, `references/`
- decision: **public-candidate**
- reason: core code, tests, and shared reference docs are the most natural public project surfaces
- note: still review for embedded environment-specific assumptions or sensitive examples

### top-level docs and project metadata
- decision: **public-candidate**
- examples: `README.md`, `ARCHITECTURE.md`, `STATE_FILES.md`, `SECURITY.md`, `CONTRIBUTING.md`, `LICENSE`, `CODE_OF_CONDUCT.md`, `VERSION_ROADMAP.md`
- note: this is the main public-facing explanation layer

### `reports/campaign_registry/`
- decision: **review-required**
- reason: structurally valuable as an example of planner history, but may contain campaign-specific names, templates, or environment-specific details
- preferred public treatment: review selectively, then either publish a sanitized subset or replace with one intentionally prepared example registry entry

### other `reports/` content
- decision: **exclude-from-public-snapshot**
- reason: mixed audits, closeouts, local runtime state, generated artifacts, release scratch notes, and deployment-specific history are too mixed to treat as default public content

### `reports/state/`, `reports/cache/`, `reports/archive/`, dotfiles under `reports/`
- decision: **exclude-from-public-snapshot**
- reason: these are local/generated runtime artifacts or control-plane state, not clean public repository content

### `memory/`
- decision: **exclude-from-public-snapshot**
- reason: personal/operator continuity and local internal notes

### `logs/`
- decision: **exclude-from-public-snapshot**
- reason: local execution history and potentially sensitive runtime traces

### `pending/`
- decision: **exclude-from-public-snapshot**
- reason: unfinished local staging area, not a stable public artifact class

### `tmp/`
- decision: **exclude-from-public-snapshot**
- reason: ephemeral work products, probes, and handoff residue

### `state/`
- decision: **review-required**
- reason: the directory name suggests runtime or local state; keep private by default unless a specific file is intentionally converted into public sample material
- preferred public treatment: publish only prepared examples, if any

### workspace/operator-specific root files
- decision: **exclude-from-public-snapshot**
- examples: `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, `WORKFLOW.md`, `HEARTBEAT.md`, `MEMORY.md`, `NEXT_SESSION.md`
- reason: local operator/bootstrap/identity guidance rather than public project documentation

## Recommended next public-release action
The next prep wave should build a deliberate public snapshot plan with:
1. a keep list for public docs/code
2. an explicit exclude list for local/internal areas
3. a short set of sample/example artifacts for anything worth illustrating publicly
