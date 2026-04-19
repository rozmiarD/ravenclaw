from __future__ import annotations

import sys
from collections import defaultdict, deque
from pathlib import Path

ENGINE_DIR = str(Path(__file__).resolve().parents[1])
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from auto_campaign_queue import QueueCoordinator  # type: ignore


def test_queue_coordinator_enqueue_and_dequeue_semantics() -> None:
    followup_queue: list[dict] = []
    precision_queue: list[dict] = []
    host_rr: dict[str, deque] = defaultdict(deque)
    qc = QueueCoordinator(
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        host_rr=host_rr,
        host_success_count={},
        host_fail_count={},
    )

    task_a = {'objective': 'Probe A', 'target': 'https://api.example.com/a'}
    task_b = {'objective': 'Probe B', 'target': 'https://api.example.com/b'}
    task_c = {'objective': 'Probe C', 'target': 'https://auth.example.com/c'}

    qc.enqueue(task_a, high_priority=False)
    qc.enqueue(task_b, high_priority=True)
    qc.enqueue(task_c, high_priority=False)

    assert task_a['queue_lane'] == 'followup'
    assert task_b['queue_lane'] == 'precision'
    assert task_c['queue_lane'] == 'followup'
    assert precision_queue == [task_b]
    assert followup_queue == [task_a, task_c]

    assert qc.dequeue() == task_b
    next_task = qc.dequeue()
    assert next_task == task_a or next_task == task_c
    assert next_task not in followup_queue


def test_queue_coordinator_host_health_gate_only_blocks_deep_or_followup() -> None:
    qc = QueueCoordinator(
        followup_queue=[],
        precision_queue=[],
        host_rr=defaultdict(deque),
        host_success_count={'api.example.com': 1},
        host_fail_count={'api.example.com': 6},
    )

    assert qc.host_health_blocked('api.example.com', 'deep') is True
    assert qc.host_health_blocked('api.example.com', 'followup') is True
    assert qc.host_health_blocked('api.example.com', 'fast') is False


def test_queue_coordinator_can_requeue_front_without_losing_lane() -> None:
    followup_queue: list[dict] = []
    precision_queue: list[dict] = []
    host_rr: dict[str, deque] = defaultdict(deque)
    qc = QueueCoordinator(
        followup_queue=followup_queue,
        precision_queue=precision_queue,
        host_rr=host_rr,
        host_success_count={},
        host_fail_count={},
    )

    task = {'objective': 'Probe A', 'target': 'https://api.example.com/a'}
    qc.enqueue(task, high_priority=False)
    popped = qc.dequeue()
    assert popped == task
    assert followup_queue == []
    qc.requeue_front(popped)
    assert task['queue_lane'] == 'followup'
    assert followup_queue == [task]
    assert host_rr['api.example.com'][0] == task


def test_queue_coordinator_accepts_canonical_queue_lane_on_requeue() -> None:
    qc = QueueCoordinator(
        followup_queue=[],
        precision_queue=[],
        host_rr=defaultdict(deque),
        host_success_count={},
        host_fail_count={},
    )
    task = {'objective': 'Probe P', 'target': 'https://api.example.com/p', 'queue_lane': 'precision'}
    qc.requeue_front(task)
    assert qc.precision_queue == [task]
    popped = qc.dequeue()
    assert popped == task
    assert popped['queue_lane'] == 'precision'
