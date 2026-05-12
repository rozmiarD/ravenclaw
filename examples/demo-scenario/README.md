# Ravenclaw Demo Scenario

This is the public-safe, market-legible demo path for the current package chain:

```text
Ravenclaw reference runtime -> GovEngine security-profile helpers -> SCLite lifecycle validation
```

Run it from a local checkout:

```bash
./scripts/bootstrap_public_demo.sh scenario
```

Optional path controls:

```bash
RAVENCLAW_WORKSPACE=/path/to/ravenclaw \
DEMO_SCENARIO_OUTPUT_DIR=/tmp/ravenclaw-demo-scenario \
./scripts/bootstrap_public_demo.sh scenario
```

The demo generates `demo_scenario_summary.json` and `demo_scenario_summary.md` next to the normal public demo bundle artifacts.

## What it proves

- Ravenclaw can produce the local/demo-safe proof trace.
- GovEngine exposes the optional `govengine.security_profile` boundary for security-oriented helper discovery.
- SCLite validates every lifecycle artifact and verifies the hash-linked artifact-chain manifest.
- Execution remains dry-run/mock; no live target scanning occurs.

## Trace

```text
scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence contract -> artifact chain manifest
```

## Non-claims

This demo does **not** claim production deployment readiness, live execution authority, adapter completeness, raw evidence publication, or authorization to test third-party targets.
