# CEREVIA V1.5 Cross-Domain Evidence Interoperability

V1.5 composes independently produced neuroscience, proteomics, and Earth/Space evidence into one claim chain without inventing a cross-domain provenance language.

> **The domains remain separate. The evidence relationships become composable.**

## Composition contract

Each domain contributes an independently verified finding and a raw source identity. The cross-domain analysis records a per-domain evidence map containing the finding identifier and content hash, source identifier and content hash, and source lineage. The final claim therefore preserves three interrogable evidence streams rather than replacing them with one opaque aggregate artifact.

The cross-domain relationship is deliberately declared as **provenance composition only**. It does not assert a biological, proteomic, seismic, or causal relationship. The proof asks whether independently identifiable evidence can participate in one scientific argument while retaining separate custody and verification paths.

## Acceptance criteria

| Test | Required result |
|---|---|
| Source verification | Neuroscience, proteomics, and Earth/Space bundles independently verify before composition. |
| Fresh-process verification | The serialized cross-domain bundle verifies from disk without the original catalog or execution state. |
| Shared semantics | The normal bundle verifier and Observatory reconstruct the combined chain; no cross-domain verifier is introduced. |
| Provenance preservation | The final specification exposes each domain’s source ID, content hash, and lineage. |
| Selective invalidation | Revoking one domain source affects that domain’s finding and the cross-domain finding, but not the other domain findings. |
| Domain neutrality | `impact_of()` works on raw artifacts from all domains without understanding domain-specific scientific objects. |

The V1.5 proof exercises selective revocation for neuroscience, proteomics, and Earth/Space independently. Each revocation produces a precise blast radius rather than invalidating unrelated evidence.

## Reproduce

```bash
cd /home/ubuntu/cerevia
PYTHONPATH=. python3 examples/cross_domain/cross_domain_proof.py
```

The generated cross-domain bundle is a local proof artifact and is ignored by Git. Its source domain bundles remain independently verifiable inputs.
