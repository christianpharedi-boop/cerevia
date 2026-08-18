# CEREVIA V0.5 Evidence Graph

CEREVIA V0.5 projects the linear artifact provenance chain and neuroscience ontology into a pure in-memory directed evidence graph. It introduces no GUI, database, cloud service, or AI layer.

## Graph model

| Node | Purpose |
|---|---|
| Study, Participant, Session, Recording, Event | Experimental context. |
| Artifact, Transformation | Immutable data and the operation that generated it. |
| Feature, Analysis, Finding | Scientific computations and claims. |

| Edge | Direction |
|---|---|
| `GENERATED_BY` | Artifact → Transformation. |
| `DERIVED_FROM` | Child artifact → parent artifact. |
| `RECORDED_DURING` | Recording or event → session/recording context. |
| `ASSOCIATED_WITH` | Context or computational entity → related evidence. |
| `ANALYZED_BY` | Analysis → feature. |
| `SUPPORTS` | Analysis or evidence → finding. |

The graph is a projection, not an alternative source of truth. Artifact content hashes, parent identities, catalog validation, and manifest verification remain authoritative.

## Queries

`supports_finding(finding_id)` traverses from a finding through supporting analyses and upstream artifacts. `findings_depending_on(node_id)` finds all downstream Finding nodes affected by a source. `invalidate(node_id)` computes the non-mutating dependency closure for a hypothetical invalidation. The graph itself is immutable by convention at the query boundary; no query silently edits catalog state.

The evidence manifest now contains `evidence_graph`, `evidence_graph_hash`, and the existing manifest hash. The graph hash is deterministic for the graph content, while the manifest hash continues to cover the full audit record.

The V0.5 real-data example projects the complete analysis artifact chain generated from OpenNeuro ds003810 into a graph and reports graph node count, edge count, support coverage, and invalidation coverage.
