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

## V1.1 Sentinel

CEREVIA Sentinel is the defensive layer above the core. It runs adversarial attack suites, supports Ed25519 verification attestations, maintains an append-only hash-linked transparency log, and propagates source revocation through dependent analyses, claims, and findings. It makes silent change difficult and detected compromise visible; it does not claim scientific truth. See [`docs/sentinel.md`](docs/sentinel.md).

## V1.2 Observatory

CEREVIA Observatory is a contracts-first, **read-only query layer** over manifests, evidence graphs, independent verification, Sentinel attestations, revocations, and transparency-log history. It answers “why does this finding exist?”, “what evidence supports it?”, “what did CEREVIA know at a given time?”, and “what is affected if this artifact is revoked?” without becoming a second authority capable of rewriting evidence. See [`docs/observatory.md`](docs/observatory.md).

The reference implementation is intentionally a CLI rather than a dashboard:

```bash
PYTHONPATH=. python3 examples/bids_eeg/observatory_query.py \
  examples/bids_eeg/verification_bundle.json \
  --sentinel examples/bids_eeg/sentinel_result.json
```

## V1.3 Proteomics Domain Transplant

V1.3 tests whether the exact Evidence Core, Sentinel, and Observatory trust semantics survive a domain change. The proteomics adapter understands a public protein-expression assay, processing, quantification, and descriptive comparison; it does not create a second identity system, verifier, claim framework, mutable database, or evidence graph. See [`docs/proteomics-v1.3.md`](docs/proteomics-v1.3.md).

The transplant proof uses the same 13 adversarial Sentinel attacks and the same Observatory `impact_of()` query used for neuroscience:

```bash
PYTHONPATH=. python3 examples/proteomics/proteomics_proof.py \
  examples/proteomics/data/hela_proteins_subset.csv
```

## V1.4 Earth/Space Domain Transplant

V1.4 tests the same trust architecture against spatial-temporal observations and derived products. The Earth/Space adapter understands USGS GeoJSON earthquake observations, coordinate/time normalization, and a descriptive event-cluster product; it does not create a second provenance or verification system. See [`docs/earthspace-v1.4.md`](docs/earthspace-v1.4.md).

The proof uses the same 13 adversarial Sentinel attacks and the same Observatory `impact_of()` query as neuroscience and proteomics:

```bash
PYTHONPATH=. python3 examples/earthspace/earthspace_proof.py \
  examples/earthspace/data/usgs_earthquakes_2024-01-01_m5.json
```

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/bids_eeg/evidence_aware_analysis.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
PYTHONPATH=. python3 examples/bids_eeg/verify_bundle.py \
  examples/bids_eeg/verification_bundle.json
PYTHONPATH=. python3 examples/bids_eeg/observatory_query.py \
  examples/bids_eeg/verification_bundle.json \
  --sentinel examples/bids_eeg/sentinel_result.json
PYTHONPATH=. python3 examples/proteomics/proteomics_proof.py \
  examples/proteomics/data/hela_proteins_subset.csv
PYTHONPATH=. python3 examples/earthspace/earthspace_proof.py \
  examples/earthspace/data/usgs_earthquakes_2024-01-01_m5.json
```

The real V1.0 proof uses OpenNeuro ds003810 EEG and its 68 EDF behavioral events. It exports the qualified claim chain and verifies it in a fresh Python process. Tests then corrupt an upstream payload, claim statement, and manifest to confirm that independent verification fails explicitly.

The repository also contains the V0.7 three-observation implementation for EEG, behavioral events, and eye tracking, plus V0.8 evidence-aware analysis and V0.9 claim validation. No participant data is copied into this repository.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.
