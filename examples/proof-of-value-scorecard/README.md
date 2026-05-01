# Proof-of-Value Scorecard Example

This directory contains a committed public-safe example of the Ravenclaw proof-of-value scorecard.

Generate it from the repository root with:

```bash
python scripts/build_proof_of_value_scorecard.py . --check > examples/proof-of-value-scorecard/scorecard.json
python scripts/build_proof_of_value_scorecard.py . --format markdown --check > examples/proof-of-value-scorecard/scorecard.md
```

The scorecard checks whether the public evidence paths for Ravenclaw's governance/reviewability benchmark dimensions are present.

It does **not** claim live vulnerability discovery, production readiness, protocol-adapter completeness, or superior real-world outcomes by itself.
