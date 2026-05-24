# ARCHITECTURE_OVERVIEW.md

This is the short architecture map for Ravenclaw.
Read this first if you want the shape of the system without the full production deep dive.

## One-line model

Ravenclaw is a governance-first runtime where planning, authorization, execution, and interpretation are deliberately separated.

## Core flow

`scope / operator input -> planner -> policy gate / auditor -> prepared execution spec -> approved execution spec -> execution engine -> analysis / qualification -> operator visibility`

The current public lifecycle/review path makes the governed handoff explicit as artifacts:

`runtime projection -> policy decision -> execution contract -> scoped execution ticket -> execution receipt -> evidence contract -> review bundle`

## Major components

### Planner
Turns operator input and scope into structured planning artifacts and runtime intent.
Its job is to propose and shape work, not to authorize arbitrary execution.

### Policy gate and auditor
Evaluate whether a proposed action is allowed under scope, tool, auth, and aggression constraints.
This is where governance is enforced before execution.

### Execution engine
Builds the final command invocation and runs it under policy and whitelist constraints.
This is the only layer that should construct final executable commands.

### Analysis and qualification
Interpret raw output into findings, evidence quality, and conservative operator-facing conclusions.
This layer is meant to reduce narrative drift and keep outputs tied to artifacts.

### Logdash
Operator-facing control plane for runtime visibility, control actions, state truth, findings, and related telemetry.

## Why the separation matters

Many weak autonomy systems collapse planning, permission, and execution into one loop.
That produces fast output, but often weak accountability.

Ravenclaw takes the opposite approach:
- the planner does not get unrestricted authority
- the executor does not invent goals
- the auditor does not become the executor
- the analysis layer should not fabricate success

This separation is a practical safety and quality measure, not only an architectural preference.

## Where governance actually lives

Governance in Ravenclaw is not only a README idea.
It shows up in:
- policy and whitelist surfaces
- scope and target validation
- approval semantics for sensitive actions
- execution-engine constraints
- artifact-oriented review and replay surfaces
- the draft Security Contract Layer, which names the reusable contract artifacts without claiming to be a new protocol

## Where operator approval enters

Sensitive or ambiguity-heavy actions should not flow straight from plan to execution.
Operator approval remains part of the model for elevated cases.
That is central to the system's intended trust posture.

## What this overview leaves out

This file does not try to list every module, state file, or runtime seam.
For the deeper production map, read:
- `ARCHITECTURE.md`
- `STATE_FILES.md`
- `engine/RUNTIME_MANIFEST.md`

## Short public takeaway

Ravenclaw is best understood as a bounded security-research runtime that tries to make autonomy more trustworthy by putting real structure between idea generation, approval, execution, and evidence interpretation.
In public form, this should be read as a governance-first runtime core and reference implementation for a small Security Contract Layer, with some deployment-specific operator reality intentionally left in a private overlay rather than bundled into the repository. OpenClaw, MCP, and A2A are potential later carriers for those contracts, not replacement protocols.
