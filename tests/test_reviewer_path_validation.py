from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_reviewer_path.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("ravenclaw_validate_reviewer_path", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reviewer_path_validator_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert proc.stdout.strip() == "reviewer_path_ok:ravenclaw-security==0.18.3"


def test_reviewer_path_validator_catches_stale_pytest_q_ci_claim() -> None:
    validator = _load_validator()

    errors = validator.ci_truth_errors(
        workflow_text=(
            "python scripts/validate_public_truth.py\n"
            "python scripts/validate_reviewer_path.py\n"
            "python scripts/validate_extraction_roadmap.py\n"
            "python scripts/validate_govengine_helper_boundary.py\n"
            "package-dry-run:\n"
            "python -m twine check dist/*\n"
            "python -m pip check\n"
            "- contracts_policy\n"
            "- auto_campaign\n"
            "- runtime_core\n"
            "- runtime_runner\n"
            "- logdash\n"
            "- misc_public\n"
        ),
        quality_text=(
            "Current truth:\n"
            "- runs on push and pull request\n"
            "- uses Python 3.11\n"
            "- installs the minimal test dependencies\n"
            "- runs `pytest -q`\n"
            "`contracts_policy` `auto_campaign` `runtime_core` "
            "`runtime_runner` `logdash` `misc_public`"
        ),
    )

    assert errors == ["QUALITY_SIGNALS.md:stale_pytest_q_ci_claim"]


def test_reviewer_path_validator_catches_forbidden_adapter_claim() -> None:
    validator = _load_validator()

    errors = validator.forbidden_claim_errors({
        "README.md": "OpenClaw adapter is implemented for production-ready runtime",
    })

    assert errors == [
        "README.md:forbidden_reviewer_claim:OpenClaw adapter is implemented",
        "README.md:forbidden_reviewer_claim:production-ready runtime",
    ]


def test_reviewer_path_validator_catches_missing_required_command() -> None:
    validator = _load_validator()

    errors = validator.required_text_errors({
        "REVIEWER_VALIDATION_GUIDE.md": "python scripts/validate_public_install.py --dev",
        "VALIDATION.md": "For a shorter reviewer-oriented path, see `REVIEWER_VALIDATION_GUIDE.md`.",
        "QUALITY_SIGNALS.md": ".github/workflows/pytest.yml matrixed pytest slices public truth validation public helper smoke package dry-run ravenclaw-security==0.18.3",
        "PUBLIC_STATUS.md": "ravenclaw-security==0.18.3 narrow public profile/readiness package full runtime remains source/reference",
        "README.md": "ravenclaw-security==0.18.3 govengine>=0.12.2a0,<0.13 sclite-core>=1.0.1,<1.1",
    })

    assert any(
        error
        == "REVIEWER_VALIDATION_GUIDE.md:missing_reviewer_truth:./scripts/bootstrap_public_demo.sh scenario"
        for error in errors
    )
