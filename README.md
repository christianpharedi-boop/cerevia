# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.3 Real-World Interoperability

CEREVIA now speaks the external BIDS EEG organization and metadata standard without attempting to become a BIDS implementation. The new adapter validates `dataset_description.json`, EEG sidecars, channels TSV files, and event files; reads real EDF/BDF signals; binds BIDS participant, session, task, run, modality, channels, and events to the CEREVIA ontology; and emits an immutable evidence artifact with source SHA-256 and BIDS metadata.

The first real proof uses OpenNeuro dataset ds003810, version 2.0.2. A real `sub-02_task-MIvsRest_run-0_eeg.edf` was read at 15 channels and 125 Hz. The source dataset remains external and is not committed to this repository.

The V0.2 ontology and V0.1.2 integrity core remain underneath the adapter. CEREVIA continues to enforce immutable artifacts, parent content hashes, environment fingerprints, catalog integrity validation, exact ontology context, and independently hashed manifests.

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/bids_eeg/ingest_openneuro.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
```

The BIDS interoperability contract is documented in [`docs/bids-eeg.md`](docs/bids-eeg.md). No copied participant data is required in the CEREVIA repository.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.
