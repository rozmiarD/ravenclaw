# Repository Publication Readiness Analysis — 2026-05-08

## Purpose

Historical record: this document captures the publication decision state on
2026-05-08. It is not the current package-chain truth source; use `README.md`,
`PUBLIC_STATUS.md`, `VALIDATION.md`, and `VERSION_ROADMAP.md` for current claims.

Status update: this note began as a readiness analysis. Since then, SCLite has been published as `sclite-core==0.2.1`, GovEngine has been published as `govengine==0.1.0`, and Ravenclaw public dependency metadata now consumes those package ranges instead of Git URL pins.

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

Current public direction is now:

```text
Ravenclaw -> govengine>=0.1,<0.2 -> sclite-core>=0.2.1,<0.3
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

### PyPI outcome

- Published as PyPI distribution `sclite-core==0.2.1`.
- Python import package remains `sclite`.
- Build, `twine check`, clean install, and package import verification passed before publication.
- The original distribution name `sclite` was not accepted by PyPI, so the neutral distribution name `sclite-core` was selected.

### Recommendation

Keep SCLite on `0.2.x` while the lifecycle contract remains pre-1.0 and use patch releases for packaging/docs fixes.

## GovEngine readiness

### Already strong

- Dedicated public repo exists.
- Package imports and standalone tests pass.
- GitHub Actions pytest exists.
- Architecture/API/validation/roadmap docs exist.
- Core API/runner/OODA surfaces now exist.
- Carrier adapters are explicitly deferred.

### PyPI outcome

- Published as `govengine==0.1.0`.
- Depends on `sclite-core>=0.2.1,<0.3`.
- Build, `twine check`, clean install, `pip check`, package import/version checks, and PyPI install verification passed before publication.
- API stability policy remains conservative and pre-1.0.

### Recommendation

Keep GovEngine on `0.1.x` until the public API boundary is hardened further and Ravenclaw package-consumption validation stays green.

## Ravenclaw readiness

### Already strong

- Public repo has broad docs: README, PUBLIC_STATUS, QUALITY_SIGNALS, VALIDATION, PUBLISHING, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG, version roadmap, public proof references.
- Security Contract validation receipt exists and passes.
- Public demo/proof artifacts are schema-backed.
- Repo consumes SCLite and GovEngine as explicit dependencies.

### Gaps / risks

- Ravenclaw now consumes `sclite-core` and `govengine` package ranges instead of Git URL pins, but it is still probably not the right first PyPI runtime package because it is a runtime/reference system with broader operational expectations.
- Public version is `0.10.0`, but historical changelog contains stronger old `1.0.0` language; existing docs already explain the truth-restaging, but future package metadata should keep that conservative posture.
- Packaging currently sets `packages = []` and `py-modules = []`, which is valid for repo metadata but not a useful installable runtime package.

### Recommendation

Keep Ravenclaw as the public reference repo for now. Defer Ravenclaw PyPI until:

1. the public install story is stable on package dependencies;
2. validation proves Ravenclaw consumes `sclite-core` and `govengine` cleanly;
3. a clear decision is made whether Ravenclaw should be a package, an app repo, or a source/demo distribution.

## Versioning recommendation

- **SCLite**: published as `sclite-core==0.2.1`; stay `0.2.x` for lifecycle candidate releases and use patch releases for publication/docs fixes.
- **GovEngine**: published as `govengine==0.1.0`; stay `0.1.x` while API/runner/OODA surfaces remain pre-alpha.
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

1. Validate Ravenclaw end-to-end against the PyPI package chain.
2. Keep Ravenclaw as a reference runtime/source distribution until package/app boundaries are clearer.
3. Only after package-consumption validation stays green, revisit adapter proposals in the documented OpenClaw -> MCP -> A2A order.
