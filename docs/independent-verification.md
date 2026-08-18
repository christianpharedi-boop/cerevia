# CEREVIA V1.0 Independent Verification

CEREVIA V1.0 tests whether an independent researcher can verify an evidence-to-claim chain without access to the original in-memory execution state.

## Verification bundle

A verification bundle contains the evidence manifest, complete serialized artifact catalog including payloads, the executable analysis specification, its specification hash, and the manifest’s evidence graph. The bundle is sufficient to reconstruct the declared chain:

```text
source → artifacts → graph → analysis → inference → claim → finding
```

The verifier independently checks the following conditions:

| Check | Meaning |
|---|---|
| Manifest hash | The manifest itself has not been altered. |
| Specification hash | The declared analysis specification is unchanged. |
| Artifact content identities | Each artifact hash recomputes from serialized payload, metadata, operation, parameters, environment, and parent content hashes. |
| Parent closure | No serialized artifact references a missing ancestor. |
| Claim chain | The final finding references a claim, which references a multimodal inference. |
| Evidence hashes | Claim evidence IDs resolve to the exact content hashes declared by the claim. |
| Uncertainty | The claim preserves a declared uncertainty type. |
| Graph hash | The serialized dependency graph has not been altered. |

The standalone verifier returns `VERIFIED` when all checks pass. A changed raw payload, claim statement, manifest field, graph, specification, or ancestor identity produces `INVESTIGATE` with a diagnostic failure list. The verifier does not rerun the original analysis; it verifies the serialized scientific argument and computational identities. Exact rerun remains available through the V0.4 AnalysisSpecification machinery.

## Real proof

The V1.0 proof exports the OpenNeuro ds003810 EEG and EDF behavioral-event chain, then starts a fresh Python process that reads only `verification_bundle.json`. The fresh process verifies the final finding, claim, inference, analysis, evidence graph, and all artifact identities. Separate tests corrupt an upstream payload, claim statement, and manifest and confirm that verification fails.
