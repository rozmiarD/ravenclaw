# Repository Publication Readiness Analysis — 2026-05-08

## Purpose

This note captures a publication-readiness pass across the current public repository family:

- **SCLite** — reusable Security Contract Layer lifecycle package.
- **GovEngine** — governed-execution helper/control package consuming SCLite.
- **Ravenclaw** — governance-first reference runtime and public proof implementation.

Adapters are intentionally deferred. The next work should make the repositories boringly publishable: versioning, changelogs, packaging, validation, release gates, and PyPI readiness.

## Recommended release order

1. **SCLite first**
   - Best PyPI candidate today.
   - Already has `version = "0.2.0"`, CLI entry points, empty runtime dependencies, packaged schemas/examples, changelog, and CI.
   - Publishing SCLite first unblocks normal package dependencies for GovEngine.

2. **GovEngine second**
   - Should depend on a released SCLite version range instead of a Git URL pin.
   - Needs a version decision before PyPI (`0.1.0` likely fits better than `0.0.0` after API/runner/OODA surfaces landed).
   - Needs package metadata/docs hardening before external users rely on it.

3. **Ravenclaw third / later**
   - Strong public runtime/proof repo, but likely not the first PyPI package.
   - Current value is as reference implementation, demo/proof surface, and governed runtime source.
   - PyPI packaging should wait until public delivery boundaries and dependency chain are stable.

## Cross-repo dependency goal

Current public direction should become:

```text
Ravenclaw -> GovEngine >=0.y,<0.z -> SCLite >=0.2,<0.3
```

Avoid long-term Git URL pins in public release metadata.

## SCLite readiness

### Already strong

- `pyproject.toml` has package metadata, `version = "0.2.0"`, classifiers, URLs, scripts, package data, and no runtime dependencies.
- `CHANGELOG.md` exists.
- CLI exists: `sclite` / `scl`.
- CI exists.
- README clearly states SCLite is not an executor/scanner/authorization authority.
- Publication checklist exists.

### Remaining before PyPI

- Add root `CONTRIBUTING.md`, `SECURITY.md`, and optionally `PUBLIC_STATUS.md` / `VALIDATION.md` for public-reader parity.
- Run build checks: `python -m build` and `twine check dist/*`.
- Verify PyPI name availability and project metadata rendering.
- Decide whether `0.2.0` is the first PyPI release or whether to cut `0.2.1` after publication docs are added.
- Create a release checklist that includes tag identity, changelog, CI, package build, TestPyPI dry run, then PyPI.

### Recommendation

SCLite should be the first PyPI release candidate after a short docs/build wave.

## GovEngine readiness

### Already strong

- Dedicated public repo exists.
- Package imports and standalone tests pass.
- GitHub Actions pytest exists.
- Architecture/API/validation/roadmap docs exist.
- Core API/runner/OODA surfaces now exist.
- Carrier adapters are explicitly deferred.

### Gaps found

- Version is still `0.0.0`.
- Runtime dependency points to SCLite by Git URL pin, which is not a good PyPI release posture.
- `CHANGELOG.md` was missing before this readiness wave.
- Root public hygiene docs were thin/missing: `CONTRIBUTING.md`, `SECURITY.md`, `PUBLIC_STATUS.md`, `PUBLISHING.md`.
- No build/twine release check documented as a normal gate.
- API stability policy needs to remain conservative and pre-1.0.

### Recommendation

Do not publish GovEngine to PyPI until SCLite is published. Then:

1. change dependency from Git URL to `sclite>=0.2,<0.3`;
2. choose initial external version, likely `0.1.0`;
3. run package build/twine checks;
4. tag only after Ravenclaw can consume the package candidate cleanly.

## Ravenclaw readiness

### Already strong

- Public repo has broad docs: README, PUBLIC_STATUS, QUALITY_SIGNALS, VALIDATION, PUBLISHING, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, version roadmap, public proof references.
- Security Contract validation receipt exists and passes.
- Public demo/proof artifacts are schema-backed.
- Repo consumes SCLite and GovEngine as explicit dependencies.

### Gaps / risks

- `pyproject.toml` still uses Git URL pins for SCLite and GovEngine.
- Ravenclaw is probably not the right first PyPI package because it is a runtime/reference system with broader operational expectations.
- Public version is `0.10.0`, but historical changelog contains stronger old `1.0.0` language; existing docs already explain the truth-restaging, but future package metadata should keep that conservative posture.
- Packaging currently sets `packages = []` and `py-modules = []`, which is valid for repo metadata but not a useful installable runtime package.

### Recommendation

Keep Ravenclaw as the public reference repo for now. Defer PyPI until:

1. SCLite and GovEngine are package-installable;
2. Ravenclaw's public install story no longer needs Git dependency pins;
3. a clear decision is made whether Ravenclaw should be a package, an app repo, or a source/demo distribution.

## Versioning recommendation

- **SCLite**: stay `0.2.x` for lifecycle candidate releases; use patch releases for publication/docs fixes.
- **GovEngine**: move from `0.0.0` to `0.1.0` when SCLite package dependency is available and the current API/runner/OODA surface is treated as the first external pre-alpha line.
- **Ravenclaw**: keep `0.10.x` until public install/delivery posture supports a stronger public claim.

## PyPI sequence

### Phase A — SCLite package release candidate

- Add missing public hygiene docs.
- Build locally.
- Run `twine check`.
- Test install from local wheel.
- Optional TestPyPI dry run.
- Tag/release only with explicit operator approval.

### Phase B — GovEngine package release candidate

- Replace SCLite Git dependency with a version range.
- Bump to `0.1.0` if approved.
- Build locally and run `twine check`.
- Test Ravenclaw against installed SCLite/GovEngine packages.
- Tag/release only with explicit operator approval.

### Phase C — Ravenclaw package/distribution decision

- Decide package vs app/source distribution.
- Remove Git pins once package dependencies are stable.
- Keep public-status and non-claim docs aligned.

## Adapter status

Adapters remain deferred. Do not start OpenClaw/MCP/A2A implementation until package boundaries and release hygiene are solid.

When adapter work resumes, default order remains:

1. OpenClaw contract carrier/presenter;
2. MCP policy-gated tool wrapper/gateway later;
3. A2A metadata/profile example last.

## Immediate next wave

Recommended next wave:

1. SCLite publication hygiene: add missing root docs and build/twine checks.
2. Decide SCLite first PyPI version (`0.2.0` vs `0.2.1`).
3. After SCLite is package-ready, prepare GovEngine `0.1.0` with normal SCLite dependency.
4. Only then revisit Ravenclaw dependency pins and public install docs.
