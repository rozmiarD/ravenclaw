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
- approved execution shape
- dry-run execution
- operator-facing visibility

## Official demo path

### 1. Create a local environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2. Generate a planner artifact from the sample scope

```bash
python3 engine/plan_campaign.py \
  --scope-txt engine/planer/examples/sample_scope.txt \
  --flags-json '{"homelab": false}'
```

This demonstrates the planner entry surface and campaign-shaping path.

### 3. Run the governed pipeline in dry-run mode

```bash
python3 engine/run_pipeline.py \
  --task "Fetch the homepage and summarize visible technologies" \
  --target "https://example.com" \
  --dry-run
```

This demonstrates the governed single-task flow without claiming live execution.

What to look for:
- the task is shaped into a governed flow
- the runtime stays in dry-run mode
- output includes approval/execution structure rather than blind command execution

### 4. Start Logdash locally

```bash
cd logdash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py --port 9091
```

Then open:
- <http://127.0.0.1:9091>

This demonstrates the operator-facing control plane locally.

## Why this demo is the official one

This path is the smallest public-safe slice that is already real in the repo today.
It avoids pretending there is already a polished one-command deployment when that would be overstating current maturity.

## What this demo does not prove

This demo does **not** prove:
- full production deployment readiness
- polished public operator ergonomics
- broad toolchain integration completeness
- superiority over other systems by itself

It is a safe orientation/demo path, not the whole product story.

## Next maturity target

The next public-demo improvements should make this path easier and more cohesive, but without weakening its honesty or safety posture.