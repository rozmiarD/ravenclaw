# Replayable Truth Runtime fixture

This public-safe fixture shows Ravenclaw replaying a stored runtime decision without live target execution.

Files:

- `replay_bundle.json` — sanitized replay input bundle using `phase5-replay-bundle-v1`.
- `replay_result.json` — deterministic replay output produced from the bundle.

The fixture uses only `example.com` demo targets and does not contain credentials, cookies, raw live target output, or operator-local state.

Validate it with:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_replayable_truth_fixture.py examples/replayable-truth-runtime
```

The point is not to claim a live vulnerability. The point is to show that Ravenclaw can preserve enough runtime truth to replay governance-aware decisions offline.
