# Public Core vs Private Overlay Boundary

This file explains the most important public-boundary truth about Ravenclaw:
the public repository is a **governance-first runtime core**, not a full dump of the operator's live security environment.

## Short version

Ravenclaw should be read as two related layers:
- **public core** — the architecture, contracts, policy surfaces, executor posture, Logdash control-plane logic, tests, docs, and bounded demo/dry-run paths that can be published safely
- **private overlay** — operator-specific models, deployment wiring, live credentials, local state, internal memory, host-specific setup, and environment-specific execution reality that should not be assumed to exist in the public repo

The public repo is meant to expose the system's governed runtime shape.
It is **not** meant to expose every high-leverage private or environment-specific capability.

## What belongs to the public core

The public core includes the parts of Ravenclaw that can be inspected, tested, and discussed safely as the durable architecture:
- front-door docs and public trust surfaces
- policy and whitelist surfaces
- execution-engine-first command construction model
- planner/runtime/auditor contracts that are publishable without exposing private operator reality
- Logdash operator-facing control and state truth logic
- tests, validation surfaces, and public-safe examples
- snapshot assembly and publication-boundary tooling

These are the parts that carry the public technical thesis.

## What belongs to the private overlay

The private overlay includes the parts that are real in operator use but are not part of the public-core promise:
- model/provider configuration that depends on external runtime setup
- operator-specific prompts, memory, bootstrap, persona, or account state
- live campaign data, credentials, cookies, and internal targets
- deployment-specific host wiring, secrets, service layout, and local helper state
- internal notes, generated runtime residue, and other live-workspace artifacts
- higher-leverage operational integrations that are too sensitive, too environment-specific, or strategically premature for public release

These are not "fake" just because they are not public.
They are simply outside the public artifact boundary.

## Why this boundary matters

Without an explicit boundary, readers can misread the repo in two different wrong ways:
- **overread it** as if the public tree is claiming to be a fully packaged autonomous offensive platform
- **underread it** as if anything not bundled publicly must be hand-wavy or fake

Both interpretations are wrong.

The public claim is narrower:
Ravenclaw is a serious governance-first security research runtime with a publishable core and a separate operator/private overlay reality.

## How to read `engine/brain.py`

`engine/brain.py` should be read as a **planner/brain adapter seam**, not proof that the full production planner stack is locally embedded in this file.

In public form, this seam is expected to:
- preserve the interface shape used by the governed runtime
- make the adapter/fallback behavior explicit
- avoid pretending that a remote model integration is a full local implementation

If the runtime is configured with a real external planner integration, that integration lives in the surrounding environment and runtime wiring.
If not, the public core should degrade honestly via deterministic or bounded fallback behavior.

## Public promise vs non-promise

### Public promise
The public repo aims to honestly expose:
- the system's architecture
- governance model
- execution-control posture
- operator-visible truth surfaces
- bounded demo/dry-run behavior
- validation and contract evidence

### Non-promise
The public repo does **not** promise:
- that every private deployment component is bundled here
- that local public checkout equals the operator's full live environment
- that all private model/runtime integrations are open-sourced
- that the repo is claiming a one-command production offensive stack

## Recommended interpretation

The best way to read Ravenclaw is:
- **as a public core**: a serious, inspectable, governance-first runtime and control-plane artifact
- **with a private overlay boundary**: some operational reality stays outside the public tree by design

That is not a weakness in itself.
The weakness would be pretending the boundary does not exist.
