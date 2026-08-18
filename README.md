# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.6.1 Alignment Integrity

CEREVIA now hardens the EEG-plus-behavioral boundary. Alignment requires exact agreement on pseudonymous participant, session, and task context, and the raw EEG artifact is an exact alignment parent. Negative or out-of-range event onsets, invalid tolerances, missing recording duration, missing participant context, and changed parent identities are rejected or produce different alignment identities.

The alignment semantics are explicit: this release performs validated recording-timebase mapping, not independent event-detector matching. Each behavioral EDF annotation is deterministically mapped to `round(onset_seconds × sampling_rate_hz)` after bounds validation.

The multimodal chain remains:

```text
EEG raw → QC → filter → epochs → alpha power ─┐
                                               ├→ multimodal analysis → finding
EDF annotations → behavioral events → alignment ─┘
```

The evidence graph identifies the final finding as dependent on behavioral evidence. See [`docs/multimodal.md`](docs/multimodal.md).

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/bids_eeg/multimodal_analysis.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
```

The real OpenNeuro proof validates and maps 68 EDF annotations, verifies the manifest, and exports the multimodal evidence graph. No participant data is copied into this repository.

This release deliberately remains limited to EEG plus behavioral events; it does not add eye tracking, MRI, MEG, a GUI, a database, or an AI layer.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.
