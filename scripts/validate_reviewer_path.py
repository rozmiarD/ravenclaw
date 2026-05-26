#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]

REVIEWER_TRUTH_DOCS = (
    "README.md",
    "INSTALL.md",
    "PUBLIC_STATUS.md",
    "VALIDATION.md",
    "REVIEWER_VALIDATION_GUIDE.md",
    "QUALITY_SIGNALS.md",
    "PROOF_OF_VALUE.md",
    "SECURITY_CONTRACT_LAYER.md",
    "REPLAYABLE_TRUTH_RUNTIME.md",
)

REQUIRED_REVIEWER_PATHS = (
    "PUBLIC_STATUS.md",
    "QUALITY_SIGNALS.md",
    "VALIDATION.md",
    "REVIEWER_VALIDATION_GUIDE.md",
    "PROOF_OF_VALUE.md",
    "SECURITY_CONTRACT_LAYER.md",
    "REPLAYABLE_TRUTH_RUNTIME.md",
    "references/public-safe-proof-walkthrough.md",
    "references/public-core-private-overlay-boundary.md",
    "references/public-validation-surface-index-v0.1.md",
    "references/public-snapshot-manifest-v0.1.md",
    "scripts/bootstrap_public_demo.sh",
    "scripts/validate_public_install.py",
    "scripts/validate_clean_public_install.py",
    "scripts/validate_package_runtime_boundary.py",
    "scripts/validate_openclaw_fixture_presenter.py",
    "scripts/list_public_validation_surfaces.py",
    "scripts/build_public_snapshot_manifest.py",
    "scripts/run_security_contract_validation.py",
    "scripts/run_pytest_slice.py",
    "bin/demo-bundle",
    "examples/openclaw-fixture-presenter/carrier_input.json",
    "examples/openclaw-fixture-presenter/presenter_packet.json",
    ".github/workflows/pytest.yml",
)

REQUIRED_REVIEWER_COMMANDS = (
    "./scripts/bootstrap_public_demo.sh scenario",
    "python scripts/validate_public_install.py --dev",
    "python scripts/validate_package_runtime_boundary.py",
    "python scripts/validate_openclaw_fixture_presenter.py",
    "python scripts/list_public_validation_surfaces.py --format json --check",
    "python scripts/run_security_contract_validation.py --include-pytest",
    "python scripts/build_public_snapshot_manifest.py . --format reviewer-report --check",
)

REQUIRED_CI_SLICES = (
    "contracts_policy",
    "auto_campaign",
    "runtime_core",
    "runtime_runner",
    "logdash",
    "misc_public",
)

FORBIDDEN_REVIEWER_CLAIMS = (
    "OpenClaw adapter is implemented",
    "MCP adapter is implemented",
    "A2A adapter is implemented",
    "complete public runtime package",
    "full PyPI runtime package",
    "production-ready runtime",
    "production ready runtime",
    "owns PKI",
    "owns KMS",
    "owns key-store",
    "owns trust-store",
)


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _pyproject() -> Mapping[str, object]:
    return tomllib.loads(_read("pyproject.toml"))["project"]


def _project_dependency(project: Mapping[str, object], name: str) -> str:
    prefix = f"{name}>="
    for dependency in project.get("dependencies", []):  # type: ignore[union-attr]
        text = str(dependency)
        if text.startswith(prefix):
            return text
    raise AssertionError(f"missing_dependency:{name}")


def _contains_expected(text: str, expected: str) -> bool:
    return expected in text or " ".join(expected.split()) in " ".join(text.split())


def missing_path_errors(paths: tuple[str, ...] = REQUIRED_REVIEWER_PATHS) -> list[str]:
    errors: list[str] = []
    for path in paths:
        if not (ROOT / path).exists():
            errors.append(f"reviewer_path_missing:{path}")
    return errors


