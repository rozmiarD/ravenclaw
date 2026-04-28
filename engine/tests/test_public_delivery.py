from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

import public_delivery as pd  # type: ignore


def test_resolve_delivery_profile_demo_defaults_to_local_public_safe() -> None:
    profile = pd.resolve_delivery_profile(explicit_mode='demo', env={})
    assert profile['runtime_mode'] == 'demo'
    assert profile['demo_mode'] is True
    assert profile['forced_dry_run'] is True
    assert profile['public_safe'] is True
    assert profile['operator_overlay_required'] is False
    assert profile['adapters']['brain']['mode'] == 'local'
    assert profile['adapters']['auditor']['mode'] == 'local'
    assert profile['adapters']['execution']['mode'] == 'mock'


def test_resolve_delivery_profile_local_defaults_to_external_brain_and_auditor() -> None:
    profile = pd.resolve_delivery_profile(explicit_mode='local', env={})
    assert profile['runtime_mode'] == 'local'
    assert profile['forced_dry_run'] is False
    assert profile['adapters']['brain']['mode'] == 'external'
    assert profile['adapters']['auditor']['mode'] == 'external'
    assert profile['adapters']['execution']['mode'] == 'local'
    assert profile['external_integrations_expected'] is True


def test_resolve_delivery_profile_honors_adapter_env_overrides() -> None:
    profile = pd.resolve_delivery_profile(
        explicit_mode='demo',
        env={
            'RAVENCLAW_BRAIN_ADAPTER': 'mock',
            'RAVENCLAW_AUDITOR_ADAPTER': 'external',
            'RAVENCLAW_EXECUTION_ADAPTER': 'mock',
        },
    )
    assert profile['adapters']['brain']['mode'] == 'mock'
    assert profile['adapters']['auditor']['mode'] == 'external'
    assert profile['adapters']['execution']['mode'] == 'mock'


def test_apply_delivery_profile_forces_demo_dry_run_and_config_overrides() -> None:
    args = argparse.Namespace(dry_run=False, objective='o', target='https://example.com')
    cfg = {
        'execution_mode': 'faithful',
        'experimental_payloads': True,
        'enable_analysis': True,
        'enable_light': True,
    }
    profile = pd.resolve_delivery_profile(explicit_mode='demo', env={})
    effective_args, effective_cfg, notes = pd.apply_delivery_profile_to_pipeline(args, cfg, delivery_profile=profile)
    assert args.dry_run is False
    assert effective_args.dry_run is True
    assert effective_cfg['execution_mode'] == 'normalized'
    assert effective_cfg['experimental_payloads'] is False
    assert effective_cfg['enable_analysis'] is False
    assert effective_cfg['enable_light'] is False
    assert effective_cfg['force_target_in_scope'] is True
    assert notes['dry_run_forced'] is True
    assert notes['runtime_mode'] == 'demo'
    assert notes['demo_scope_target'] is True
    assert len(notes['config_overrides']) >= 1
