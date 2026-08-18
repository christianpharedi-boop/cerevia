# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to independently verifiable scientific claims. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V1.0 Independent Verification

CEREVIA V1.0 answers a focused question: **Can an independent researcher verify the evidence-to-claim chain without access to the original in-memory execution state?**

The project exports a self-contained verification bundle containing the evidence manifest, full serialized artifact catalog, analysis specification, specification hash, and evidence graph.

```text
source → artifacts → graph → analysis → inference → claim → finding
```

A fresh verification process independently checks manifest integrity, specification identity, every artifact content hash, ancestor closure, evidence hashes, claim/inference/finding roles, uncertainty declaration, and graph hash. A valid chain returns `VERIFIED`; corruption returns `INVESTIGATE` with diagnostic failures. See [`docs/independent-verification.md`](docs/independent-verification.md).

> **Verification of computation is not verification of truth.** CEREVIA verifies that a serialized evidence-to-claim chain is internally intact and that a qualified claim follows from declared computations under declared assumptions. It does not decide that the scientific hypothesis is true.

V1.0 freezes the Evidence Core primitives—immutable artifacts, content identities, provenance, ontology context, interoperability, reproducible execution, evidence graphs, multimodal alignment, inference, claims, uncertainty, and independent verification. Future domain adapters and extensions should preserve this boundary. See [`docs/evidence-core-v1.md`](docs/evidence-core-v1.md).

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/bids_eeg/evidence_aware_analysis.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
PYTHONPATH=. python3 examples/bids_eeg/verify_bundle.py \
  examples/bids_eeg/verification_bundle.json
```

The real V1.0 proof uses OpenNeuro ds003810 EEG and its 68 EDF behavioral events. It exports the qualified claim chain and verifies it in a fresh Python process. Tests then corrupt an upstream payload, claim statement, and manifest to confirm that independent verification fails explicitly.

The repository also contains the V0.7 three-observation implementation for EEG, behavioral events, and eye tracking, plus V0.8 evidence-aware analysis and V0.9 claim validation. No participant data is copied into this repository.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.
