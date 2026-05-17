#!/usr/bin/env python3
from __future__ import annotations

from govengine.tool_registry import (
    get_all_planner_visible_tools,
    get_capability_catalog,
    get_capability_tool_coverage,
    get_execution_allowed_tools,
    get_family_tool_coverage,
    get_planner_visible_tools,
    get_profile_catalog,
    get_task_family_catalog,
    get_tool_catalog,
)


def main() -> int:
    tools = get_tool_catalog()
    profiles = get_profile_catalog()
    execution_tools = set(get_execution_allowed_tools())
    planner_any = set(get_all_planner_visible_tools())
    executor_only_declared = sorted([
        name for name in execution_tools
        if not (tools.get(name) or {}).get('planner_profiles')
    ])
    shadow_execution_only = sorted([
        name for name in executor_only_declared
        if str((tools.get(name) or {}).get('category') or '') not in {'operator_support'}
    ])
    missing_installed = sorted([name for name, meta in tools.items() if name in execution_tools and not bool(meta.get('installed', False))])

    print(
        'tools={} execution_allowed={} planner_visible_any={} executor_only_declared={} shadow_execution_only={} missing_installed={}'.format(
            len(tools), len(execution_tools), len(planner_any), len(executor_only_declared), len(shadow_execution_only), len(missing_installed)
        )
    )

    for profile in profiles:
        planner_tools = get_planner_visible_tools(profile)
        family_coverage = get_family_tool_coverage(profile, planner_only=True)
        uncovered_families = sorted([fam for fam, names in family_coverage.items() if not names])
        capability_coverage = get_capability_tool_coverage(profile, planner_only=True)
        uncovered_capabilities = sorted([cap for cap, names in capability_coverage.items() if not names])
        print(
            'PROFILE {} planner_visible={} families_covered={}/{} uncovered_families={} capabilities_covered={}/{} uncovered_capabilities={}'.format(
                profile,
                len(planner_tools),
                len(family_coverage) - len(uncovered_families),
                len(family_coverage),
                len(uncovered_families),
                len(capability_coverage) - len(uncovered_capabilities),
                len(capability_coverage),
                len(uncovered_capabilities),
            )
        )
        for fam in uncovered_families[:20]:
            print('  UNCOVERED_FAMILY', profile, fam)
        for cap in uncovered_capabilities[:20]:
            print('  UNCOVERED_CAPABILITY', profile, cap)

    for tool in executor_only_declared[:100]:
        meta = tools.get(tool) or {}
        print('EXECUTOR_ONLY_DECLARED', tool, 'category=' + str(meta.get('category') or 'unknown'))
    for tool in shadow_execution_only[:100]:
        meta = tools.get(tool) or {}
        print('SHADOW_EXECUTION_ONLY', tool, 'category=' + str(meta.get('category') or 'unknown'))
    for tool in missing_installed[:100]:
        meta = tools.get(tool) or {}
        print('MISSING_INSTALLED', tool, 'category=' + str(meta.get('category') or 'unknown'))

    empty_capability_defs = sorted([name for name, meta in get_capability_catalog().items() if not meta])
    if empty_capability_defs:
        for name in empty_capability_defs:
            print('EMPTY_CAPABILITY_DEF', name)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
