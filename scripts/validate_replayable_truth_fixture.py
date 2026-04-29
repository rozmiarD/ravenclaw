#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / 'engine'
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from evaluation_bundle import validate_replay_bundle  # type: ignore
from evaluation_replay import replay_decision_bundle  # type: ignore

EXPECTED_TARGET_SUFFIXES = ('.example.com', 'example.com')


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise AssertionError(f'{path}: expected JSON object')
    return value


def _target_is_public_safe(target: str) -> bool:
    host = target.lower().removeprefix('https://').removeprefix('http://').split('/', 1)[0]
    return host == 'example.com' or host.endswith(EXPECTED_TARGET_SUFFIXES[0])


def _assert_public_safe_bundle(bundle: Mapping[str, Any]) -> None:
    run_identity = bundle.get('run_identity') if isinstance(bundle.get('run_identity'), dict) else {}
    target = str(run_identity.get('target') or '')
    if not _target_is_public_safe(target):
        raise AssertionError(f'unsafe replay target: {target!r}')
    execution = bundle.get('execution') if isinstance(bundle.get('execution'), dict) else {}
    if str(execution.get('mode') or '').lower() not in {'demo', 'dry-run', 'dry_run', ''}:
        raise AssertionError(f'unexpected replay execution mode: {execution.get("mode")!r}')
    payload = json.dumps(bundle, sort_keys=True).lower()
    forbidden_markers = ('password=', 'authorization:', 'bearer ', 'cookie:', 'set-cookie:', 'github_pat', 'api_key')
    leaked = [marker for marker in forbidden_markers if marker in payload]
    if leaked:
        raise AssertionError(f'forbidden marker(s) in replay fixture: {leaked!r}')


def validate_fixture(fixture_dir: Path) -> None:
    bundle_path = fixture_dir / 'replay_bundle.json'
    result_path = fixture_dir / 'replay_result.json'
    bundle = _load_json(bundle_path)
    expected_result = _load_json(result_path)
    normalized = validate_replay_bundle(bundle)
    _assert_public_safe_bundle(normalized)
    actual_result = replay_decision_bundle(normalized)
    if actual_result != expected_result:
        raise AssertionError('replay_result.json does not match deterministic replay output')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate the public-safe Replayable Truth Runtime fixture.')
    parser.add_argument('fixture_dir', nargs='?', default='examples/replayable-truth-runtime')
    args = parser.parse_args(argv)
    fixture_dir = Path(args.fixture_dir)
    validate_fixture(fixture_dir)
    print(f'replayable_truth_fixture_ok:{fixture_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
