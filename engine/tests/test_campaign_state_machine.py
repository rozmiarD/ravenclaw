from __future__ import annotations

import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from campaign_state_machine import derive_family_state, derive_host_stage, derive_campaign_stage  # type: ignore


def test_campaign_state_machine_derives_family_host_and_campaign_states() -> None:
    family = derive_family_state(analysis_contract={'expected_signal_observed': 'partial'}, promising=True, host_state_band='healthy')
    host = derive_host_stage(promising=True, family_state=family, host_state_band='healthy')
    campaign = derive_campaign_stage(runs=[{'promising': True, 'analysis_contract': {'evidence_goal_met': 'no'}}])
    assert family == 'signal_found'
    assert host == 'validation'
    assert campaign == 'signal_validation'


def test_campaign_state_machine_exposes_exploitation_host_stage() -> None:
    host = derive_host_stage(promising=True, family_state='exploring', host_state_band='exploitation')
    assert host == 'exploitation'
