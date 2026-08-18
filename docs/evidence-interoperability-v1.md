# CEREVIA Evidence Interoperability Specification V1

This document defines the smallest contract a scientific domain adapter must satisfy to become a CEREVIA-compatible evidence producer. The specification is intentionally a **constitution**, not a domain framework. It defines custody, identity, lineage, verification, invalidation, and claim boundaries while leaving scientific payload meaning to the adapter.

## Conformance profile

A domain adapter declares an `EvidenceInteroperabilityProfile` containing the following fields:

| Field | Requirement |
|---|---|
| `domain` | Stable domain identifier such as `neuroscience`, `proteomics`, or `earthspace`. |
| `adapter_version` | Adapter implementation version, independent of the specification version. |
| `supported_artifact_types` | Artifact kinds the adapter emits. The profile must include `finding`. |
| `input_contract` | Human- and machine-readable description of accepted domain input. |
| `output_contract` | Declared serialized outputs, including artifacts, provenance, manifests, and findings. |
| `identity_semantics` | Statement that identifies how CEREVIA content identity is preserved. |
| `lineage_semantics` | Statement describing parent references and computational ancestry. |
| `verification_requirements` | Required shared checks, including serialized verification and invalidation behavior. |
| `source_artifact_id` | Stable raw/source evidence artifact used by the conformance suite. |
| `final_finding_id` | Stable qualified finding used by the conformance suite. |

Profiles are frozen dataclasses. The specification version is `1.0`; changing the universal fields or semantics requires a new specification version rather than silently changing an existing profile.

## Five universal contracts

### 1. Evidence Contract

Every adapter must emit independently identifiable evidence artifacts. An artifact has an immutable content identity derived from its artifact ID, kind, payload, metadata, operation, parameters, environment, software version, and parent content identities. The domain determines what the payload means; CEREVIA determines how it is identified and related.

### 2. Lineage Contract

Every derived artifact must identify the artifacts that produced it through parent artifact IDs. A verifier must be able to reconstruct the complete computational ancestry from serialized records. Opaque aggregate provenance is not conformant.

### 3. Verification Contract

A serialized bundle must independently verify without the original process state, original in-memory catalog, hidden execution state, or domain-specific verifier. Verification checks manifest integrity, specification identity, artifact content identities, parent closure, claim evidence hashes, role structure, uncertainty, execution identity, and graph identity.

### 4. Invalidation Contract

Every evidence dependency must have a computable downstream impact. Revoking `X` must identify affected nodes, claims, and findings. Unrelated domain findings must remain unaffected. Sentinel revocation and Observatory `impact_of()` provide the shared implementation of this contract.

### 5. Claim Contract

A claim must preserve evidence IDs and hashes, inference identity, hypothesis, statement, assumptions, uncertainty, experimental context, method, validation status, and computed result. A claim’s qualification records the relationship between declared computation and declared assumptions; it does not establish scientific truth.

> **Verification of computation is not verification of truth.**

## Conformance suite

The reusable suite checks artifact identity, immutable provenance, parent lineage, serialized verification, claim structure, uncertainty declaration, graph projection, selective invalidation, revocation propagation, Observatory queries, cross-domain composition, and fresh-file verification. The three reference adapters are the first conformant implementations:

| Adapter | Profile status |
|---|---|
| Neuroscience | Conformant |
| Proteomics | Conformant |
| Earth/Space | Conformant |
| Cross-domain composition | Conformant |

Run the proof with:

```bash
cd /home/ubuntu/cerevia
PYTHONPATH=. python3 examples/substrate_stress_tests/conformance_proof.py
```

## References

[1]: https://github.com/christianpharedi-boop/cerevia "CEREVIA source repository and reference implementation"
