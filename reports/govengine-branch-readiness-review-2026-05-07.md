# GovEngine Branch Readiness Review — 2026-05-07

Status: local review only; no push performed.
Worktree: `/home/probo/.openclaw/worktrees/ravenclaw-govengine-plan`.
Branch: `ravenclaw/govengine-plan-refresh`.
Reviewed HEAD: `3ef8ad4 feat: extract GovEngine dry-run runner helpers`.
Public `origin/main` at review time: `7519b6a8e96f9b4dc0c32cdfac3ba7878dbbd64a`.

## Branch range reviewed

Commits on this branch over `origin/main`:

1. `1fda753 docs: refresh GovEngine extraction plan`
2. `072e5c8 feat: add GovEngine context seam`
3. `921b2ea feat: expose GovEngine policy and SCLite seams`
4. `df73aac feat: add GovEngine dependency seams`
5. `bff98dc feat: extract GovEngine execution gate helpers`
6. `4b0f538 feat: extract GovEngine command shape helpers`
7. `12f70af feat: add GovEngine scope port`
8. `3ef8ad4 feat: extract GovEngine dry-run runner helpers`

Net branch shape: 44 files changed, about 3,757 insertions / 2,053 deletions over `origin/main`.

## What is ready

### 1. Public snapshot hygiene is green

A fresh public snapshot was assembled at review time and checked directly.

Observed:

- front-door docs present: `README.md`, `INSTALL.md`, `ENVIRONMENT_SUPPORT.md`, `DEMO.md`, `VALIDATION.md`, `QUALITY_SIGNALS.md`, `PUBLIC_STATUS.md`, `AUDIENCE.md`, `DOCS_MAP.md`, `ARCHITECTURE_OVERVIEW.md`, `WHY_RAVENCLAW.md`, `ARCHITECTURE.md`, `STATE_FILES.md`, `SECURITY.md`, `CONTRIBUTING.md`, `LICENSE`, `CODE_OF_CONDUCT.md`;
- excluded local/private areas absent: `memory/`, `logs/`, `pending/`, `tmp/`, `state/`;
- `govengine/` is included in the assembled snapshot;
- residue audit passed with `blockers=0` and contextual warnings only.

Snapshot checks run:

```bash
./scripts/assemble_public_snapshot.sh "$SNAP"
PYTHONDONTWRITEBYTECODE=1 /tmp/ravenclaw-docs-venv/bin/python scripts/validate_security_contract_fixtures.py examples/security-contract-proof
/tmp/ravenclaw-docs-venv/bin/python scripts/audit_public_snapshot_residue.py .
/tmp/ravenclaw-docs-venv/bin/python scripts/build_public_snapshot_manifest.py . --check
```

Result highlights:

- `security_contract_fixtures_ok`
- `public_snapshot_residue_ok`
- `files=551 blockers=0 warnings=29`
- manifest check passed

### 2. Validation parity is green

Publication-readiness parity command:

```bash
/tmp/ravenclaw-docs-venv/bin/python scripts/run_security_contract_validation.py \
  --include-pytest \
  --include-github-actions-matrix \
  --format markdown
```

Receipt result: `status: passed`.

Checks:

- `fixture_validation` passed
- `public_validation_surface_index` passed
- `demo_bundle_smoke` passed
- `assemble_public_snapshot` passed
- `snapshot_fixture_validation` passed
- `snapshot_residue_audit` passed
- `snapshot_replayable_truth_fixture` passed
- `snapshot_scope_fidelity_fixture` passed
- `snapshot_manifest` passed
- `proof_of_value_scorecard` passed
- `proof_of_value_scorecard_fixture` passed
- `focused_pytest` passed
- `github_actions_pytest_matrix` passed

### 3. In-repo migration seam is healthy

The Ravenclaw compatibility-wrapper strategy is working:

- `engine/policy_core.py`, `engine/execution_contracts.py`, and `engine/tool_registry.py` alias GovEngine modules;
- executor now delegates pure execution-gate, command-shape, scope-port, and dry-run result helpers to `govengine.execution.*`;
- prior full slice validations remained green after each stage.

## What is not ready for a separate GovEngine repo yet

### 1. `govengine/` is not standalone-importable by itself

A standalone probe copied only `govengine/` into a temp directory and imported selected modules.

Standalone successes:

- `govengine`
- `govengine.context`
- `govengine.scope`
- `govengine.execution.runner`
- `govengine.execution.command_shape`
- `govengine.execution.approved_spec`
- `govengine.execution.ticket_gate`

Standalone failures:

