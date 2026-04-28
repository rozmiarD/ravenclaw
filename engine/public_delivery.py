from __future__ import annotations

import argparse
import os
from typing import Any, Callable, Dict, Mapping, Tuple
from urllib.parse import urlparse

SUPPORTED_RUNTIME_MODES = {'demo', 'local', 'external'}
SUPPORTED_ADAPTER_MODES = {'mock', 'local', 'external'}


BrainRunner = Callable[[], Dict[str, Any]]
AuditorRunner = Callable[[], Dict[str, Any]]
ExecutionRunner = Callable[[bool], Dict[str, Any]]


SAFE_DEMO_HOSTS = {'example.com', 'www.example.com', 'localhost', '127.0.0.1', '::1'}


def normalize_runtime_mode(value: Any) -> str:
    raw = str(value or '').strip().lower()
    return raw if raw in SUPPORTED_RUNTIME_MODES else 'local'


def normalize_adapter_mode(value: Any, *, default: str) -> str:
    raw = str(value or '').strip().lower()
    return raw if raw in SUPPORTED_ADAPTER_MODES else str(default or 'local').strip().lower() or 'local'


def is_safe_demo_target(target: Any) -> bool:
    raw = str(target or '').strip()
    if not raw:
        return False
    parsed = urlparse(raw if '://' in raw else f'//{raw}')
    host = str(parsed.hostname or '').strip().lower()
    if not host:
        return False
    return host in SAFE_DEMO_HOSTS or host.endswith('.example.com')



def resolve_delivery_profile(*, explicit_mode: Any = '', env: Mapping[str, str] | None = None) -> Dict[str, Any]:
    env_map = env or os.environ
    runtime_mode = normalize_runtime_mode(explicit_mode or env_map.get('RAVENCLAW_MODE') or 'local')

    defaults = {
        'demo': {'brain': 'local', 'auditor': 'local', 'execution': 'mock'},
        'local': {'brain': 'external', 'auditor': 'external', 'execution': 'local'},
        'external': {'brain': 'external', 'auditor': 'external', 'execution': 'external'},
    }
    chosen_defaults = defaults.get(runtime_mode, defaults['local'])

    brain_mode = normalize_adapter_mode(env_map.get('RAVENCLAW_BRAIN_ADAPTER'), default=chosen_defaults['brain'])
    auditor_mode = normalize_adapter_mode(env_map.get('RAVENCLAW_AUDITOR_ADAPTER'), default=chosen_defaults['auditor'])
    execution_mode = normalize_adapter_mode(env_map.get('RAVENCLAW_EXECUTION_ADAPTER'), default=chosen_defaults['execution'])

    profile: Dict[str, Any] = {
        'runtime_mode': runtime_mode,
        'demo_mode': runtime_mode == 'demo',
        'public_safe': runtime_mode == 'demo',
        'operator_overlay_required': runtime_mode != 'demo',
        'forced_dry_run': runtime_mode == 'demo',
        'settings_overrides': {
            'execution_mode': 'normalized' if runtime_mode == 'demo' else '',
            'experimental_payloads': False if runtime_mode == 'demo' else None,
            'enable_analysis': False if runtime_mode == 'demo' else None,
            'enable_light': False if runtime_mode == 'demo' else None,
        },
        'adapters': {
            'brain': {
                'mode': brain_mode,
                'surface': 'planner',
                'implementation': (
                    'deterministic_demo_brain_action'
                    if runtime_mode == 'demo' and brain_mode == 'local'
                    else {
                        'local': 'fallback_brain_action',
                        'mock': 'fixed_mock_brain_action',
                        'external': 'runtime_agent_io.ask_json',
                    }.get(brain_mode, 'runtime_agent_io.ask_json')
                ),
            },
            'auditor': {
                'mode': auditor_mode,
                'surface': 'governance',
                'implementation': {
                    'local': 'deterministic_local_auditor',
                    'mock': 'fixed_mock_auditor',
                    'external': 'runtime_agent_io.ask_json',
                }.get(auditor_mode, 'runtime_agent_io.ask_json'),
            },
            'execution': {
                'mode': execution_mode,
                'surface': 'executor',
                'implementation': {
                    'local': 'ExecutionEngine.execute_approved_spec',
                    'mock': 'mock_execution_result',
                    'external': 'external_execution_adapter_not_implemented',
                }.get(execution_mode, 'ExecutionEngine.execute_approved_spec'),
            },
        },
    }
    profile['external_integrations_expected'] = any(
        str(info.get('mode') or '') == 'external'
        for info in (profile.get('adapters') or {}).values()
        if isinstance(info, dict)
    )
    return profile


