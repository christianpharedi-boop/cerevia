# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.1.1 invariant-hardening release

This release makes artifact payloads and metadata recursively immutable, preserves failed QC artifacts before the pipeline halts, records a computational environment fingerprint, gives evidence manifests their own SHA-256 identity, and tests deliberate chain-of-custody attacks.

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