- `govengine.policy.core` -> `ModuleNotFoundError: No module named 'json_state_io'`
- `govengine.tool_registry` -> `ModuleNotFoundError: No module named 'json_state_io'`
- `govengine.contracts.execution` -> `ModuleNotFoundError: No module named 'campaign_utils'`
- `govengine.policy.gateway` -> transitive `json_state_io` / Ravenclaw helper dependencies

Interpretation: the branch is ready as a Ravenclaw in-repo migration seam, but not ready as an independent GovEngine repository without another dependency-isolation wave.

### 2. Direct Ravenclaw helper imports remain in GovEngine modules

Detected direct bootstrap/helper imports:

- `govengine/contracts/execution.py`
  - imports `campaign_utils.extract_host_from_url`
- `govengine/policy/gateway.py`
  - imports `campaign_utils.extract_host_from_url`, `host_in_scope`, `load_scope_domains`
  - imports `action_compiler.compile_action_spec`
  - imports `action_validators.validate_probe_recipe`, `validate_action_contract_v2`
  - imports `action_schema.DEFAULT_ACTION_TYPE`
- `govengine/tool_registry.py`
  - imports `json_state_io.atomic_write_json`, `safe_load_json_object`

These are acceptable for the current in-place migration, but they are blockers for repo extraction.

### 3. `govengine.policy.gateway` still contains duplicated target-observation/scope logic

Stage 2D/2E moved command-shape and scope-port helpers into `govengine.execution`, but `govengine.policy.gateway` still has its own `_arg_target_observations`, `_extract_hosts_from_text`, and scope enforcement-style logic wired to `campaign_utils`.

Recommendation: before splitting the repo, route `policy.gateway` through the same neutral scope/command-shape ports, or explicitly mark it as a Ravenclaw profile adapter instead of GovEngine core.

### 4. Packaging is partial, not repo-ready

`pyproject.toml` now includes:

```toml
[tool.setuptools]
packages = ["govengine", "govengine.contracts", "govengine.execution", "govengine.policy"]
py-modules = []
```

This is enough to expose in-repo GovEngine packages, but not enough for a clean standalone package because several required modules still live under Ravenclaw `engine/` and are reached through compatibility path bootstrapping.

## Risk assessment

### Safe to do now

- Keep iterating on the in-repo GovEngine branch.
- Publish/review the Ravenclaw branch through a clean snapshot if desired, after applying the usual publish-tree procedure.
- Begin preparing a separate GovEngine repository scaffold as an empty/clean target with package metadata, CI, and docs, but do not copy the current `govengine/` as final standalone source without fixing dependencies.

### Do not do yet

- Do not move subprocess execution into GovEngine before the boundary review below is complete.
- Do not claim GovEngine is a standalone package/repo yet.
- Do not publish from the live worktree.
- Do not split by copying current `govengine/` alone and expecting it to install/import cleanly.

## Recommended next waves

### Stage 2G — dependency isolation before subprocess movement

Goal: make current GovEngine modules importable without Ravenclaw `engine/` path bootstrapping.

Suggested order:

1. Move or port neutral JSON state helpers into `govengine.state_store`.
2. Replace `govengine.tool_registry` dependency on `json_state_io` with the neutral state-store API.
3. Replace `govengine.contracts.execution` dependency on `campaign_utils.extract_host_from_url` with `GovScopePort` or a local neutral host parser.
4. Route `govengine.policy.gateway` target/scope helpers through `govengine.execution.command_shape` + `GovScopePort`.
5. Decide whether `action_schema`, `action_validators`, and `action_compiler` are GovEngine core or Ravenclaw profile adapters; move once, do not duplicate.
6. Add a CI-style test that copies only `govengine/` into a temp directory and imports the public package surface.

Gate:

```bash
python -m pytest -q engine/tests/test_govengine_* 
# plus standalone temp-copy import probe for govengine public modules
```

### Stage 2H — repo scaffold rehearsal

Goal: prepare extraction mechanics without publishing.

Suggested order:

1. Generate a temp standalone repo scaffold.
2. Copy `govengine/`, minimal tests, `pyproject.toml`, README stub, and license.
3. Install editable in a clean venv.
4. Run standalone import and focused tests.
5. Record remaining Ravenclaw dependency blockers.

Gate: no push; report only.

### Stage 2I — execution backend design review

Only after 2G/2H are green:

- define runner protocol/result object;
- keep Ravenclaw concrete subprocess runner as adapter first;
- move dry-run-safe assembly before live execution;
- migrate live subprocess execution last, with explicit operator approval.

## Bottom line

The branch is healthy and public-snapshot-safe as a Ravenclaw migration branch. It is not yet ready to become the first commit of a standalone GovEngine repo without a dependency-isolation wave.

Recommended immediate next action: Stage 2G dependency isolation, not subprocess extraction.
