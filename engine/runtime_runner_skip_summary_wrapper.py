from __future__ import annotations

from typing import Callable


def build_main_skip_summary_flushers(*, build_main_skip_summary_flushers_fn: Callable[..., dict], make_skip_summary_flusher_fn: Callable[..., Callable[[bool], None]], precheck_skip_count_ref: list[int], precheck_skip_examples: list[str], dns_skip_count: dict[str, int], host_cooldown_skip_count: dict[str, int], execution_gate_skip_count: dict[str, int], execution_gate_skip_examples: dict[str, list[str]]) -> dict:
    return build_main_skip_summary_flushers_fn(
        make_skip_summary_flusher_fn=make_skip_summary_flusher_fn,
        precheck_skip_count_ref=precheck_skip_count_ref,
        precheck_skip_examples=precheck_skip_examples,
        dns_skip_count=dns_skip_count,
        host_cooldown_skip_count=host_cooldown_skip_count,
        execution_gate_skip_count=execution_gate_skip_count,
        execution_gate_skip_examples=execution_gate_skip_examples,
    )