def apply_delivery_profile_to_pipeline(
    args: argparse.Namespace,
    cfg: Dict[str, Any],
    *,
    delivery_profile: Dict[str, Any],
) -> Tuple[argparse.Namespace, Dict[str, Any], Dict[str, Any]]:
    effective_args = argparse.Namespace(**vars(args))
    effective_cfg = dict(cfg or {})
    notes: Dict[str, Any] = {
        'runtime_mode': str(delivery_profile.get('runtime_mode') or 'local'),
        'dry_run_forced': False,
        'config_overrides': [],
        'demo_scope_target': False,
    }

    if delivery_profile.get('forced_dry_run'):
        if not bool(getattr(effective_args, 'dry_run', False)):
            notes['dry_run_forced'] = True
        effective_args.dry_run = True

    overrides = delivery_profile.get('settings_overrides') if isinstance(delivery_profile.get('settings_overrides'), dict) else {}
    for key, value in overrides.items():
        if key == 'force_target_in_scope':
            continue
        if value in (None, ''):
            continue
        if effective_cfg.get(key) != value:
            notes['config_overrides'].append({'key': key, 'before': effective_cfg.get(key), 'after': value})
        effective_cfg[key] = value

    if bool(delivery_profile.get('demo_mode')) and is_safe_demo_target(getattr(effective_args, 'target', '')):
        if effective_cfg.get('force_target_in_scope') is not True:
            notes['config_overrides'].append({'key': 'force_target_in_scope', 'before': effective_cfg.get('force_target_in_scope'), 'after': True})
        effective_cfg['force_target_in_scope'] = True
        notes['demo_scope_target'] = True

    effective_args.runtime_mode = str(delivery_profile.get('runtime_mode') or 'local')
    return effective_args, effective_cfg, notes


def run_brain_adapter(
    *,
    delivery_profile: Dict[str, Any],
    external_runner: BrainRunner,
    local_runner: BrainRunner,
    mock_runner: BrainRunner,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    adapter = ((delivery_profile.get('adapters') or {}).get('brain') or {}) if isinstance((delivery_profile.get('adapters') or {}).get('brain'), dict) else {}
    mode = str(adapter.get('mode') or 'external')
    if mode == 'local':
        return local_runner(), {'mode': mode, 'source': 'local_adapter'}
    if mode == 'mock':
        return mock_runner(), {'mode': mode, 'source': 'mock_adapter'}
    return external_runner(), {'mode': 'external', 'source': 'external_adapter'}


def run_auditor_adapter(
    *,
    delivery_profile: Dict[str, Any],
    external_runner: AuditorRunner,
    local_runner: AuditorRunner,
    mock_runner: AuditorRunner,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    adapter = ((delivery_profile.get('adapters') or {}).get('auditor') or {}) if isinstance((delivery_profile.get('adapters') or {}).get('auditor'), dict) else {}
    mode = str(adapter.get('mode') or 'external')
    if mode == 'local':
        return local_runner(), {'mode': mode, 'source': 'local_adapter'}
    if mode == 'mock':
        return mock_runner(), {'mode': mode, 'source': 'mock_adapter'}
    return external_runner(), {'mode': 'external', 'source': 'external_adapter'}


def run_execution_adapter(
    *,
    delivery_profile: Dict[str, Any],
    dry_run: bool,
    local_runner: ExecutionRunner,
    mock_runner: ExecutionRunner,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    adapter = ((delivery_profile.get('adapters') or {}).get('execution') or {}) if isinstance((delivery_profile.get('adapters') or {}).get('execution'), dict) else {}
    mode = str(adapter.get('mode') or 'local')
    effective_dry_run = bool(dry_run or delivery_profile.get('forced_dry_run', False))
    if mode == 'mock':
        return mock_runner(effective_dry_run), {'mode': mode, 'source': 'mock_adapter', 'effective_dry_run': effective_dry_run}
    if mode == 'external':
        raise RuntimeError('execution_adapter_not_implemented:external')
    return local_runner(effective_dry_run), {'mode': 'local', 'source': 'local_adapter', 'effective_dry_run': effective_dry_run}
