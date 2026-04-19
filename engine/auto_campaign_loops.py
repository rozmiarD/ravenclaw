from __future__ import annotations

from typing import Callable, Any


def run_curated_loop(
    target_plan: list[dict],
    *,
    should_stop: Callable[[], bool],
    before_entry: Callable[[dict], None] | None,
    process_entry: Callable[[dict], None],
) -> None:
    for entry in target_plan:
        if should_stop():
            break
        if before_entry is not None:
            before_entry(entry)
        process_entry(entry)


def run_dynamic_loop(
    *,
    should_continue: Callable[[], bool],
    before_iteration: Callable[[], None] | None,
    select_task: Callable[[], Any],
    process_task: Callable[[Any], None],
) -> None:
    while should_continue():
        if before_iteration is not None:
            before_iteration()
        task = select_task()
        process_task(task)
