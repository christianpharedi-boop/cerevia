# CEREVIA V0.7 Multimodal Observation

CEREVIA V0.7 adds eye tracking as a second independent observation stream beside EEG and behavioral events. The design separates three scientific roles:

| Role | CEREVIA representation |
|---|---|
| Observation | Independent immutable `raw_eeg`, `behavioral_events`, and `eye_tracking` artifacts. |
| Alignment | Explicit `cross_modal_alignment` artifacts whose parents are the observations being related. |
| Inference | `multimodal_inference` artifacts whose parents include independent observations and explicit alignments. |
| Finding | A provisional scientific claim bound to the inference artifact and exact evidence parents. |

## Eye-tracking interoperability

The adapter consumes BIDS physiological recording pairs using a `_physio.tsv` or `_physio.tsv.gz` file and matching JSON sidecar. It requires `PhysioType: eyetrack`, a positive `SamplingFrequency`, a `Columns` declaration containing `time` and at least one signal column, monotonic timestamps, finite signal values, and a sampling-frequency-consistent duration. The first proof uses the real CC0 OpenNeuro EEGEyeNet dataset `ds005872` version `1.0.0`, which contains simultaneously collected EEG and eye-tracking data [1]. The implementation follows the generic BIDS physiological recordings contract for `_physio` files and explicitly does not claim full coverage of the newer Eye-Tracking-BIDS extension [2] [3].

## Context safety

EEG-eye alignment requires exact participant, session, and task agreement and records both source content hashes. It rejects a relationship merely because two files are neuroscience data. The real proof ingests 161,733 eye-tracking samples from EEGEyeNet and rejects an attempted relationship with the unrelated OpenNeuro ds003810 EEG context because the participant and task differ.

## Three-stream inference

The `three_stream_inference` operation requires one EEG feature, one behavioral observation, one eye-tracking observation, and explicit EEG-behavior and EEG-eye alignments. It preserves all five as exact artifact parents. The evidence graph therefore retains independent audit paths rather than collapsing EEG, behavior, and eye tracking into one opaque blob. Provisional computation remains distinct from a scientific claim.

## References

[1]: https://openneuro.org/datasets/ds005872/versions/1.0.0 "OpenNeuro EEGEyeNet Dataset ds005872 v1.0.0"

[2]: https://bids-specification.readthedocs.io/en/stable/modality-specific-files/physiological-recordings.html "BIDS physiological recordings specification"

[3]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12889726/ "Eye-Tracking-BIDS preprint"
