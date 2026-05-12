# DEMO.md

This is the current official public-safe demo path for Ravenclaw.

It is intentionally narrow:
- local
- dry-run oriented
- no real-world targeting required
- focused on showing the governed flow, not maximum capability

## Goal of the demo

Show that Ravenclaw is structured around:
- planning
- policy/gating
- prepared and approved execution specs
- dry-run execution receipts
- evidence-oriented summaries
- operator-facing visibility

The current maturity target is a public-safe contract proof trace:

`scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence summary`

## Official demo path

### 1. Create a local environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2. Run the official demo entrypoint

Fastest supported local path:

```bash
./scripts/bootstrap_public_demo.sh demo
```

This uses the shared public bootstrap contract and then runs:
- sample scope planning
- governed dry-run pipeline execution

Equivalent direct entry:

```bash
bin/demo
```

If you only want to inspect the commands first:

```bash
./scripts/bootstrap_public_demo.sh demo-print
```

If you want reusable generated artifacts for review/demo sharing:

```bash
./scripts/bootstrap_public_demo.sh bundle
```

That writes the public demo bundle into `demo-output/`.

The bundle includes compact proof-trace artifacts such as policy decision, redacted prepared spec, approved execution spec, dry-run execution receipt, evidence summary, and bundle summary files. These artifacts are generated from the same demo-mode runtime path and are intended to stay sanitized and deterministic.

### Demo scenario: Ravenclaw -> GovEngine -> SCLite

For the shortest package-chain demo:

```bash
./scripts/bootstrap_public_demo.sh scenario
```

This generates the normal demo bundle, validates the SCLite v0.2 lifecycle artifacts, verifies the artifact-chain manifest, and records the GovEngine `security_profile` helper boundary in `demo-output/demo-scenario/demo_scenario_summary.json` and `.md`.

Use `RAVENCLAW_WORKSPACE=/path/to/ravenclaw` when running from a non-default checkout, and `DEMO_SCENARIO_OUTPUT_DIR=/tmp/ravenclaw-demo-scenario` to choose an output directory.

## Under the hood

The wrapper currently runs these bounded commands:

### Sample scope planning

```bash
python3 engine/plan_campaign.py \
  --scope-txt engine/planer/examples/sample_scope.txt \
  --flags-json '{"homelab": false}' \
  --runtime-mode demo
```

### Governed dry-run pipeline

```bash
python3 engine/run_pipeline.py \
  --objective "Fetch the homepage and summarize visible technologies" \
  --target "https://example.com" \
  --runtime-mode demo \
  --dry-run
```

What to look for:
- the task is shaped into a governed flow
- demo mode is explicit in output (`settings.runtime_mode`, `delivery_profile`, `integration_adapters`)
- the runtime stays in dry-run mode
- output includes approval/execution structure rather than blind command execution

In the current public demo contract:
- planner delivery is local/demo-safe
- auditor delivery is local/demo-safe
- execution delivery is explicit `mock` dry-run, surfaced in output rather than implied
- generated demo bundle artifacts come from that same contract, not from a separate canned fixture path

### Optional: start Logdash locally

```bash
./scripts/bootstrap_public_demo.sh logdash
```

### Optional: devcontainer / compose path

Devcontainer/Codespaces-style bring-up:
- open the repo with `.devcontainer/devcontainer.json`
- the post-create step runs `./scripts/bootstrap_public_demo.sh install`

Compose-based demo startup:

```bash
docker compose -f compose.demo.yaml run --rm demo
```

Compose-based generated bundle:

```bash
docker compose -f compose.demo.yaml run --rm demo-bundle
```

Compose-based Logdash:

```bash
docker compose -f compose.demo.yaml up logdash
```

Then open:
- <http://127.0.0.1:9091>

This demonstrates the operator-facing control plane locally.

## Why this demo is the official one

This path is the smallest public-safe slice that is already real in the repo today.
The wrapper now drives a real `RAVENCLAW_MODE=demo` path instead of only wrapping normal local commands, and the repo now includes bootstrap/devcontainer/compose convenience surfaces around that same contract. It still does not pretend Ravenclaw already has a polished production deployment story.

## What this demo does not prove

This demo does **not** prove:
- full production deployment readiness
- polished public operator ergonomics
- broad toolchain integration completeness
- superiority over other systems by itself

It is a safe orientation/demo path, not the whole product story.

## Next maturity target

The next public-demo improvements should keep making the contract proof trace more legible, schema-validated, and public-safe. Adapter promotion comes later: OpenClaw Skill first after contract proof, MCP later, and A2A security metadata/profile later as an example-first carrier. Ravenclaw should not present this as a new protocol.
