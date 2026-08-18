# CEREVIA V0.3 BIDS-EEG Interoperability

CEREVIA V0.3 treats BIDS as an external organization and metadata standard. CEREVIA does not reimplement BIDS; it validates the BIDS EEG contract, binds the recording to the CEREVIA ontology, and adds evidence provenance around the external source.

The adapter follows the BIDS EEG layout and required sidecar fields. BIDS EEG recordings use a matching `_eeg.json` sidecar and `_channels.tsv`; the sidecar supplies fields such as `EEGReference`, `SamplingFrequency`, `EEGChannelCount`, and `RecordingType`.[^1] BIDS events are represented by `events.tsv` rows with required `onset` and `duration` columns when event files are present.[^2]

## Supported V0.3 path

```text
BIDS dataset
  → validate dataset_description.json, _eeg.json, _channels.tsv, and events.tsv
  → read EDF/BDF signal
  → bind sub/session/task/run to Study, Participant, Session, Recording, Channel, and Event
  → create immutable raw EEG artifact
  → record source SHA-256 and BIDS metadata in artifact metadata
  → verify CEREVIA manifest
```

The first real proof uses OpenNeuro dataset **ds003810**, version **2.0.2**, “Motor Imagery vs Rest - Low-Cost EEG System.” The public dataset page identifies it as BIDS-valid, EEG-only, CC0-licensed, and provides the dataset DOI.[^3] CEREVIA validated and read the real `sub-02_task-MIvsRest_run-0_eeg.edf` signal, with 15 channels at 125 Hz. The downloaded source file was not added to this repository; only the ingestion adapter, tests, and generated result summary are committed.

## Reproducibility and boundary

The raw artifact records the BIDS dataset identifier, relative source path, BIDS version, source SHA-256, participant/session/task context, modality, channel names, and acquisition sampling rate. The original BIDS files remain the external source of record. CEREVIA stores no copied participant data in the repository.

The interoperability example is:

```bash
PYTHONPATH=. python3 examples/neuro/ingest_openneuro.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
```

[^1]: [BIDS EEG specification](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html), including the EEG filename layout, supported formats, sidecar requirements, and channel definitions.
[^2]: [BIDS events specification](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files/events.html), including required event timing columns.
[^3]: [OpenNeuro ds003810 version 2.0.2](https://openneuro.org/datasets/ds003810/versions/2.0.2), dataset metadata, BIDS validation status, license, DOI, and file listing.
