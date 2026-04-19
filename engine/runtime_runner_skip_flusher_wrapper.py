from __future__ import annotations

from typing import Callable


def make_skip_summary_flusher(*, make_skip_summary_flusher_fn: Callable[..., Callable[[bool], None]], flush_skip_summaries_fn: Callable[..., None], log_event_fn: Callable[..., None], precheck_skip_count_ref: list[int], precheck_skip_examples_ref: list[str], dns_skip_count_ref: dict[str, int], host_cooldown_skip_count_ref: dict[str, int], execution_gate_skip_count_ref: dict[str, int], execution_gate_skip_examples_ref: dict[str, list[str]]) -> Callable[[bool], None]:
    return make_skip_summary_flusher_fn(
        flush_skip_summaries_fn=flush_skip_summaries_fn,
        log_event_fn=log_event_fn,
        precheck_skip_count_ref=precheck_skip_count_ref,
        precheck_skip_examples_ref=precheck_skip_examples_ref,
        dns_skip_count_ref=dns_skip_count_ref,
        host_cooldown_skip_count_ref=host_cooldown_skip_count_ref,
        execution_gate_skip_count_ref=execution_gate_skip_count_ref,
        execution_gate_skip_examples_ref=execution_gate_skip_examples_ref,
    )
