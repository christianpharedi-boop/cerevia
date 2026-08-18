# CEREVIA V0.1 Architecture

CEREVIA is intentionally a scientific engine rather than a web application. The first vertical slice proves that a neuroscience observation can become a traceable derived finding without overwriting state.

```text
RAW EVIDENCE -> OBSERVATION -> QUALITY CONTROL -> TRANSFORMATION -> FEATURE -> ANALYSIS -> FINDING
      \________________________________________________________________________________________/
                                      machine-readable provenance
```

The Earth-specific foundation is preserved under `third_party/coresignal_earth/`. It contains CoreSignal’s strict IERS C04 parser, LOD model, provenance schema, and license. CEREVIA reuses the same principles: source data are never silently edited, provenance is explicit, hashes represent byte identity, and admission precedes analysis.

The V0.1 catalog is in-memory and append-only. A future persistence layer may serialize the catalog, but it must preserve the same invariants and content hashes.

## Vertical slice

The example creates synthetic EEG, ingests it under `demo-001 / sub-001 / ses-01`, runs a finite-sample QC gate, applies a deterministic FFT band-pass filter, creates one-second epochs, extracts 8–12 Hz spectral power, computes a descriptive one-sample statistic, records a provisional finding, and emits `evidence_manifest.json`.
