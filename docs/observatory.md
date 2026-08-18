# CEREVIA V1.2 Observatory

CEREVIA Observatory is a **read-only query layer** over existing evidence records. It observes manifests, evidence graphs, independent verification results, Sentinel attestations, revocations, and transparency-log history. It does not rewrite artifacts, mutate graph state, issue attestations, revoke sources, or decide scientific truth.

> **The Observatory may interpret the record, but it is never an authority over the record.**

## Contract surface

| Query | Purpose |
|---|---|
| `get_finding()` | Returns a finding, its claim reference, current integrity result, and current status. |
| `get_lineage()` | Returns the deterministic path from a finding through its upstream computational and evidentiary dependencies. |
| `get_supporting_evidence()` | Returns the claim artifact and the exact evidence identifiers and declared content hashes supporting it. |
| `get_verification()` | Returns independent verification checks, failures, and Sentinel status. |
| `get_attestations()` | Returns serialized cryptographic attestations associated with the observed bundle. |
| `get_revocations()` | Returns source revocations affecting a subject or its dependency closure. |
| `get_history()` | Returns transparency and revocation events, optionally filtered by an ISO-8601 `as_of` timestamp. |
| `impact_of()` | Computes the downstream invalidation closure and affected findings for an artifact. |

## Temporal semantics

`get_history(as_of=...)` answers what was recorded by the supplied timestamp. It does not retroactively rewrite the current verification result. This makes historical status and current status separate, explicit queries.

## Read-only semantics

`ObservatorySnapshot` deep-copies all inputs at construction and returns copies from query methods. The graph is reconstructed from the serialized manifest, allowing an independent process to query a self-contained bundle without the original process state. No Observatory method mutates the bundle, graph, attestation, transparency log, or revocation registry.

## Domain neutrality

The Observatory does not introduce neuroscience-specific query semantics. Domain adapters remain responsible for creating ontology and artifact records; Observatory exposes the same contracts for neuroscience, proteomics, Earth science, and future domains.
