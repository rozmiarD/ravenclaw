from __future__ import annotations

from typing import Callable


def build_main_precheck_hooks(*, build_main_precheck_hooks_fn: Callable[..., dict], precheck_skip_count_ref: list[int], flush_precheck_summary_fn: Callable[[], None], flush_dns_skip_summary_fn: Callable[[], None], flush_host_cooldown_summary_fn: Callable[[], None], flush_execution_gate_summary_fn: Callable[[], None]) -> dict:
    return build_main_precheck_hooks_fn(
        precheck_skip_count_ref=precheck_skip_count_ref,
        flush_precheck_summary_fn=flush_precheck_summary_fn,
        flush_dns_skip_summary_fn=flush_dns_skip_summary_fn,
        flush_host_cooldown_summary_fn=flush_host_cooldown_summary_fn,
        flush_execution_gate_summary_fn=flush_execution_gate_summary_fn,
    )
