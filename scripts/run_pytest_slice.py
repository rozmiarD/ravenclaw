#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOTS = (Path("engine/tests"), Path("engine/planer/tests"), Path("tests"))
SLICE_ORDER = (
    "contracts_policy",
    "auto_campaign",
    "runtime_core",
    "runtime_runner",
    "logdash",
    "misc_public",
)


def _all_test_files() -> list[Path]:
    files: list[Path] = []
    for root in TEST_ROOTS:
        files.extend(sorted((REPO_ROOT / root).glob("test_*.py")))
    return sorted({path.resolve() for path in files})


def _starts(path: str, *prefixes: str) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def classify_test(path: Path) -> str:
    rel = path.resolve().relative_to(REPO_ROOT).as_posix()
    name = path.name

    if _starts(rel, "engine/tests/test_runtime_runner_"):
        return "runtime_runner"

    if _starts(rel, "engine/tests/test_runtime_", "tests/test_runtime_"):
        return "runtime_core"

    if "logdash" in name:
        return "logdash"

    if _starts(
        rel,
        "engine/tests/test_auto_campaign_",
        "engine/tests/test_campaign_",
    ) or rel == "tests/test_auto_campaign_controls.py":
        return "auto_campaign"

    if _starts(
        rel,
        "engine/tests/test_action_",
        "engine/tests/test_contracts_",
        "engine/tests/test_execution_contracts.py",
        "engine/tests/test_executor_v2.py",
        "engine/tests/test_pipeline_context_",
        "engine/tests/test_planer_scope_ingestion.py",
        "engine/tests/test_planner_intent_contract.py",
        "engine/tests/test_policy_",
        "engine/tests/test_request_decoration_contract_verifier.py",
        "engine/tests/test_run_pipeline_",
        "engine/tests/test_scope_exclusions.py",
        "engine/tests/test_semantic_",
        "engine/tests/test_signal_contract.py",
        "engine/tests/test_tool_registry",
        "engine/planer/tests/",
        "tests/test_policy_core.py",
        "tests/test_signal_contract_governance_disposition.py",
    ):
        return "contracts_policy"

    return "misc_public"


def collect_slice(slice_name: str) -> list[Path]:
    if slice_name == "all":
        return _all_test_files()
    files = [path for path in _all_test_files() if classify_test(path) == slice_name]
    if not files:
        raise SystemExit(f"unknown or empty slice: {slice_name}")
    return files


def describe_slices() -> list[tuple[str, int]]:
    files = _all_test_files()
    return [(name, sum(1 for path in files if classify_test(path) == name)) for name in SLICE_ORDER]


def run_pytest(files: Iterable[Path], extra_args: list[str]) -> int:
    rel_files = [path.resolve().relative_to(REPO_ROOT).as_posix() for path in files]
    cmd = [sys.executable, "-m", "pytest", "-q", *rel_files, *extra_args]
    return subprocess.call(cmd, cwd=REPO_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a stable Ravenclaw pytest slice")
    parser.add_argument("slice", nargs="?", default="all", choices=(*SLICE_ORDER, "all"))
    parser.add_argument("--list", action="store_true", help="list available slices and file counts")
    parser.add_argument("--show-files", action="store_true", help="print files selected for the slice and exit")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER, help="extra args passed through to pytest after '--'")
    args = parser.parse_args()

    if args.list:
        for name, count in describe_slices():
            print(f"{name}\t{count}")
        return 0

    files = collect_slice(args.slice)
    if args.show_files:
        for path in files:
            print(path.resolve().relative_to(REPO_ROOT).as_posix())
        return 0

    extra_args = list(args.pytest_args)
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]
    return run_pytest(files, extra_args)


if __name__ == "__main__":
    raise SystemExit(main())
