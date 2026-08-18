# CEREVIA External Pilot: 30-Minute Quickstart

This document is designed for a researcher who has never seen CEREVIA before. It describes the task without revealing implementation reasoning or requiring privileged access.

## What CEREVIA is

CEREVIA is a protocol for producing, exchanging, independently verifying, and tracing scientific evidence and claims across computational and institutional boundaries. It verifies computational integrity and declared provenance; it does not decide whether a scientific hypothesis is true.

## What you receive

| Item | Location |
|---|---|
| Frozen interoperability specification | [`docs/evidence-interoperability-v1.md`](../evidence-interoperability-v1.md) |
| External implementation | [`examples/external_impl/standalone_protocol.py`](../../examples/external_impl/standalone_protocol.py) |
| Institutional exchange profile | [`docs/institutional-exchange-v2.1.md`](../institutional-exchange-v2.1.md) |
| Pilot proof and adversarial scenarios | [`examples/pilot/pilot_proof.py`](../../examples/pilot/pilot_proof.py) |
| Acceptance criteria and answer schema | [`docs/external-institutional-pilot-v2.2.md`](../external-institutional-pilot-v2.2.md) |
| Readiness state | [`readiness.json`](readiness.json) |

## First 30 minutes

| Time | Activity | Expected output |
|---|---|---|
| 0–5 minutes | Read the V1.6 specification and identify the five universal contracts. | Written list of evidence, lineage, verification, invalidation, and claim checks. |
| 5–10 minutes | Inspect the V2.0 standalone implementation without importing the CEREVIA package. | Independent understanding of serialized identity, manifest, graph, and verifier rules. |
| 10–15 minutes | Run the provided pilot fixture and inspect the valid answer. | A valid package answer and an agreement record. |
| 15–20 minutes | Run the altered-hash, stale-revocation, and wrong-recipient scenarios. | Explicit failures and their failure classes. |
| 20–25 minutes | Independently answer authenticity, bundle validity, lineage, claim, uncertainty, history, revocation, impact, and unaffected-finding questions. | A machine-readable answer record. |
| 25–30 minutes | Compare your answers with the reference answer and record every disagreement. | Agreement report or a reproducible failure report. |

## Rules of the pilot

The external participant should not receive private development reasoning or implementation assistance. Do not change the V1.6 specification to make an inconvenient result pass. Treat a failure as useful evidence about the protocol or its documentation. Keep sensitive scientific data under the institution’s own governance; exchange only the protocol artifacts and approved out-of-band references.

The pilot is not considered complete until an external team independently executes it and returns its answer record. The repository’s own pilot proof is only a readiness demonstration.

## Minimal command path

```bash
cd /home/ubuntu/cerevia
PYTHONPATH=. python3 examples/pilot/pilot_proof.py
PYTHONPATH=. python3 -m unittest tests.test_pilot_kit -v
```
