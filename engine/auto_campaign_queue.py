from __future__ import annotations

from collections import deque

from auto_campaign_targets import attack_family, host_from_target  # type: ignore


class QueueCoordinator:
    def __init__(
        self,
        followup_queue: list[dict],
        precision_queue: list[dict],
        host_rr: dict[str, deque],
        host_success_count: dict[str, int],
        host_fail_count: dict[str, int],
    ) -> None:
        self.followup_queue = followup_queue
        self.precision_queue = precision_queue
        self.host_rr = host_rr
        self.host_success_count = host_success_count
        self.host_fail_count = host_fail_count

    @staticmethod
    def _queue_lane(task: dict, default: str = 'followup') -> str:
        lane = str(task.get('queue_lane') or task.get('_queue_lane') or default).strip().lower()
        return lane if lane in {'followup', 'precision'} else default

    @classmethod
    def _apply_queue_lane(cls, task: dict, lane: str) -> None:
        normalized = cls._queue_lane({'queue_lane': lane}, default='followup')
        task['queue_lane'] = normalized
        task['_queue_lane'] = normalized

    def enqueue(self, task: dict, high_priority: bool = False) -> None:
        h = host_from_target(str(task.get('target') or ''))
        if high_priority:
            self._apply_queue_lane(task, 'precision')
            self.precision_queue.append(task)
        else:
            self._apply_queue_lane(task, 'followup')
            if h:
                self.host_rr[h].append(task)
            self.followup_queue.append(task)

    def requeue_front(self, task: dict) -> None:
        if not isinstance(task, dict):
            return
        lane = self._queue_lane(task)
        h = host_from_target(str(task.get('target') or ''))
        if lane == 'precision':
            if task not in self.precision_queue:
                self.precision_queue.insert(0, task)
            return
        if task not in self.followup_queue:
            self.followup_queue.insert(0, task)
        if h:
            q = self.host_rr[h]
            if task not in q:
                q.appendleft(task)

    def host_health_blocked(self, host: str, mode: str) -> bool:
        h = str(host or '')
        if not h:
            return False
        if str(mode).lower() not in {'deep', 'followup'}:
            return False
        succ = self.host_success_count.get(h, 0)
        fail = self.host_fail_count.get(h, 0)
        total = succ + fail
        if total < 6:
            return False
        fail_rate = fail / max(1, total)
        return fail_rate >= 0.75 and succ <= 1

    def dequeue(self) -> dict | None:
        if self.precision_queue:
            task = self.precision_queue.pop(0)
            if isinstance(task, dict):
                self._apply_queue_lane(task, 'precision')
            return task
        if self.followup_queue:
            for h in list(self.host_rr.keys()):
                q = self.host_rr.get(h)
                if q:
                    task = q.popleft()
                    try:
                        self.followup_queue.remove(task)
                    except Exception:
                        pass
                    if isinstance(task, dict):
                        self._apply_queue_lane(task, 'followup')
                    return task
            task = self.followup_queue.pop(0)
            if isinstance(task, dict):
                self._apply_queue_lane(task, 'followup')
            return task
        return None

    def reprioritize(self, runs: list[dict]) -> None:
        weights = self._dynamic_family_boost(runs)
        self.followup_queue.sort(
            key=lambda x: -float(weights.get(attack_family(str(x.get('objective') or ''), str(x.get('target') or '')), 1.0))
        )
        self.precision_queue.sort(
            key=lambda x: -float(weights.get(attack_family(str(x.get('objective') or ''), str(x.get('target') or '')), 1.0))
        )

    @staticmethod
    def _dynamic_family_boost(runs: list[dict]) -> dict[str, float]:
        fam = {'recon': 1.0, 'xss': 1.0, 'idor': 1.0, 'generic': 1.0}
        for r in runs[-120:]:
            if not isinstance(r, dict):
                continue
            f = attack_family(str(r.get('objective') or ''), str(r.get('target') or ''))
            if f not in fam:
                fam[f] = 1.0
            st = str(r.get('engine_status') or '').lower()
            fam[f] += 0.08 if st in {'success', 'ok'} else (-0.06 if st in {'failed', 'error', 'timeout'} else 0)
        for k, v in list(fam.items()):
            fam[k] = max(0.75, min(1.35, v))
        return fam
