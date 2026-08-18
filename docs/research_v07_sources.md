# V0.7 Eye-Tracking Sources

The OpenNeuro EEGEyeNet dataset page identifies `ds005872` version `1.0.0` as a BIDS-standardized dataset of simultaneously collected EEG and eye-tracking data from one subject. It reports BIDS validation as valid with 23 warnings, CC0 licensing, one participant, one session, and DOI `doi:10.18112/openneuro.ds005872.v1.0.0`.

Source: [OpenNeuro ds005872 version 1.0.0](https://openneuro.org/datasets/ds005872/versions/1.0.0)

The BIDS physiological recordings specification states that continuous physiological recordings, including eye tracking, use matching `_physio.tsv.gz` and `_physio.json` pairs. It describes `SamplingFrequency`, `StartTime`, and `Columns` metadata and supports `PhysioType` values including eye tracking.

Source: [BIDS physiological recordings](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/physiological-recordings.html)

The 2026 Eye-Tracking-BIDS preprint describes a community extension for gaze position, pupil data, and asynchronous eye-tracker events. It emphasizes explicit organization and metadata for eye tracking and multimodal use alongside EEG and other neural recordings. This implementation uses the stable generic BIDS physiological recording contract for the first adapter boundary and does not claim full BEP020 coverage.

Source: [Eye-Tracking-BIDS preprint, PMC12889726](https://pmc.ncbi.nlm.nih.gov/articles/PMC12889726/)
