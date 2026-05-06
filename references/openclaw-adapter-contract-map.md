# OpenClaw Adapter Contract Map

Status: docs/contracts-only adapter-prep note. This is not an adapter implementation.

## Purpose

Map how a future OpenClaw carrier could consume the Ravenclaw Security Contract Layer without changing the canonical proof trace or bypassing runtime governance.

Canonical trace:

`scope/input -> policy decision -> prepared execution spec -> approved execution spec -> dry-run execution receipt -> evidence summary`

## Non-goals

- No OpenClaw Skill/plugin implementation is introduced here.
- No MCP/A2A adapter work is introduced here.
- No live target execution is authorized by this document.
- No replacement protocol claim is made; OpenClaw is treated as a future carrier for existing contracts.

## Candidate responsibilities

A future OpenClaw carrier should only bridge already-defined contract boundaries:

1. **Scope/input intake**
   - Accept operator-scoped task input.
   - Preserve scope metadata and explicit dry-run/public-safe flags.
   - Reject or pause on missing scope authority.

2. **Policy decision handoff**
   - Call or embed Ravenclaw policy evaluation through a stable boundary.
   - Preserve `decision`, `reason_code`, `approval_required`, and constraints.
   - Never reinterpret a rejected policy decision as executable.

3. **Prepared execution spec rendering**
   - Build a prepared spec from approved, scoped input only through Ravenclaw-owned helpers.
   - Keep redaction as a mandatory step before public or conversational display.
   - Avoid letting an LLM construct trusted shell commands directly.

4. **Approved execution spec handoff**
   - Pass only audited/approved execution specs to the execution boundary.
   - Preserve command authority: final commands remain constructed by the execution engine/guarded runtime, not by the carrier.

5. **Dry-run execution receipt capture**
   - Capture execution receipts as structured artifacts.
   - Preserve `dry_run`, runtime mode, return status, and provenance.
   - Do not convert dry-run proof into live-vulnerability evidence claims.

6. **Evidence summary presentation**
   - Render sanitized summaries for the operator.
   - Distinguish local proof receipts from public snapshot state and from live findings.
   - Keep raw stdout/stderr, tokens, cookies, workspace paths, and private state out of public output.

## Required gates before implementation

Before implementing this carrier, satisfy `references/carrier-readiness-checklist.md`:

- schema stability reviewed;
- redaction contract reviewed;
- command authority boundary reviewed;
- public snapshot residue audit green;
- validation receipt path green;
- non-claims preserved in public docs.

## Current status

This map is a planning artifact only. Ravenclaw Runtime remains the governed reference/proof implementation.
