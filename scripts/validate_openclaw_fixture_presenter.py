#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / 'examples' / 'openclaw-fixture-presenter'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ravenclaw.openclaw_readiness import (  # noqa: E402
    REQUIRED_NON_CLAIMS,
    build_openclaw_fixture_packet,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def validate_fixture_packet(
    carrier_input: Mapping[str, Any],
    expected_packet: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    packet = build_openclaw_fixture_packet(carrier_input)
    if packet != expected_packet:
        errors.append('fixture_packet_mismatch')
    if packet.get('artifact_type') != 'openclaw_fixture_presenter_packet':
        errors.append(f'unexpected_artifact_type:{packet.get("artifact_type")}')
    if packet.get('adapter_status') != 'not_implemented':
        errors.append(f'adapter_status_mismatch:{packet.get("adapter_status")}')
    if packet.get('fixture_mode') != 'presenter_only':
        errors.append(f'fixture_mode_mismatch:{packet.get("fixture_mode")}')
    if packet.get('non_claims') != list(REQUIRED_NON_CLAIMS):
        errors.append('required_non_claims_mismatch')
    rendered = json.dumps(packet, sort_keys=True)
    expected_rendered = json.dumps(expected_packet, sort_keys=True)
    for field in ('credentials', 'tokens', 'cookies', 'auth_headers', 'raw_stdout', 'raw_stderr'):
        value = carrier_input.get(field)
        if isinstance(value, str) and value and (value in rendered or value in expected_rendered):
            errors.append(f'sensitive_value_leaked:{field}')
    return errors


def collect_errors(example_dir: Path = EXAMPLE_DIR) -> list[str]:
    input_path = example_dir / 'carrier_input.json'
    packet_path = example_dir / 'presenter_packet.json'
    errors: list[str] = []
    if not input_path.exists():
        errors.append(f'missing_example:{input_path.relative_to(ROOT)}')
    if not packet_path.exists():
        errors.append(f'missing_example:{packet_path.relative_to(ROOT)}')
    if errors:
        return errors
    errors.extend(validate_fixture_packet(_load_json(input_path), _load_json(packet_path)))
    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print('openclaw_fixture_presenter_ok:adapter_status=not_implemented:fixture_mode=presenter_only')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
