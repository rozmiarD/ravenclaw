from __future__ import annotations

import sys
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
LOGDASH_DIR = ROOT / 'logdash'
if str(LOGDASH_DIR) not in sys.path:
    sys.path.insert(0, str(LOGDASH_DIR))

from api_planner import register_planner_api  # type: ignore
from api_runtime import register_runtime_api  # type: ignore
from api_supplemental import register_supplemental_api  # type: ignore


@pytest.mark.parametrize(
    ('register_fn', 'ctx'),
    [
        (
            register_runtime_api,
            {
                'STATE': {},
            },
        ),
        (
            register_planner_api,
            {
                'STATE': {},
            },
        ),
        (
            register_supplemental_api,
            {
                'STATE': {},
            },
        ),
    ],
)
def test_api_registration_reports_missing_context_keys(register_fn, ctx) -> None:
    app = Flask(__name__)
    with pytest.raises(KeyError) as exc:
        register_fn(app, ctx)
    assert str(exc.value.args[0]).startswith('Missing Logdash API context keys: ')
