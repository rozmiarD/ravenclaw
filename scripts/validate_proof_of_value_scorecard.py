#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / 'scripts'
ENGINE_DIR = ROOT / 'engine'
for path in (SCRIPTS_DIR, ENGINE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_proof_of_value_scorecard as scorecard_builder  # type: ignore


def validate_scorecard_file(path: Path) -> dict:
    scorecard = json.loads(path.read_text(encoding='utf-8'))
    scorecard_builder.validate_scorecard_schema(scorecard)
    if scorecard.get('artifact_type') != scorecard_builder.SCORECARD_ARTIFACT_TYPE:
        raise AssertionError('unexpected artifact_type')
    summary = scorecard.get('summary', {})
    if summary.get('status') != 'passed':
        raise AssertionError('scorecard summary.status must be passed')
    if summary.get('failed') != 0:
        raise AssertionError('scorecard summary.failed must be 0')
    if scorecard.get('scope', {}).get('live_target_execution') is not False:
        raise AssertionError('scorecard must not authorize live target execution')
    if scorecard.get('scope', {}).get('live_vulnerability_claim') is not False:
        raise AssertionError('scorecard must not claim live vulnerability evidence')
    for dimension in scorecard.get('dimensions', []):
        if dimension.get('status') != 'passed':
            raise AssertionError(f"dimension {dimension.get('id')} is not passed")
        if not dimension.get('non_claim'):
            raise AssertionError(f"dimension {dimension.get('id')} missing non_claim")
    return scorecard


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate a public-safe proof-of-value scorecard fixture.')
    parser.add_argument('path', nargs='?', default='examples/proof-of-value-scorecard/scorecard.json')
    args = parser.parse_args(argv)

    scorecard = validate_scorecard_file(Path(args.path))
    print(f"proof_of_value_scorecard_ok:{scorecard['summary']['dimension_count']}:{args.path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
