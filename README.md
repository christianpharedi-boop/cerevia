# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.6 Multimodal Evidence

CEREVIA now supports a deliberately narrow multimodal proof: **EEG plus behavioral events**. The system validates that both evidence sources share a pseudonymous participant, session, task, and declared timebase before combining them. EDF annotations from the real OpenNeuro ds003810 run are ingested as behavioral-event evidence, aligned to the EEG recording context, and linked by provenance to a multimodal analysis and provisional finding.

The multimodal chain is:

```text
EEG raw → QC → filter → epochs → alpha power ─┐
                                               ├→ multimodal analysis → finding
EDF annotations → behavioral events → alignment ─┘
```

The evidence graph can answer which findings depend on the behavioral artifact, while the artifact catalog remains authoritative for content hashes, parent identities, and integrity validation. See [`docs/multimodal.md`](docs/multimodal.md).

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/bids_eeg/multimodal_analysis.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
```

The real-data V0.6 proof extracted 68 EDF behavioral events, aligned all 68 under the declared recording timebase, verified the evidence manifest, and projected the multimodal result into the evidence graph. No participant data is copied into this repository.

This release intentionally does not add eye tracking, MRI, MEG, a GUI, a database, or an AI layer.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.