def required_text_errors(text_by_path: Mapping[str, str]) -> list[str]:
    project = _pyproject()
    version = str(project["version"])
    govengine_dep = _project_dependency(project, "govengine")
    sclite_dep = _project_dependency(project, "sclite-core")

    required_by_path = {
        "REVIEWER_VALIDATION_GUIDE.md": (
            *REQUIRED_REVIEWER_COMMANDS,
            "does **not** authorize live target execution",
            "Protocol adapters such as OpenClaw, MCP, or A2A are complete",
            "not PKI, production identity proof, or key-management support",
        ),
        "VALIDATION.md": (
            "For a shorter reviewer-oriented path, see `REVIEWER_VALIDATION_GUIDE.md`.",
            "python scripts/validate_clean_public_install.py",
            "python scripts/run_pytest_slice.py --list",
            "python scripts/run_security_contract_validation.py --include-pytest",
            "Older proof-trace fixtures are migration/history material",
        ),
        "QUALITY_SIGNALS.md": (
            ".github/workflows/pytest.yml",
            "matrixed pytest slices",
            "public truth validation",
            "public helper smoke",
            "package dry-run",
            "ravenclaw-security==0.18.2",
            "package/runtime boundary",
        ),
        "PUBLIC_STATUS.md": (
            f"ravenclaw-security=={version}",
            "narrow public profile/readiness package",
            "full runtime remains source/reference",
        ),
        "README.md": (
            f"ravenclaw-security=={version}",
            govengine_dep,
            sclite_dep,
        ),
    }

    errors: list[str] = []
    for path, expected_fragments in required_by_path.items():
        text = text_by_path.get(path, "")
        for expected in expected_fragments:
            if not _contains_expected(text, expected):
                errors.append(f"{path}:missing_reviewer_truth:{expected}")
    return errors


def ci_truth_errors(
    workflow_text: str,
    quality_text: str,
    slices: tuple[str, ...] = REQUIRED_CI_SLICES,
) -> list[str]:
    errors: list[str] = []
    for slice_name in slices:
        if f"- {slice_name}" not in workflow_text:
            errors.append(f".github/workflows/pytest.yml:missing_pytest_slice:{slice_name}")
        if f"`{slice_name}`" not in quality_text:
            errors.append(f"QUALITY_SIGNALS.md:missing_ci_slice:{slice_name}")
    for expected in (
        "python scripts/validate_public_truth.py",
        "python scripts/validate_reviewer_path.py",
        "python scripts/validate_extraction_roadmap.py",
        "python scripts/validate_govengine_helper_boundary.py",
        "package-dry-run:",
        "python -m twine check dist/*",
        "python -m pip check",
    ):
        if expected not in workflow_text:
            errors.append(f".github/workflows/pytest.yml:missing_ci_gate:{expected}")
    if re.search(r"Current truth:\s*- runs on push and pull request\s*- uses Python 3\.11\s*- installs the minimal test dependencies\s*- runs `pytest -q`", quality_text):
        errors.append("QUALITY_SIGNALS.md:stale_pytest_q_ci_claim")
    return errors


def forbidden_claim_errors(text_by_path: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    for path, text in text_by_path.items():
        for claim in FORBIDDEN_REVIEWER_CLAIMS:
            if claim in text:
                errors.append(f"{path}:forbidden_reviewer_claim:{claim}")
    return errors


def collect_errors() -> list[str]:
    errors = missing_path_errors()
    text_by_path = {path: _read(path) for path in REVIEWER_TRUTH_DOCS}
    errors.extend(required_text_errors(text_by_path))
    errors.extend(
        ci_truth_errors(
            workflow_text=_read(".github/workflows/pytest.yml"),
            quality_text=text_by_path["QUALITY_SIGNALS.md"],
        )
    )
    errors.extend(forbidden_claim_errors(text_by_path))
    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    project = _pyproject()
    print(f"reviewer_path_ok:ravenclaw-security=={project['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
