# GovEngine Remote Publication Report — 2026-05-08

Status: remote created and Ravenclaw consumption branch updated locally before push.

## Remote

- Repo: `https://github.com/rozmiarD/GovEngine`
- Visibility: public
- Owner account: `rozmiarD` / Krzysztof Probola
- GovEngine commit consumed by Ravenclaw: `ece11b81abe804fd1677bd20f69567cf5ce7e9bb`

## Ravenclaw branch update

The Ravenclaw GovEngine migration branch now treats GovEngine as an external git dependency instead of packaging the in-tree `govengine/` directory.

Updated `pyproject.toml` dependency:

```toml
govengine @ git+https://github.com/rozmiarD/GovEngine.git@ece11b81abe804fd1677bd20f69567cf5ce7e9bb
```

The public snapshot assembly no longer copies an in-tree `govengine/` directory; Ravenclaw remains the reference runtime and consumes GovEngine as a package.

## Boundary retained

- GovEngine owns reusable governed-execution helpers.
- Ravenclaw owns Logdash, public snapshot tooling, runtime/demo UX, and concrete runtime integration.
- Live subprocess execution remains outside GovEngine for now.

## Validation after remote dependency pin

Validation used a fresh virtualenv and installed Ravenclaw with the public GovEngine git dependency. Observed import source:

```text
govengine_import_path=/tmp/ravenclaw-govengine-remote-venv2/lib/python3.13/site-packages/govengine/__init__.py
```

Checks passed:

- focused GovEngine/Ravenclaw compatibility tests, including executor v2: `27 passed, 1 skipped`;
- `scripts/run_security_contract_validation.py --include-pytest --format markdown`;
- assembled public snapshot residue audit: `blockers=0`;
- snapshot does not contain an in-tree `govengine/` directory.
