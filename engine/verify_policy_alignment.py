#!/usr/bin/env python3
from __future__ import annotations

import yaml

from govengine.policy.core import ALLOWED_TOOLS, get_runtime_allowed_tools, get_runtime_brain_allowed_tools  # type: ignore
from contracts import get_contract_allowed_tools  # type: ignore
from paths import WORKSPACE
from tool_registry import get_execution_allowed_tools, get_planner_visible_tools, get_active_planner_profile_state  # type: ignore

WHITELIST_PATH = WORKSPACE / 'whitelist.yaml'


def load_whitelist_tools() -> tuple[set[str], set[str]]:
    if not WHITELIST_PATH.exists():
        raise FileNotFoundError(f'missing whitelist: {WHITELIST_PATH}')
    data = yaml.safe_load(WHITELIST_PATH.read_text(encoding='utf-8')) or {}
    cmds = data.get('allowed_commands', [])
    brain_cmds = data.get('brain_allowed_commands', [])
    if not isinstance(cmds, list):
        raise ValueError('whitelist.allowed_commands must be a list')
    if brain_cmds is not None and not isinstance(brain_cmds, list):
        raise ValueError('whitelist.brain_allowed_commands must be a list')
    allowed = {str(c).strip().lower() for c in cmds if str(c).strip()}
    brain_allowed = {str(c).strip().lower() for c in (brain_cmds or []) if str(c).strip()}
    return allowed, brain_allowed


def main() -> int:
    wl, brain_wl = load_whitelist_tools()
    reg_exec = {str(x).strip().lower() for x in get_execution_allowed_tools()}
    reg_core = {str(x).strip().lower() for x in get_planner_visible_tools('core')}
    active_profile = get_active_planner_profile_state()
    reg_active = {str(x).strip().lower() for x in get_planner_visible_tools(active_profile.get('active_profile') or 'core')}
    pc = {str(x).strip().lower() for x in ALLOWED_TOOLS}
    runtime_pc = {str(x).strip().lower() for x in get_runtime_allowed_tools()}
    pct = {str(x).strip().lower() for x in get_runtime_brain_allowed_tools(active_profile.get('active_profile') or 'core')}
    ctb = {str(x).strip().lower() for x in get_contract_allowed_tools(active_profile.get('active_profile') or 'core')}

    ok = True
    if wl != reg_exec:
        ok = False
        print('ERROR: whitelist.allowed_commands != tool_registry execution_allowed tools')
        print('  only_in_whitelist:', ', '.join(sorted(wl - reg_exec)) or '-')
        print('  only_in_registry:', ', '.join(sorted(reg_exec - wl)) or '-')

    if brain_wl != reg_core:
        ok = False
        print('ERROR: whitelist.brain_allowed_commands != tool_registry core planner tools')
        print('  only_in_whitelist_brain:', ', '.join(sorted(brain_wl - reg_core)) or '-')
        print('  only_in_registry_core:', ', '.join(sorted(reg_core - brain_wl)) or '-')

    if reg_exec != pc:
        ok = False
        print('ERROR: tool_registry execution tools != policy_core.ALLOWED_TOOLS')
        print('  only_in_registry:', ', '.join(sorted(reg_exec - pc)) or '-')
        print('  only_in_policy_core:', ', '.join(sorted(pc - reg_exec)) or '-')

    if reg_active != pct:
        ok = False
        print('ERROR: active tool_registry planner tools != policy_core runtime brain tools')
        print('  active_profile:', active_profile.get('active_profile'))
        print('  only_in_registry_active:', ', '.join(sorted(reg_active - pct)) or '-')
        print('  only_in_policy_core_brain:', ', '.join(sorted(pct - reg_active)) or '-')

    if pct != ctb:
        ok = False
        print('ERROR: policy_core runtime brain tools != contracts runtime brain allowlist')
        print('  only_in_policy_core_brain:', ', '.join(sorted(pct - ctb)) or '-')
        print('  only_in_contracts_brain:', ', '.join(sorted(ctb - pct)) or '-')

    if not ok:
        return 2

    print(
        f"OK: allowed={len(wl)} runtime_allowed={len(runtime_pc)} "
        f"brain_allowed_core={len(reg_core)} active_profile={active_profile.get('active_profile')} "
        f"brain_allowed_active={len(reg_active)}"
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
