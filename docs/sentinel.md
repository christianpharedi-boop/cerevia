# CEREVIA V1.1 Sentinel

CEREVIA Sentinel is a defensive extension above the frozen Evidence Core v1. The core continues to own immutable artifacts, provenance, identities, claims, graphs, and independent verification. Sentinel asks a different question:

> **Has anything about this chain changed, been substituted, revoked, replayed, or presented deceptively?**

## Defensive extensions

| Extension | Guarantee |
|---|---|
| Adversarial verifier | Runs systematic tampering scenarios and requires every attack to become `INVESTIGATE`. |
| Ed25519 attestation | A verifier can sign the bundle hash, specification hash, verifier identity, software identity, timestamp, and result. |
| Transparency log | Important events form an append-only hash-linked history without requiring blockchain infrastructure. |
| Revocation registry | A revoked source preserves history and propagates `AFFECTED / INVESTIGATE` status through dependent graph nodes. |

The V1.1 attack suite covers modified payloads, altered metadata, altered parents, substituted artifacts, removed ancestors, changed parameters, changed environments, altered claims, altered uncertainty, graph manipulation, stale execution identity, mismatched specifications, and partial bundles.

## Status boundary

`VERIFIED` means the serialized computational and evidence chain is internally intact. `QUALIFIED` means the scientific claim remains deliberately qualified. `not_estimated` means uncertainty was not estimated. `REVOKED` means a source or assertion has been withdrawn, while dependent findings become `AFFECTED / INVESTIGATE`. None of these statuses asserts scientific truth.

The initial Sentinel implementation deliberately does not add quorum infrastructure, blockchain storage, automated truth assessment, or an Observatory interface. Those are future application-layer possibilities, not changes to Evidence Core v1.
