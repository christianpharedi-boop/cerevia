# CEREVIA V0.6.1 Multimodal Alignment Integrity

CEREVIA V0.6.1 hardens the EEG-plus-behavioral boundary. The system now requires the EEG Recording and behavioral artifact to agree on **participant, session, and task** before alignment can be created. The exact raw EEG artifact is also a required alignment parent, so changing the EEG source changes the alignment identity.

## Temporal semantics

This release describes alignment precisely as **validated recording-timebase mapping**, not as a claim that behavioral markers have been independently matched to a separate EEG event detector. Each event is checked for a finite, non-negative onset, checked against the measured recording duration, and mapped deterministically to `round(onset_seconds × sampling_rate_hz)`.

The alignment artifact records the event IDs, event-to-sample map, recording duration, sampling rate, timebase, tolerance, behavioral artifact ID, EEG artifact ID, and EEG content hash. Invalid negative onsets, events outside the recording, invalid tolerances, missing duration, missing participant context, and participant/session/task mismatches are rejected.

## V0.6.1 contract

| Requirement | Enforcement |
|---|---|
| Shared participant | Recording and behavioral metadata must have the same pseudonymous participant ID. |
| Shared session | Recording and behavioral metadata must have the same session ID. |
| Shared task | Recording task and behavioral task must match exactly. |
| Exact EEG source | The raw EEG artifact is a required alignment parent. |
| Temporal bounds | Onsets must be non-negative and lie within the measured recording duration plus tolerance. |
| Deterministic mapping | Each event maps to an explicit sample index using the recording sampling rate. |
| Provenance | Behavioral and EEG parent hashes are included in the alignment artifact identity. |

The real OpenNeuro ds003810 proof extracts 68 EDF annotations, validates and maps all 68 events, verifies the multimodal manifest, and exposes the final finding as dependent on the behavioral evidence in the evidence graph.
