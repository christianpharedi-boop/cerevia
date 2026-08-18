# CEREVIA Evidence Core v1

CEREVIA V1.0 establishes a stable evidence core. The core is intentionally frozen at the architectural level so future domain work can extend it without redesigning the chain-of-custody primitives.

> **Verification of computation is not verification of truth.** CEREVIA verifies that a serialized evidence-to-claim chain is internally intact and that a qualified claim follows from declared computations under declared assumptions. It does not decide that the scientific hypothesis is true.

## Stable primitives

| Primitive | Core guarantee |
|---|---|
| Immutable artifacts | Payloads, metadata, and parameters cannot be mutated after admission. |
| Content identities | Artifact hashes include computational inputs, parents, parameters, environment, and software identity. |
| Provenance | Every derived artifact records its operation, parents, environment, timestamp, and creator. |
| Domain context | Neuroscience entities preserve study, participant, session, recording, event, and analysis meaning. |
| External interoperability | Real BIDS EEG, behavioral, and eye-tracking observations can be admitted without weakening the evidence core. |
| Reproducible execution | Analysis specifications declare exact inputs, methods, parameters, outputs, and environments. |
| Evidence graph | Dependencies, support paths, inference relations, claims, and invalidation closures are queryable. |
| Multimodal alignment | Independent observations are related only through explicit context- and timebase-validated alignment artifacts. |
| Inference | Computed results remain distinct from scientific claims. |
| Claims and uncertainty | Claims preserve assumptions, uncertainty, context, method, status, and exact evidence hashes. |
| Independent verification | A fresh process can verify the serialized source-to-finding chain and diagnose corruption. |

## Extension boundary

Future modules may add domain ontologies, source adapters, analysis methods, or user interfaces. They must treat the evidence core as an extension point rather than changing its identity rules, provenance semantics, claim qualification, or independent-verification contract.

The following are explicitly outside the frozen core: automated truth assessment, silent causal interpretation, unsupported uncertainty estimation, a database or dashboard, AI-generated scientific conclusions, and automatic addition of new modalities without an explicit interoperability contract.

## Release posture

The V1.0.0 tag marks the end of the foundation phase. Subsequent releases should answer where independently verifiable evidence infrastructure is useful in a domain, rather than adding features to the core merely for breadth.
