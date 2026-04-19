# Logdash operator truth contracts

This is the short operator-facing reference for how Logdash runtime/control-plane truth should be interpreted in the current `1.0.0` hardening line.

## Scope
This document describes:
- operator control-path semantics
- restart/recovery truth expectations
- source/provenance labels for key fallback payloads

It does not redefine runtime snapshot schemas or broader engine internals.

## 1. Control-path semantics
`/api/campaign/control` is expected to expose real lifecycle semantics, not UI-only state toggles.

Operator-facing expectations:
- `start`
  - starts runtime only when a matching runtime plan exists for the selected campaign
  - if runtime is already alive for the selected campaign, returns a resumed/alive-style success rather than spawning a duplicate process
- `resume`
  - resumes a paused live runtime when one already exists
  - does not spawn a second runtime when an existing one is alive
- `pause`
  - is only truthful when there is a running runtime to pause
  - should not pretend success if no live runtime exists
- `stop`
  - terminates a live runtime when one exists
  - should remain truthful when runtime is already stopped or absent
- `activate-from-blueprint`
  - resets operator-visible state to `idle` for the newly activated campaign context rather than leaking prior run state forward

## 2. Restart and recovery truth
`logdash/services.refresh_runtime_state(...)` is the key recovery seam for reconstructing runtime truth from persisted control artifacts.

Current hardening expectations:
- stale PID files must be cleared when no live runtime exists
- paused persisted state must remain visible when the runtime is still alive
- explicit stopped state takes precedence over misleading recent-activity heuristics
- operator-visible runtime state should degrade to truthful `idle`/`paused`/`stopped` semantics instead of optimistic guesses

## 3. Source and ownership labels
Operator-visible payloads should distinguish snapshot-backed truth from normalized persisted-file truth and from explicit empty fallbacks.

Important labels in the current hardening line:
- `runtime_snapshot_source`
  - `snapshot` when selected-campaign snapshot data is present and applicable
  - `legacy` when the UI is using fallback/runtime-derived projections instead of matching selected snapshot truth
- queue payload `source`
  - `runtime_snapshot` when queue truth comes from snapshot-backed queue sections
  - `normalized_queue_state` when using normalized persisted queue-state files
  - `empty_selected_campaign_queue` when the selected campaign has no matching snapshot queue truth and the UI intentionally returns an empty fallback payload
- host-state payload `source`
  - `snapshot` when host truth is served from selected snapshot sections
  - `normalized_host_state_file` when host truth comes from normalized persisted host-state files
  - `missing_host_state` / `invalid_host_state` when file-backed host-state truth is absent or invalid
- planner runtime-plan payload `meta.source`
  - `snapshot` when selected snapshot plan metadata applies
  - `normalized_runtime_plan_meta` when fallback truth comes from normalized runtime-plan metadata files

## 4. Documentation rule
If a future change alters these semantics, update:
- tests covering the affected truth surface
- this reference doc
- `logdash/README.md` when operator interpretation changes materially

The goal is not just passing code. The goal is operator-visible truth that stays legible under normal use and during partial failure.
