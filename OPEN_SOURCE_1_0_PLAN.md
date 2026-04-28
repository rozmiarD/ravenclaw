# OPEN_SOURCE_1_0_PLAN.md

## Purpose

This document captures the high-level release-truth transition for Ravenclaw after the public truth reset.
It is intentionally strategic rather than implementation-heavy.

The key distinction is:
- the repository may already contain technically serious `1.0.0`-line hardening work in its history
- the **current public package/release signal** is intentionally restaged lower until the public story, boundary, and delivery posture are coherent enough to defend cleanly

---

## Current release-truth stance

The public package signal is currently restaged at **`0.10.0`**.
That is not a claim that the technical work regressed.
It is a claim that the **public artifact and release framing** should be more conservative than the strongest internal milestone language that appeared earlier.

Why:
- the public repo is strongest as a governance-first runtime core
- the public/private boundary needed to be made explicit
- the public delivery/demo path is still being elevated deliberately
- some readers were likely to overread `1.0.0` as a broader product/readiness claim than the public artifact can honestly support today

In other words:
this is a **truth-restaging move**, not a denial of prior hardening work.

---

## Recommended direction

The recommended direction is:

1. continue shaping Ravenclaw Runtime into the credible governance-first reference implementation,
2. harden the trusted execution/control anchor further,
3. improve public-safe delivery and demoability,
4. make the reusable direction explicit as a small Security Contract Layer backed by real runtime artifacts,
5. add stronger public proof-of-value through schema-validated demo traces,
6. treat OpenClaw, MCP, and A2A as later adapters/carriers rather than new protocols,
7. only then reconsider whether a public `1.0.x` signal is worth reasserting.

The goal is not simply to publish code.
The goal is to publish something coherent, trustworthy, and legible, where public proof comes before adapter promotion.

---

## Interpreting the earlier `1.0.0` line

The earlier `1.0.0` milestone language should now be read as evidence of a technically serious hardening tranche, especially around:
- operator control semantics
- restart/recovery truth
- provenance/source labeling
- release-quality operator truth docs

That historical work still matters.
But after the audit-driven truth reset, it should not automatically dictate the strongest current public package signal.

---

## What must be true before reasserting a public `1.0.x` signal

Before Ravenclaw should publicly signal `1.0.x` again, the repo should have all of the following in a cleaner, more defensible form:
- public positioning that does not overstate the product boundary
- an explicit and stable public-core/private-overlay boundary
- a stronger trusted-core / execution-safety story
- a public-safe delivery path that is easier to reproduce and explain
- a schema-validated contract proof trace showing scope/input -> policy -> approved execution -> dry-run receipt -> evidence summary
- proof-of-value and benchmark surfaces that are legible to skeptical external readers
- public credibility signals broad enough to support the maturity claim

Until then, the lower public release signal is more honest.

---

## Publication stance

The recommended default is to publish a serious public core or research shell, not necessarily every high-leverage internal capability.

That means:
- public release should maximize clarity, credibility, and long-term value
- private components may remain private if they are too sensitive, too environment-specific, or strategically premature to release
- package/release signaling should follow public-truth discipline, not just internal technical pride

---

## Short rule

Do not let the strongest historical milestone language become a permanent public claim if the public artifact no longer cleanly supports that reading.

Ravenclaw should earn any future `1.0.x` public signal by aligning:
- repo truth
- public boundary
- delivery reality
- trusted-core defensibility
- public proof surfaces
