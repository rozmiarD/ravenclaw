# Engine Extraction Plan after SCLite Integration

Date: 2026-05-06
Status: draft plan after Ravenclaw -> SCLite dependency wave

## Current finding

The SCLite split is the right prerequisite for engine extraction. Ravenclaw now has a cleaner boundary:

- **SCLite** owns reusable contract artifacts, schemas, validation, redaction helpers, public-safe fixtures, and CLI helpers.
- **Ravenclaw Runtime** owns policy, approval, planning, execution, orchestration, persistence, Logdash, and proof/demo integration.
- `engine/scl_ravenclaw_adapter.py` is the explicit adapter seam.
- `engine/security_contract_layer.py` remains a compatibility wrapper for Ravenclaw-local callers.

The integration also exposed the main risk for engine extraction: many modules still assume a repository-root execution model and mutate `sys.path` or derive paths from module location. The SCLite `repo_root()` mismatch in the demo bundle was a concrete example. Engine extraction must therefore start with root/context/path ownership, not with moving files to a new repository.

## What not to do next

Do **not** immediately split `engine/` into a separate repository. That would preserve hidden coupling and create a fragile package with unclear ownership.

Do **not** start with adapters/protocols. OpenClaw/MCP/A2A remain later carriers.

Do **not** move Logdash and engine together as one package. Logdash should become a consumer/control-plane of the engine API, not part of the engine core.

## Improved extraction sequence

### Stage 0 — Extraction readiness audit

Goal: make the current dependency graph explicit.

Tasks:
- inventory imports across `engine/`, `logdash/`, `scripts/`, `bin/`, and tests;
- classify modules into groups:
  - `contracts` / schemas / normalization;
  - `policy` / governance;
  - `execution`;
  - `pipeline`;
  - `runtime orchestration`;
  - `planning`;
  - `evaluation/replay`;
  - `public demo`;
  - `Ravenclaw app/control-plane adapters`;
- identify modules that read/write repository paths directly;
- identify generated files still living under `engine/` and route them through `engine/paths.py` or `reports/`;
- produce a small dependency graph/report before code movement.

Gate:
- no code movement yet;
- full pytest and Security Contract validation still pass.

### Stage 1 — Runtime context and path boundary

Goal: stop engine modules from guessing the repository root.

Tasks:
- introduce an explicit `RavenclawRuntimeContext` / `RuntimePaths` boundary;
- make demo, pipeline, runtime runner, and validation paths consume context/path helpers;
- eliminate new direct `Path(__file__).parents[...]` root guesses outside wrappers/entrypoints;
- keep compatibility wrappers for existing scripts.

Gate:
- `scripts/run_security_contract_validation.py --include-pytest` passes;
- full pytest passes;
- public snapshot residue audit still has `blockers=0`.

### Stage 2 — Package-in-place before repo split

Goal: make `engine` installable/testable as a package while still inside Ravenclaw.

Recommended shape:
- keep existing script entrypoints for compatibility;
- add package metadata only after Stage 1 path cleanup;
- prefer a future public package name like `ravenclaw-runtime` or `ravenclaw-engine`, but avoid renaming every module in the first wave;
- add console entrypoints later for `ravenclaw-plan`, `ravenclaw-run-pipeline`, `ravenclaw-demo-bundle` only when imports are stable.

Gate:
- editable install works from a clean checkout;
- CI uses `pip install -e '.[dev]'`;
- no reliance on the live workspace layout for public validation.

### Stage 3 — Public API seam

Goal: define what downstream consumers are allowed to import.

Public-ish engine surfaces should be small:
- runtime task normalization and plan service contracts;
- policy decision/evaluation interfaces;
- prepared/approved execution spec builders;
- execution engine interface;
- replay/evaluation interfaces;
- SCLite adapter functions.

Private/internal surfaces stay private:
- auto-campaign runner internals;
- Logdash-specific projection glue;
- local persistence file layout;
- operator-specific state and runtime residue.

Gate:
- API smoke tests prove public imports without sys.path manipulation;
- Logdash consumes the API seam rather than deep file/module internals where practical.

### Stage 4 — Logdash as consumer

Goal: reduce Logdash coupling before external repo extraction.

Tasks:
- route Logdash state projections through service/helper APIs;
- keep direct file reads behind shared services;
- document engine-owned vs Logdash-owned state;
- preserve current UI behavior.

Gate:
- Logdash smoke/contract tests pass;
- runtime snapshot and operator truth tests pass.

### Stage 5 — Separate repository candidate

Goal: only after Stages 0–4, create a clean candidate tree.

Candidate tree should include:
- runtime engine package;
- tests for contract/policy/execution/pipeline/replay seams;
- dependency on `sclite`;
- no `memory/`, `reports/`, `logs/`, local state, Logdash DB, or operator-specific files;
- minimal docs explaining non-claims and integration boundary.

Ravenclaw main repo then becomes:
- app/control-plane/demo/reference workspace;
- dependency consumer of the engine package;
- owner of Logdash and Ravenclaw-specific policy/config defaults.

Gate:
- clean candidate install works;
- Ravenclaw consumes candidate package from local path or pinned Git ref;
- full Ravenclaw validation still passes.

## Immediate next development slice

The next concrete slice should be **Stage 0 + a small Stage 1 root/path fix wave**, not repo extraction.

Recommended first implementation tasks:
1. Generate/import inventory for `engine`, `logdash`, `scripts`, and `bin`.
2. Add a short report: `reports/engine-extraction-readiness-2026-05-06.md`.
3. Identify and fix the top 3 root/path assumptions that block package use.
4. Add tests around those assumptions.
5. Re-run full pytest and SCL validation.

## Success criterion

Engine extraction is ready for a separate repo only when Ravenclaw can run its public demo, SCL validation, pytest slices, and Logdash smoke using installed dependencies and explicit runtime context — without depending on hidden live-workspace layout or embedded contract-core copies.
