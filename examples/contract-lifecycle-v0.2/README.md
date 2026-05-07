# SCLite v0.2 Contract Lifecycle Fixture

This fixture demonstrates the v0.2 lightweight cryptographic integrity model:
canonical SHA-256 artifact descriptors plus an ordered hash-linked chain manifest.

It is public-safe and dry-run only. It does not claim live vulnerability evidence,
legal authorization, signer identity, or runtime enforcement.

Validate the chain/lifecycle:

```bash
sclite validate-chain sclite/examples/contract-lifecycle-v0.2/artifact_chain_manifest.json
sclite verify-lifecycle sclite/examples/contract-lifecycle-v0.2/artifact_chain_manifest.json
```
