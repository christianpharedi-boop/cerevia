# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.1.2 adversarial-integrity release

This release deliberately tests the chain of custody rather than adding new neuroscience features. CEREVIA now detects or rejects raw-data mutation, transformation-parameter tampering, deleted ancestors, swapped parents, manifest tampering, altered environment metadata, unsupported findings, malformed EEG metadata, and stale findings reused against a new dataset.

Artifact identities include the artifact content, operation, parameters, software version, environment fingerprint, and exact parent content hashes. Catalog validation recomputes those identities and reports integrity failures. Findings may only bind evidence from the exact referenced analysis lineage.

## V0.1 proof

The first vertical slice is deliberately small: synthetic EEG → ingest → hash → QC → deterministic filter → epoch → alpha-band power → analysis → finding → machine-readable evidence manifest.

## Run

```bash
cd /home/ubuntu/cerevia
python3 examples/eeg_pipeline/run.py
python3 -m unittest discover -s tests -v
```

The example writes `examples/eeg_pipeline/evidence_manifest.json`. No database, authentication, cloud service, web interface, or AI model is required.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.
