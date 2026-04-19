from __future__ import annotations

from typing import Callable


def build_queue_coordinator(*, build_queue_coordinator_fn: Callable[..., object], queue_coordinator_cls: Callable[..., object], followup_queue, precision_queue, host_rr, host_success_count, host_fail_count) -> object:
    return build_queue_coordinator_fn(
        queue_coordinator_cls=queue_coordinator_cls,
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        host_rr=host_rr,
        host_success_count=host_success_count,
        host_fail_count=host_fail_count,
    )
