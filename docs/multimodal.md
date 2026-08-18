# CEREVIA V0.6 Multimodal Evidence

CEREVIA V0.6 adds a deliberately small multimodal layer for **EEG plus behavioral events**. The goal is not merely to store two datasets; it is to prove that both evidence sources share a participant, session, task, timebase, and provenance context before they contribute to one analysis.

## Contract

| Requirement | Enforcement |
|---|---|
| Shared participant | Behavioral artifact and EEG recording carry the same pseudonymous participant context. |
| Shared session | Alignment rejects mismatched session identifiers. |
| Shared task | Behavioral events are required to share one task context. |
| Timebase | EDF annotations are represented in recording seconds; alignment records the timebase and tolerance. |
| Provenance | Behavioral source identity, alignment parameters, event IDs, and all parent artifact hashes are preserved. |
| Scientific status | Multimodal analyses and findings remain `PROVISIONAL`; computation does not auto-convert to truth. |

The implementation extracts EDF annotation markers from the real OpenNeuro ds003810 EEG run. For the validated `sub-02_task-MIvsRest_run-0_eeg.edf`, the annotation stream yielded 68 behavioral events, including motor-imagery and rest markers. The EEG raw artifact, behavioral event artifact, alignment artifact, spectral feature, multimodal analysis, and finding form one graph-connected evidence structure.

## Provenance chain

```text
EEG raw ── QC ── filter ── epochs ── alpha power ──┐
                                                     ├── multimodal analysis ── finding
EDF annotations ── behavioral events ── alignment ──┘
```

The evidence graph exposes the behavioral artifact as a dependency of the final finding. Invalidating it therefore identifies the downstream multimodal analysis and finding as affected.

This release intentionally does not add eye tracking, MRI, MEG, a GUI, a database, or an AI layer. The cross-modal context model is kept narrow until its alignment and provenance invariants are well established.
