# CEREVIA V2.0 External Conformance

V2.0 tests whether the V1.6 Evidence Interoperability Specification is a protocol rather than only a CEREVIA implementation detail.

The standalone implementation at [`examples/substrate_stress_tests/standalone_protocol.py`](../examples/substrate_stress_tests/standalone_protocol.py) intentionally does **not** import the `cerevia` package. It implements the protocol-visible rules using only the Python standard library: canonical JSON hashing, artifact content identity, parent references, manifest construction, evidence-graph hashing, serialized bundle verification, and downstream impact traversal.

## Acceptance criteria

| Criterion | Result required |
|---|---|
| Independent implementation | The standalone producer/verifier has no CEREVIA imports. |
| Independent production | The standalone implementation emits a valid protocol bundle. |
| CEREVIA verification | CEREVIA’s verifier accepts the standalone bundle. |
| Independent verification | The standalone verifier accepts CEREVIA-generated neuroscience and cross-domain bundles. |
| Selective invalidation | Standalone impact traversal agrees with Observatory on a revoked proteomics source and preserves unrelated findings. |
| Cross-domain exchange | The standalone verifier accepts the serialized CEREVIA cross-domain bundle. |
| Frozen specification | V1.6 profile and contract semantics are not changed to accommodate V2.0. |

The external producer’s claim is deliberately a descriptive protocol fixture. It does not assert a scientific relationship; it tests whether an independent implementation can preserve the evidence-to-claim structure.

## Reproduce

```bash
cd /home/ubuntu/cerevia
python3 examples/substrate_stress_tests/standalone_protocol.py produce examples/substrate_stress_tests/external_bundle.json
python3 examples/substrate_stress_tests/standalone_protocol.py verify examples/substrate_stress_tests/external_bundle.json
PYTHONPATH=. python3 examples/neuro/verify_bundle.py examples/substrate_stress_tests/external_bundle.json
PYTHONPATH=. python3 -m unittest tests.test_external_conformance -v
```

V2.0 does not silently extend V1.6. Missing protocol semantics are future specification work rather than changes made during the external-conformance experiment.
